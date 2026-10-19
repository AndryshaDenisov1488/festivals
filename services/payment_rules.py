"""Unified payment amount rules for the bot and the website."""
from __future__ import annotations

from config import SPECIAL_JUDGE_IDS
from utils.text_utils import is_affirmative_answer

MIN_PAYMENT_AMOUNT = 3500
STANDARD_PAYMENT_AMOUNT = 5000


def is_special_judge(user_id: int) -> bool:
    return int(user_id) in SPECIAL_JUDGE_IDS


def check_payment_amount(user_id: int, amount: float, confirm_non_standard: bool = False) -> str:
    if amount <= 0:
        return "positive"
    if is_special_judge(user_id):
        return "ok"
    if amount < MIN_PAYMENT_AMOUNT:
        return "min"
    if amount != STANDARD_PAYMENT_AMOUNT and not confirm_non_standard:
        return "non_standard"
    return "ok"


def rejection_text(code: str, amount: float) -> str:
    shown = "%g" % amount
    if code == "positive":
        return "Сумма должна быть больше нуля. Введите сумму ещё раз:"
    if code == "min":
        return (
            "Минимальная сумма оплаты — %s рублей.\n"
            "Вы ввели %s. Введите другую сумму:"
        ) % (MIN_PAYMENT_AMOUNT, shown)
    if code == "non_standard":
        return (
            "Стандартная сумма для турнира — %s руб.\n"
            "Вы ввели %s руб.\n\n"
            "Подтвердите эту сумму ответом «да» или отправьте другую сумму."
        ) % (STANDARD_PAYMENT_AMOUNT, shown)
    return "Некорректная сумма."


def amount_error_detail(code: str) -> str:
    if code == "positive":
        return "Сумма должна быть больше нуля"
    if code == "min":
        return "Минимальная сумма %s ₽" % MIN_PAYMENT_AMOUNT
    if code == "non_standard":
        return "non_standard"
    return "Некорректная сумма"


def parse_amount_message(text, pending_amount):
    if text is None or not str(text).strip():
        return None, False, "Отправьте сумму текстом."
    raw = str(text).strip()
    if pending_amount is not None and is_affirmative_answer(raw):
        return float(pending_amount), True, None
    try:
        amount = float(raw.replace(",", ".").replace(" ", ""))
    except ValueError:
        if pending_amount is not None:
            return None, False, "Напишите «да» для подтверждения или введите новую сумму (например: 5000)."
        return None, False, "Введите число, например 5000 или 5000.50."
    return amount, False, None
