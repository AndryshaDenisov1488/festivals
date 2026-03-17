from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, JudgePayment, Tournament
from api.dependencies import get_current_user
from services.payment_system import PaymentSystem


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/earnings/my/payments")
def earnings_payments_list(
    user: User = Depends(get_current_user),
):
    """Список всех выплат (оплаченных и ожидающих) с payment_id для confirm/correct"""
    db = SessionLocal()
    try:
        payments = db.query(JudgePayment, Tournament).join(
            Tournament, JudgePayment.tournament_id == Tournament.tournament_id
        ).filter(JudgePayment.user_id == user.user_id).order_by(Tournament.date.desc()).all()
        return [
            {
                "payment_id": p.payment_id,
                "tournament_id": p.tournament_id,
                "tournament_name": t.name,
                "tournament_date": t.date.isoformat(),
                "amount": p.amount,
                "is_paid": p.is_paid,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            }
            for p, t in payments
        ]
    finally:
        db.close()


@router.get("/earnings/my/detail")
def earnings_detail(
    user: User = Depends(get_current_user),
):
    ps = PaymentSystem(bot=None)
    data = ps.get_judge_earnings(user.user_id)
    return {
        "total_tournaments": data["total_tournaments"],
        "total_amount": data["total_amount"],
        "tournament_earnings": [
            {
                "name": t[0],
                "date": t[1].isoformat() if t[1] else None,
                "amount": t[2],
                "payment_date": t[3].isoformat() if t[3] else None,
            }
            for t in data["tournament_earnings"]
        ],
        "monthly_earnings": [
            {"month": m[0], "total_amount": m[1], "tournaments_count": m[2]}
            for m in data["monthly_earnings"]
        ],
    }


@router.get("/earnings/my/summary")
def earnings_summary(
    user: User = Depends(get_current_user),
):
    ps = PaymentSystem(bot=None)
    data = ps.get_judge_earnings(user.user_id)
    total = data["total_tournaments"]
    amount = data["total_amount"]
    rating = "⭐ Начинающий судья"
    if total >= 50:
        rating = "🥇 Золотой судья"
    elif total >= 25:
        rating = "🥈 Серебряный судья"
    elif total >= 10:
        rating = "🥉 Бронзовый судья"
    return {
        "total_tournaments": total,
        "total_amount": amount,
        "average_amount": amount / total if total else 0,
        "rating": rating,
    }


class ConfirmPaymentIn(BaseModel):
    payment_id: int
    amount: float


@router.post("/earnings/my/confirm")
async def confirm_payment(
    payload: ConfirmPaymentIn,
    user: User = Depends(get_current_user),
):
    from database import SessionLocal
    db = SessionLocal()
    try:
        payment = db.query(JudgePayment).filter(
            JudgePayment.payment_id == payload.payment_id,
            JudgePayment.user_id == user.user_id,
            JudgePayment.is_paid == False,
        ).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        if payload.amount < 3500:
            raise HTTPException(status_code=400, detail="Min amount 3500")
        ps = PaymentSystem(bot=None)
        ok = await ps.handle_payment_confirmation(payload.payment_id, True, payload.amount)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to confirm")
        return {"ok": True}
    finally:
        db.close()


class CorrectEarningsIn(BaseModel):
    payment_id: int
    amount: float


@router.post("/earnings/my/correct")
def correct_earnings(
    payload: CorrectEarningsIn,
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        payment = db.query(JudgePayment).filter(
            JudgePayment.payment_id == payload.payment_id,
            JudgePayment.user_id == user.user_id,
            JudgePayment.is_paid == True,
        ).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        if payload.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        payment.amount = payload.amount
        db.commit()
        return {"ok": True}
    finally:
        db.close()
