"""Дата «сегодня» в московском времени — для корректной фильтрации «будущих» турниров."""
from datetime import date, datetime, timezone
from typing import Iterable, List, TypeVar

import pytz

MSK = pytz.timezone("Europe/Moscow")

RUSSIAN_MONTHS = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)

# Сезон фигурного катания: август → июнь (июль обычно без турниров)
SEASON_MONTHS = (
    "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
)

MONTH_NAME_TO_NUM = {name: idx + 1 for idx, name in enumerate(RUSSIAN_MONTHS)}

T = TypeVar("T")


def get_today() -> date:
    """Сегодняшняя дата по Москве (не зависит от часового пояса сервера)."""
    return datetime.now(MSK).date()


def month_sort_key(month: str) -> int:
    """Ключ сортировки: август → … → июнь; июль и неизвестные — в конец."""
    try:
        return SEASON_MONTHS.index(month)
    except ValueError:
        if month == "Июль":
            return len(SEASON_MONTHS)
        return len(SEASON_MONTHS) + 1


def sort_month_names(months: Iterable[str]) -> List[str]:
    """Сортирует месяцы в порядке сезона: август → июнь."""
    return sorted(months, key=month_sort_key)


def month_name_to_year_month(month_name: str, ref: date | None = None) -> tuple[int, int]:
    """Подбирает (год, номер месяца) для календаря дат в текущем сезоне."""
    today = ref or get_today()
    month_num = MONTH_NAME_TO_NUM.get(month_name)
    if not month_num:
        return today.year, today.month

    year = today.year
    if month_num >= 8:
        if today.month < 8:
            year -= 1
    elif month_num <= 6:
        if today.month >= 8:
            year += 1
    return year, month_num


def sort_by_tournament_date(items: Iterable[T]) -> List[T]:
    """Сортирует объекты с атрибутом tournament по дате турнира (раньше → позже)."""
    return sorted(items, key=lambda x: x.tournament.date)
