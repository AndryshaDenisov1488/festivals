"""Утилиты для API: формат дат dd.mm.yyyy, зона Москвы"""
from datetime import date, datetime
from typing import Callable, List, Optional, TypeVar

import pytz

T = TypeVar("T")


def filter_by_search(items: List[T], term: str, *field_getters: Callable[[T], str]) -> List[T]:
    """Фильтрует список: term (без учёта регистра) входит в любое из полей. Работает с кириллицей."""
    t = term.strip().lower()
    if not t:
        return items
    return [x for x in items if any(t in str(g(x) or "").lower() for g in field_getters)]

MSK = pytz.timezone("Europe/Moscow")


def format_date(d: Optional[date]) -> Optional[str]:
    """Формат даты dd.mm.yyyy"""
    if d is None:
        return None
    return d.strftime("%d.%m.%Y")


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Формат datetime в московском времени: dd.mm.yyyy HH:mm"""
    if dt is None:
        return None
    if type(dt) is date:
        return format_date(dt)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    dt_msk = dt.astimezone(MSK)
    return dt_msk.strftime("%d.%m.%Y %H:%M")
