from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from api.dependencies import get_current_admin
from api.utils import format_date, format_datetime
from services.budget_service import BudgetService


router = APIRouter()


@router.get("")
async def list_budgets(
    month: Optional[str] = Query(None),
    future_only: bool = Query(False, description="Только будущие турниры"),
    admin: User = Depends(get_current_admin),
):
    from datetime import date

    bs = BudgetService(bot=None)
    data = await bs.get_all_budgets()
    if month:
        data = [item for item in data if item.get("tournament_month") == month]
    if future_only:
        from utils.date_utils import get_today
        today = get_today()
        data = [item for item in data if item.get("tournament_date") and item["tournament_date"] >= today]
    return [
        {
            **item,
            "tournament_date": format_date(item.get("tournament_date")),
            "budget_set_date": format_datetime(item.get("budget_set_date")),
        }
        for item in data
    ]


@router.get("/summary")
async def budget_summary(
    admin: User = Depends(get_current_admin),
):
    bs = BudgetService(bot=None)
    data = await bs.get_admin_profit_summary()
    return data


@router.get("/{tournament_id}")
async def get_budget(
    tournament_id: int,
    admin: User = Depends(get_current_admin),
):
    bs = BudgetService(bot=None)
    data = await bs.get_tournament_budget(tournament_id)
    if not data:
        raise HTTPException(status_code=404, detail="Budget not found")
    return data


class BudgetSetIn(BaseModel):
    total_budget: float


@router.post("/{tournament_id}")
async def set_budget(
    tournament_id: int,
    payload: BudgetSetIn,
    admin: User = Depends(get_current_admin),
):
    if payload.total_budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be positive")
    bs = BudgetService(bot=None)
    ok = await bs.set_tournament_budget(tournament_id, payload.total_budget)
    if not ok:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return {"ok": True}
