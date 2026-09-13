from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from database import SessionLocal
from models import User
from api.dependencies import get_current_admin
from services.export_service import build_export_workbook_bytes


router = APIRouter()


def _stream_export(
    *,
    period: str,
    month: Optional[str] = None,
    year: Optional[int] = None,
    season_key: Optional[str] = None,
):
    db = SessionLocal()
    try:
        buffer, filename = build_export_workbook_bytes(
            db,
            period=period,
            month=month,
            year=year,
            season_key=season_key,
        )
        if buffer is None:
            raise HTTPException(status_code=404, detail="Нет данных для выбранного периода")
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    finally:
        db.close()


@router.get("/month")
def export_month(
    month: str,
    admin: User = Depends(get_current_admin),
):
    return _stream_export(period="month", month=month)


@router.get("/year")
def export_year(
    year: int,
    admin: User = Depends(get_current_admin),
):
    return _stream_export(period="year", year=year)


@router.get("/season")
def export_season(
    season_key: str = Query(..., description="Ключ сезона вида 2026-2027 или all"),
    admin: User = Depends(get_current_admin),
):
    return _stream_export(period="season", season_key=season_key)


@router.get("/all")
def export_all(admin: User = Depends(get_current_admin)):
    return _stream_export(period="all")
