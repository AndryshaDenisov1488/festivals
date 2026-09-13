#!/usr/bin/env python3
"""Восстановление registration_cancellations из bot.log (до появления учёта в коде)."""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import SessionLocal
from models import RegistrationCancellation, RegistrationStatus, Tournament

LOG_PATH = Path(__file__).resolve().parents[1] / "bot.log"
SEASON_START = datetime(2025, 7, 1)
CANCEL_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - .* - "
    r".+ \(ID: (?P<user_id>\d+)\) отменил запись на турнир ID: (?P<tournament_id>\d+)$"
)
PAYMENT_DELETED_RE = re.compile(r"на турнир (?P<tournament_id>\d+)$")


def parse_cancellations():
    if not LOG_PATH.exists():
        print(f"Log not found: {LOG_PATH}")
        return []

    events = []
    prev_line = ""
    for line in LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        m = CANCEL_RE.match(line.strip())
        if not m:
            prev_line = line
            continue
        ts = datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S")
        if ts < SEASON_START:
            prev_line = line
            continue
        user_id = int(m.group("user_id"))
        tournament_id = int(m.group("tournament_id"))
        had_payment = False
        if "Удалена запись об оплате" in prev_line and f"на турнир {tournament_id}" in prev_line:
            pm = PAYMENT_DELETED_RE.search(prev_line)
            if pm and int(pm.group("tournament_id")) == tournament_id:
                had_payment = True
        events.append({
            "cancelled_at": ts,
            "user_id": user_id,
            "tournament_id": tournament_id,
            "previous_status": RegistrationStatus.APPROVED if had_payment else RegistrationStatus.PENDING,
        })
        prev_line = line
    return events


def main():
    events = parse_cancellations()
    if not events:
        print("No cancellation events found in log for current season.")
        return

    session = SessionLocal()
    try:
        existing = {
            (user_id, tournament_id, cancelled_at.strftime("%Y-%m-%d %H:%M"))
            for user_id, tournament_id, cancelled_at in session.query(
                RegistrationCancellation.user_id,
                RegistrationCancellation.tournament_id,
                RegistrationCancellation.cancelled_at,
            ).all()
        }

        inserted = 0
        skipped = 0
        reg_id_base = 1_000_000
        for i, ev in enumerate(events):
            key = (ev["user_id"], ev["tournament_id"], ev["cancelled_at"].strftime("%Y-%m-%d %H:%M"))
            if key in existing:
                skipped += 1
                continue
            t = session.query(Tournament).filter(Tournament.tournament_id == ev["tournament_id"]).first()
            if not t:
                skipped += 1
                continue
            session.add(
                RegistrationCancellation(
                    registration_id=reg_id_base + i,
                    user_id=ev["user_id"],
                    tournament_id=ev["tournament_id"],
                    previous_status=ev["previous_status"],
                    cancelled_at=ev["cancelled_at"],
                )
            )
            existing.add(key)
            inserted += 1

        session.commit()
        total = session.query(RegistrationCancellation).count()
        approved = session.query(RegistrationCancellation).filter(
            RegistrationCancellation.previous_status == RegistrationStatus.APPROVED
        ).count()
        print(f"Parsed: {len(events)}, inserted: {inserted}, skipped: {skipped}")
        print(f"DB total: {total}, approved refusals: {approved}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
