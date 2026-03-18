from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus, JudgePayment
from config import ADMIN_IDS, MAX_JUDGES_PER_TOURNAMENT, BOT_TOKEN
from api.dependencies import get_current_admin
from api.utils import format_date


router = APIRouter()


class BroadcastIn(BaseModel):
    message: str


@router.post("/broadcast")
async def broadcast(
    payload: BroadcastIn,
    admin: User = Depends(get_current_admin),
):
    from config import BOT_TOKEN
    if not BOT_TOKEN or not payload.message:
        raise HTTPException(status_code=400, detail="Invalid request")
    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        ok, fail = 0, 0
        for u in users:
            try:
                await bot.send_message(u.user_id, payload.message, parse_mode="HTML")
                ok += 1
            except Exception:
                fail += 1
        return {"total": len(users), "ok": ok, "fail": fail}
    finally:
        db.close()
        await bot.session.close()


@router.get("/registrations")
def admin_list_registrations(
    month: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        q = db.query(Registration).join(Tournament)
        if month:
            q = q.filter(Tournament.month == month)
        if status:
            q = q.filter(Registration.status == status)
        q = q.order_by(Tournament.date.desc(), Registration.registration_id)
        regs = q.all()
        return [
            {
                "registration_id": r.registration_id,
                "tournament_id": r.tournament_id,
                "tournament_name": r.tournament.name,
                "tournament_date": format_date(r.tournament.date),
                "tournament_month": r.tournament.month,
                "user_id": r.user_id,
                "user_name": f"{r.user.first_name} {r.user.last_name}",
                "status": r.status,
            }
            for r in regs
        ]
    finally:
        db.close()


async def _notify_judge_approve(user_id: int, tournament_name: str, tournament_date: str) -> None:
    """Telegram + email при одобрении заявки."""
    if BOT_TOKEN:
        try:
            from aiogram import Bot
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                user_id,
                f"✅ Вы утверждены для судейства турнира <b>{tournament_date} {tournament_name}</b>!",
                parse_mode="HTML"
            )
            await bot.session.close()
        except Exception:
            pass


async def _notify_judge_reject(user_id: int, tournament_name: str, tournament_date: str) -> None:
    """Telegram + email при отклонении заявки."""
    if BOT_TOKEN:
        try:
            from aiogram import Bot
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                user_id,
                f"❌ Ваша заявка на судейство турнира <b>{tournament_date} {tournament_name}</b> отклонена.",
                parse_mode="HTML"
            )
            await bot.session.close()
        except Exception:
            pass


@router.post("/registrations/{registration_id}/approve")
async def admin_approve_registration(
    registration_id: int,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        reg = db.query(Registration).options(
            joinedload(Registration.user),
            joinedload(Registration.tournament),
        ).filter(Registration.registration_id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
        if reg.status != RegistrationStatus.PENDING:
            raise HTTPException(status_code=400, detail="Registration already processed")
        approved_count = db.query(Registration).filter(
            Registration.tournament_id == reg.tournament_id,
            Registration.status == RegistrationStatus.APPROVED,
        ).count()
        if approved_count >= MAX_JUDGES_PER_TOURNAMENT:
            raise HTTPException(status_code=400, detail="Max judges reached")
        reg.status = RegistrationStatus.APPROVED
        db.commit()

        t = reg.tournament
        u = reg.user
        tournament_date = format_date(t.date)
        tournament_name = t.name

        existing = db.query(JudgePayment).filter(
            JudgePayment.user_id == u.user_id,
            JudgePayment.tournament_id == t.tournament_id,
        ).first()
        if not existing:
            db.add(JudgePayment(
                user_id=u.user_id,
                tournament_id=t.tournament_id,
                is_paid=False,
                reminder_sent=False,
            ))
            db.commit()

        await _notify_judge_approve(u.user_id, tournament_name, tournament_date)
        if u.email and getattr(u, "email_verified", False):
            from api.email_service import send_registration_approved_email
            send_registration_approved_email(u.email, tournament_name, tournament_date)

        return {"ok": True, "status": "approved"}
    finally:
        db.close()


@router.post("/registrations/{registration_id}/reject")
async def admin_reject_registration(
    registration_id: int,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        reg = db.query(Registration).options(
            joinedload(Registration.user),
            joinedload(Registration.tournament),
        ).filter(Registration.registration_id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
        if reg.status != RegistrationStatus.PENDING:
            raise HTTPException(status_code=400, detail="Registration already processed")
        reg.status = RegistrationStatus.REJECTED
        db.commit()

        t = reg.tournament
        u = reg.user
        tournament_date = format_date(t.date)
        tournament_name = t.name

        await _notify_judge_reject(u.user_id, tournament_name, tournament_date)
        if u.email and getattr(u, "email_verified", False):
            from api.email_service import send_registration_rejected_email
            send_registration_rejected_email(u.email, tournament_name, tournament_date)

        return {"ok": True, "status": "rejected"}
    finally:
        db.close()
