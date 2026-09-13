"""Сезоны фигурного катания: с 1 июля по 30 июня."""
from datetime import date
import re
from typing import Optional

from utils.date_utils import get_today

SEASON_KEY_RE = re.compile(r"^(\d{4})-(\d{4})$")


def season_bounds_from_start_year(start_year: int) -> tuple[date, date]:
    return date(start_year, 7, 1), date(start_year + 1, 6, 30)


def get_current_season_key(ref: Optional[date] = None) -> str:
    d = ref or get_today()
    start_year = d.year if d.month >= 7 else d.year - 1
    return f"{start_year}-{start_year + 1}"


def normalize_season_param(season: Optional[str]) -> Optional[str]:
    """None / 'all' — без фильтра; иначе ключ сезона или текущий сезон."""
    if not season or season == "all":
        return None
    match = SEASON_KEY_RE.fullmatch(season)
    if match and int(match.group(2)) == int(match.group(1)) + 1:
        return season
    return get_current_season_key()


def get_season_date_range(season_key: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    if season_key is None:
        return None, None
    try:
        start_year = int(season_key.split("-")[0])
    except (ValueError, IndexError):
        current_key = get_current_season_key()
        start_year = int(current_key.split("-")[0])
    return season_bounds_from_start_year(start_year)


def list_seasons() -> list[dict]:
    current = get_current_season_key()
    current_start_year = int(current.split("-")[0])
    result = []
    for start_year in range(current_start_year, 2023, -1):
        key = f"{start_year}-{start_year + 1}"
        start, end = season_bounds_from_start_year(start_year)
        result.append({
            "key": key,
            "label": f"{start_year}–{start_year + 1}",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "is_current": key == current,
        })
    result.append({
        "key": "all",
        "label": "Все сезоны",
        "start": None,
        "end": None,
        "is_current": False,
    })
    return result


def season_label(season_key: Optional[str]) -> str:
    if season_key is None:
        return "Все сезоны"
    return season_key.replace("-", "–")
