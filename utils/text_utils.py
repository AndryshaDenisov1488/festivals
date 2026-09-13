"""Утилиты для обработки пользовательского текста."""

_AFFIRMATIVE_ANSWERS = frozenset({'да', 'yes', 'y', 'д'})


def is_affirmative_answer(text: str) -> bool:
    """Проверяет ответ «да» без учёта регистра (да, Да, ДА и т.д.)."""
    return text.strip().casefold() in _AFFIRMATIVE_ANSWERS
