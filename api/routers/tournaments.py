from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Tournament
from api.dependencies import get_db, get_current_user
from api.utils import format_date
from models import User


router = APIRouter()


@router.get("")
def list_tournaments(
    month: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Tournament)
    if month:
        q = q.filter(Tournament.month == month)
    if from_date:
        q = q.filter(Tournament.date >= from_date)
    if to_date:
        q = q.filter(Tournament.date <= to_date)
    q = q.order_by(Tournament.date)
    tournaments = q.all()
    return [
        {
            "tournament_id": t.tournament_id,
            "month": t.month,
            "date": format_date(t.date),
            "name": t.name,
        }
        for t in tournaments
    ]


@router.get("/{tournament_id}")
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tournament not found")
    return {
        "tournament_id": t.tournament_id,
        "month": t.month,
        "date": format_date(t.date),
        "name": t.name,
    }
