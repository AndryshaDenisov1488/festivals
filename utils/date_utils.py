"""Дата «сегодня» в московском времени — для корректной фильтрации «будущих» турниров."""
from datetime import date, datetime, timezone

import pytz

MSK = pytz.timezone("Europe/Moscow")


def get_today() -> date:
    """Сегодняшняя дата по Москве (не зависит от часового пояса сервера)."""
    return datetime.now(MSK).date()
