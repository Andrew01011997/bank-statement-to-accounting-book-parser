# -*- coding: utf-8 -*-
"""
Розбір, валідація та фільтрація сум для парсера банківських виписок.
Негативні суми (витрати) відсіюються тут — парсери пропускають None.
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
    - "(1200)" (бухгалтерський формат)

    Args:
        amount_str: Рядок з сумою для перевірки

    Returns:
        True якщо знайдено знак мінуса, False інакше
    """
    cleaned = amount_str.strip()

    # Перевіряємо префіксні знаки мінуса
    if any(cleaned.startswith(sign) for sign in constants.MINUS_SIGNS):
        return True

    # Дужки (бухгалтерський формат)
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


def extract_and_validate_amount(amount_str: str, decimal_comma: bool = False) -> Optional[float]:
    """
    Комбінована функція: витягує та валідує суму.

    Алгоритм:
    1. Перевіряє на негативність (за знаком у рядку)
    2. Очищує whitespace (і замінює кому на крапку, якщо decimal_comma)
    3. Витягує число
    4. Валідує межі

    Args:
        amount_str: Рядок з сумою
        decimal_comma: True якщо кома - десятковий розділювач ("2 267,80")

    Returns:
        float якщо валідна позитивна сума, інакше None
    """
    if not amount_str or is_negative_amount(amount_str):
        return None

    cleaned = re.sub(constants.WHITESPACE_PATTERN, '', amount_str)
    if decimal_comma:
        cleaned = cleaned.replace(',', '.')

    match = re.search(constants.AMOUNT_PATTERN, cleaned)
    if not match:
        return None

    try:
        amount = float(match.group(1))
        return amount if is_valid_amount(amount) else None
    except ValueError:
        return None


def to_float(number_str: str, decimal_comma: bool = False) -> float:
    """
    Перетворює суму з тексту виписки (контрольна сума, деталі операції) на float.
    Прибирає пробіли-роздільники тисяч (звичайні та нерозривні). Знак не перевіряється.

    Args:
        number_str: Рядок з числом ("2 728 455.00" або "231 283,90")
        decimal_comma: True якщо кома - десятковий розділювач

    Returns:
        float

    Raises:
        ValueError: Якщо рядок не є числом
    """
    cleaned = number_str.replace(' ', '').replace('\xa0', '')
    if decimal_comma:
        cleaned = cleaned.replace(',', '.')
    return float(cleaned)
