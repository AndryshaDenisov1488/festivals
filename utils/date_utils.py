"""Дата «сегодня» в московском времени — для корректной фильтрации «будущих» турниров."""
from datetime import date, datetime, timezone
from typing import Iterable, List, TypeVar

import pytz

MSK = pytz.timezone("Europe/Moscow")

RUSSIAN_MONTHS = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)

T = TypeVar("T")


def get_today() -> date:
    """Сегодняшняя дата по Москве (не зависит от часового пояса сервера)."""
    return datetime.now(MSK).date()


def month_sort_key(month: str) -> int:
    try:
        return RUSSIAN_MONTHS.index(month)
    except ValueError:
        return len(RUSSIAN_MONTHS)


def sort_month_names(months: Iterable[str]) -> List[str]:
    """Сортирует названия месяцев по календарю (январь → декабрь)."""
    return sorted(months, key=month_sort_key)


def sort_by_tournament_date(items: Iterable[T]) -> List[T]:
    """Сортирует объекты с атрибутом tournament по дате турнира (раньше → позже)."""
    return sorted(items, key=lambda x: x.tournament.date)
