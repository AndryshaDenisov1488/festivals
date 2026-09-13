from datetime import date

from utils.date_utils import month_name_to_year_month, sort_month_names
from utils.season import (
    get_current_season_key,
    get_season_date_range,
    list_seasons,
    normalize_season_param,
    season_bounds_from_start_year,
)


def test_season_bounds_are_july_through_june():
    assert season_bounds_from_start_year(2026) == (
        date(2026, 7, 1),
        date(2027, 6, 30),
    )


def test_current_season_changes_on_july_first():
    assert get_current_season_key(date(2026, 6, 30)) == "2025-2026"
    assert get_current_season_key(date(2026, 7, 1)) == "2026-2027"


def test_arbitrary_valid_season_key_is_preserved():
    assert normalize_season_param("2026-2027") == "2026-2027"
    assert get_season_date_range("2026-2027") == (
        date(2026, 7, 1),
        date(2027, 6, 30),
    )


def test_current_season_is_always_available(monkeypatch):
    monkeypatch.setattr("utils.season.get_today", lambda: date(2026, 9, 13))
    seasons = list_seasons()
    assert seasons[0]["key"] == "2026-2027"
    assert seasons[0]["is_current"] is True
    assert seasons[-1]["key"] == "all"


def test_months_follow_july_to_june_season_order():
    assert sort_month_names(["Январь", "Июнь", "Июль", "Август"]) == [
        "Июль",
        "Август",
        "Январь",
        "Июнь",
    ]
    assert month_name_to_year_month("Июль", date(2027, 2, 1)) == (2026, 7)
    assert month_name_to_year_month("Июнь", date(2026, 9, 1)) == (2027, 6)
