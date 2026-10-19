"""Web export uses the same workbook as the Telegram bot."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from services.excel_export import build_export_workbook


def build_export_workbook_bytes(
    session: Session,
    *,
    period: str = "all",
    month: Optional[str] = None,
    year: Optional[int] = None,
    season_key: Optional[str] = None,
):
    bio, filename, _stats = build_export_workbook(
        session,
        period,
        month=month,
        year=year,
        season_key=season_key,
    )
    if bio is None:
        return None, ""
    return bio, filename
