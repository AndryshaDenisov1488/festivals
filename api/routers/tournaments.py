from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Tournament, Registration, RegistrationStatus, User
from api.dependencies import get_db, get_current_user
from api.utils import format_date, filter_by_search
from utils.date_utils import get_today


router = APIRouter()


@router.get("")
def list_tournaments(
    month: Optional[str] = Query(None),
    future_only: bool = Query(True, description="Только будущие турниры"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None, description="Поиск по названию турнира или месяцу"),
    my_approved_only: bool = Query(
        False,
        description="Только турниры, на которые текущий пользователь утверждён (для «кто на фест»)",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Tournament)
    if my_approved_only:
        q = q.filter(
            Tournament.tournament_id.in_(
                db.query(Registration.tournament_id).filter(
                    Registration.user_id == user.user_id,
                    Registration.status == RegistrationStatus.APPROVED,
                )
            )
        )
    if month:
        q = q.filter(Tournament.month == month)
    if future_only:
        q = q.filter(Tournament.date >= get_today())
    if from_date:
        q = q.filter(Tournament.date >= from_date)
    if to_date:
        q = q.filter(Tournament.date <= to_date)
    q = q.order_by(Tournament.date)
    tournaments = q.all()
    if search and search.strip():
        tournaments = filter_by_search(tournaments, search, lambda t: t.name, lambda t: t.month)
    return [
        {
            "tournament_id": t.tournament_id,
            "month": t.month,
            "date": format_date(t.date),
            "name": t.name,
        }
        for t in tournaments
    ]


@router.get("/{tournament_id}/approved-judges")
def list_approved_judges_for_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Список утверждённых судей на турнир (для судей: кто ещё едет на фест)."""
    t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    my_approved = (
        db.query(Registration)
        .filter(
            Registration.tournament_id == tournament_id,
            Registration.user_id == user.user_id,
            Registration.status == RegistrationStatus.APPROVED,
        )
        .first()
    )
    if not my_approved:
        raise HTTPException(
            status_code=403,
            detail="Доступно только для турниров, на которые вы утверждены",
        )
    rows = (
        db.query(User)
        .join(Registration, Registration.user_id == User.user_id)
        .filter(
            Registration.tournament_id == tournament_id,
            Registration.status == RegistrationStatus.APPROVED,
        )
        .order_by(User.last_name, User.first_name)
        .all()
    )
    return [
        {
            "user_id": u.user_id,
            "name": f"{u.first_name} {u.last_name}".strip(),
            "function": u.function,
            "category": u.category,
        }
        for u in rows
    ]


@router.get("/{tournament_id}")
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return {
        "tournament_id": t.tournament_id,
        "month": t.month,
        "date": format_date(t.date),
        "name": t.name,
    }
