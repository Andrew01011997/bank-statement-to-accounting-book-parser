# -*- coding: utf-8 -*-
"""
Валідація та фільтрація сум для парсера банківських виписок
ВИРІШУЄ ПРОБЛЕМУ #1: Фільтрація негативних значень
"""

from typing import Optional
import re
from . import constants


def is_negative_amount(amount_str: str) -> bool:
    """
    Перевіряє наявність знака мінуса ПЕРЕД парсингом числа.

    Розпізнає:
    - "-1200.50" (hyphen-minus)
    - "−500" (minus sign, U+2212)
    - "–300" (en dash, U+2013)
    - "(1200)" (бухгалтерський формат - бонус)

    Args:
        amount_str: Рядок з сумою для перевірки

    Returns:
        True якщо знайдено знак мінуса, False інакше
    """
    cleaned = amount_str.strip()

    # Перевіряємо префіксні знаки мінуса
    if any(cleaned.startswith(sign) for sign in constants.MINUS_SIGNS):
        return True

    # Бонус: дужки (бухгалтерський формат)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        return True

    return False


def is_valid_amount(amount: float) -> bool:
    """
    Перевіряє, чи сума в допустимих межах.

    Args:
        amount: Числове значення суми

    Returns:
        True якщо сума в межах MIN_AMOUNT та MAX_AMOUNT
    """
    return constants.MIN_AMOUNT <= amount <= constants.MAX_AMOUNT


def extract_and_validate_amount(amount_str: str) -> Optional[float]:
    """
    Комбінована функція: витягує та валідує суму.

    Алгоритм:
    1. Перевіряє на негативність (за знаком у рядку)
    2. Очищує whitespace
    3. Витягує число
    4. Валідує межі

    Args:
        amount_str: Рядок з сумою

    Returns:
        float якщо валідна позитивна сума, інакше None
    """
    if not amount_str or is_negative_amount(amount_str):
        return None

    cleaned = re.sub(constants.WHITESPACE_PATTERN, '', amount_str)
    match = re.search(constants.AMOUNT_PATTERN, cleaned)

    if not match:
        return None

    try:
        amount = float(match.group(1))
        return amount if is_valid_amount(amount) else None
    except ValueError:
        return None
