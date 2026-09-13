"""Учёт отмен записей судей для статистики отказов."""
from datetime import date, datetime
from typing import Any

import pytz
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models import Registration, RegistrationCancellation, RegistrationStatus, Tournament

MSK = pytz.timezone("Europe/Moscow")


def record_registration_cancellation(session: Session, registration: Registration) -> None:
    """Сохраняет отмену записи перед удалением registration."""
    session.add(
        RegistrationCancellation(
            registration_id=registration.registration_id,
            user_id=registration.user_id,
            tournament_id=registration.tournament_id,
            previous_status=registration.status,
            cancelled_at=datetime.now(MSK).replace(tzinfo=None),
        )
    )


def season_cancellation_filter(season_start: date, season_end_exclusive: date):
    return and_(
        RegistrationCancellation.cancelled_at >= datetime.combine(season_start, datetime.min.time()),
        RegistrationCancellation.cancelled_at < datetime.combine(season_end_exclusive, datetime.min.time()),
    )


def approved_cancellation_filter():
    return RegistrationCancellation.previous_status == RegistrationStatus.APPROVED


def count_season_approved_assignments(
    session: Session,
    season_start: date,
    season_end: date,
    season_filter,
) -> int:
    """Все одобрения за сезон: текущие + отменённые после одобрения."""
    current_approved = (
        session.query(func.count(Registration.registration_id))
        .join(Tournament, Tournament.tournament_id == Registration.tournament_id)
        .filter(
            Registration.status == RegistrationStatus.APPROVED,
            Tournament.date >= season_start,
            Tournament.date <= season_end,
        )
        .scalar()
        or 0
    )
    cancelled_after_approval = (
        session.query(func.count(RegistrationCancellation.cancellation_id))
        .filter(season_filter, approved_cancellation_filter())
        .scalar()
        or 0
    )
    return current_approved + cancelled_after_approval


def aggregate_approved_refusals_by_user(
    rows: list[tuple],
    *,
    with_names: bool = False,
) -> dict[int, dict[str, Any]]:
    by_user: dict[int, dict[str, Any]] = {}
    for row in rows:
        if with_names:
            user_id, first_name, last_name, cnt = row
        else:
            user_id, cnt = row
            first_name, last_name = None, None
        if user_id not in by_user:
            entry: dict[str, Any] = {"user_id": user_id, "refusals": 0}
            if with_names:
                entry["user_name"] = f"{first_name} {last_name}".strip()
            by_user[user_id] = entry
        by_user[user_id]["refusals"] += cnt
    return by_user


def count_users_season_approved_assignments(
    session: Session,
    user_ids: list[int],
    season_start: date,
    season_end: date,
    season_filter,
) -> dict[int, int]:
    """Одобрения за сезон по каждому судье: текущие + отменённые после одобрения."""
    if not user_ids:
        return {}

    counts = {user_id: 0 for user_id in user_ids}

    current_rows = (
        session.query(Registration.user_id, func.count(Registration.registration_id))
        .join(Tournament, Tournament.tournament_id == Registration.tournament_id)
        .filter(
            Registration.user_id.in_(user_ids),
            Registration.status == RegistrationStatus.APPROVED,
            Tournament.date >= season_start,
            Tournament.date <= season_end,
        )
        .group_by(Registration.user_id)
        .all()
    )
    for user_id, cnt in current_rows:
        counts[user_id] = counts.get(user_id, 0) + cnt

    cancelled_rows = (
        session.query(RegistrationCancellation.user_id, func.count(RegistrationCancellation.cancellation_id))
        .filter(
            RegistrationCancellation.user_id.in_(user_ids),
            season_filter,
            approved_cancellation_filter(),
        )
        .group_by(RegistrationCancellation.user_id)
        .all()
    )
    for user_id, cnt in cancelled_rows:
        counts[user_id] = counts.get(user_id, 0) + cnt

    return counts


def enrich_judge_refusal_stats(
    by_user: dict[int, dict[str, Any]],
    approved_assignments_by_user: dict[int, int],
) -> list[dict[str, Any]]:
    result = []
    for stats in by_user.values():
        refusals = stats["refusals"]
        if refusals <= 0:
            continue
        user_id = stats["user_id"]
        approved_assignments = approved_assignments_by_user.get(user_id, refusals)
        result.append({
            **stats,
            "approved_assignments": approved_assignments,
            "refusal_pct": round((refusals / approved_assignments) * 100, 1) if approved_assignments > 0 else 0.0,
        })
    result.sort(key=lambda x: (-x["refusals"], -x["refusal_pct"], x.get("user_name", "")))
    return result


def approved_refusals_stats_list(by_user: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    result = [stats for stats in by_user.values() if stats["refusals"] > 0]
    result.sort(key=lambda x: (-x["refusals"], x.get("user_name", "")))
    return result


def get_responsibility_label(refusal_pct: float) -> str:
    if refusal_pct <= 5:
        return "Очень высокая"
    if refusal_pct <= 12:
        return "Высокая"
    if refusal_pct <= 20:
        return "Средняя"
    if refusal_pct <= 35:
        return "Низкая"
    return "Очень низкая"
