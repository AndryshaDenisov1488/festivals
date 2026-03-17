# utils/calendar.py
from datetime import date
from calendar import monthrange
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
log = logging.getLogger(__name__)

def prev_month(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)

def next_month(y: int, m: int):
    return (y + 1, 1) if m == 12 else (y, m + 1)

def _normalize_ym(arg):
    # Принимает None | (y,m) | date -> (y, m)
    if arg is None:
        today = date.today()
        return today.year, today.month
    if isinstance(arg, tuple) and len(arg) == 2:
        return int(arg[0]), int(arg[1])
    if isinstance(arg, date):
        return arg.year, arg.month
    raise ValueError("build_calendar(): expected None, (y,m) or date")

def build_calendar(current=None) -> InlineKeyboardMarkup:
    y, m = _normalize_ym(current)
    days_in_month = monthrange(y, m)[1]

    kb = InlineKeyboardMarkup(row_width=7)

    # Заголовок с навигацией
    kb.row(
        InlineKeyboardButton("«", callback_data=f"cal_prev_{y}_{m}"),
        InlineKeyboardButton(f"{m:02}.{y}", callback_data="cal_nop"),
        InlineKeyboardButton("»", callback_data=f"cal_next_{y}_{m}"),
    )

    # Дни недели
    kb.row(*[InlineKeyboardButton(x, callback_data="cal_nop") for x in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]])

    # Сдвиг на понедельник
    first_weekday = (date(y, m, 1).weekday() + 1) % 7  # 0=Пн ... 6=Вс
    lead = 6 if first_weekday == 0 else first_weekday - 1

    cells = [InlineKeyboardButton(" ", callback_data="cal_nop")] * lead

    # Кнопки дней — ЕДИНЫЙ формат выбора дня: cal_pick_YYYY_MM_DD
    for d in range(1, days_in_month + 1):
        cells.append(InlineKeyboardButton(f"{d:02}", callback_data=f"cal_pick_{y}_{m}_{d}"))

    while len(cells) % 7 != 0:
        cells.append(InlineKeyboardButton(" ", callback_data="cal_nop"))

    for i in range(0, len(cells), 7):
        kb.row(*cells[i:i+7])

    # Доп. навигация
    kb.row(
        InlineKeyboardButton("← Месяц", callback_data=f"cal_prev_{y}_{m}"),
        InlineKeyboardButton("Месяц →", callback_data=f"cal_next_{y}_{m}"),
    )

    # Кнопка отмены (по желанию)
    kb.row(InlineKeyboardButton("Отмена", callback_data="cal_cancel"))
    # отладка формата кнопок
    try:
        sample = [b.callback_data for b in kb.inline_keyboard[2] if b.callback_data][:3]
        log.info("[calendar.build_calendar] sample cb: %s", sample)
    except Exception:
        pass
    return kb
