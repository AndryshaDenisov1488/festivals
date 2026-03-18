import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Registration, Tournament, User
from models import RegistrationStatus
from config import MAX_JUDGES_PER_TOURNAMENT, CHANNEL_ID, ADMIN_EMAIL
from api.dependencies import get_current_user, get_db
from api.utils import format_date, filter_by_search


router = APIRouter()


class RegistrationCreateIn(BaseModel):
    tournament_id: int


@router.get("/my")
def my_registrations(
    month: Optional[str] = None,
    status: Optional[str] = None,
    future_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from datetime import date

    q = db.query(Registration).join(Tournament, Registration.tournament_id == Tournament.tournament_id).filter(
        Registration.user_id == user.user_id
    )
    if month:
        q = q.filter(Tournament.month == month)
    if future_only:
        from utils.date_utils import get_today
        q = q.filter(Tournament.date >= get_today())
    if status:
        q = q.filter(Registration.status == status)
    q = q.order_by(Tournament.date)
    regs = q.all()
    if search and search.strip():
        regs = [r for r in regs if filter_by_search([r.tournament], search, lambda t: t.name, lambda t: t.month)]
    return [
        {
            "registration_id": r.registration_id,
            "tournament_id": r.tournament_id,
            "status": r.status,
            "tournament": {
                "name": r.tournament.name,
                "date": format_date(r.tournament.date),
                "month": r.tournament.month,
            },
        }
        for r in regs
    ]


logger = logging.getLogger(__name__)


async def _notify_channel_new_registration(user_name: str, tournament_str: str) -> None:
    """Отправляет уведомление о новой заявке в Telegram-канал."""
    from config import BOT_TOKEN
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.warning("Telegram-канал: BOT_TOKEN или CHANNEL_ID не заданы, уведомление пропущено")
        return
    try:
        from aiogram import Bot
        async with Bot(token=BOT_TOKEN) as bot:
            await bot.send_message(
                CHANNEL_ID,
                "🔔 <b>Новая заявка</b>\n"
                f"👤 <b>{user_name}</b>\n"
                f"Турнир: <b>{tournament_str}</b>\n"
                "Статус: На рассмотрении",
                parse_mode="HTML"
            )
        logger.info("Уведомление в канал отправлено: %s, %s", user_name, tournament_str)
    except Exception as e:
        logger.exception("Ошибка отправки в Telegram-канал: %s", e)


def _notify_admin_email_new_registration(user_name: str, tournament_str: str) -> None:
    """Дублирует уведомление о новой заявке на email админа."""
    if not ADMIN_EMAIL:
        return
    try:
        from api.email_service import send_new_registration_to_admin_email
        send_new_registration_to_admin_email(ADMIN_EMAIL, user_name, tournament_str)
    except Exception as e:
        logger.exception("Ошибка отправки email админу: %s", e)


@router.post("", status_code=201)
async def create_registration(
    payload: RegistrationCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tournament = db.query(Tournament).filter(Tournament.tournament_id == payload.tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    existing = db.query(Registration).filter(
        Registration.user_id == user.user_id,
        Registration.tournament_id == payload.tournament_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered")

    approved_count = db.query(Registration).filter(
        Registration.tournament_id == payload.tournament_id,
        Registration.status == RegistrationStatus.APPROVED,
    ).count()
    if approved_count >= MAX_JUDGES_PER_TOURNAMENT:
        raise HTTPException(status_code=400, detail="Max judges reached")

    reg = Registration(
        user_id=user.user_id,
        tournament_id=payload.tournament_id,
        status=RegistrationStatus.PENDING,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    user_name = f"{user.first_name} {user.last_name}"
    tournament_str = f"{format_date(tournament.date)} {tournament.name}"
    await _notify_channel_new_registration(user_name, tournament_str)
    _notify_admin_email_new_registration(user_name, tournament_str)

    return {
        "registration_id": reg.registration_id,
        "tournament_id": reg.tournament_id,
        "status": reg.status,
    }


@router.delete("/{registration_id}", status_code=204)
def cancel_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from models import JudgePayment

    reg = db.query(Registration).filter(
        Registration.registration_id == registration_id,
        Registration.user_id == user.user_id,
    ).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")

    db.query(JudgePayment).filter(
        JudgePayment.user_id == user.user_id,
        JudgePayment.tournament_id == reg.tournament_id,
    ).delete(synchronize_session=False)
    db.delete(reg)
    db.commit()
    return None
