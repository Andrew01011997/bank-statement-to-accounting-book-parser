# -*- coding: utf-8 -*-
"""
Amount parsing, validation and filtering.
Negative amounts (expenses) are filtered out here; parsers skip None.
"""

from typing import Optional
import re
from . import constants


def is_negative_amount(amount_str: str) -> bool:
    """
    Detects a minus sign BEFORE the number is parsed.

    Recognises:
    - "-1200.50" (hyphen-minus)
    - "−500" (minus sign, U+2212)
    - "–300" (en dash, U+2013)
    - "(1200)" (accounting format)

    Args:
        amount_str: Amount string to check

    Returns:
        True if a minus sign was found, False otherwise
    """
    cleaned = amount_str.strip()

    if any(cleaned.startswith(sign) for sign in constants.MINUS_SIGNS):
        return True

    # Parentheses (accounting format)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        return True

    return False


def is_valid_amount(amount: float) -> bool:
    """
    Checks that an amount is within bounds.

    Args:
        amount: Numeric amount

    Returns:
        True if MIN_AMOUNT <= amount <= MAX_AMOUNT
    """
    return constants.MIN_AMOUNT <= amount <= constants.MAX_AMOUNT


def extract_and_validate_amount(amount_str: str, decimal_comma: bool = False) -> Optional[float]:
    """
    Extracts and validates an amount.

    Steps:
    1. Reject negatives (by the sign in the string)
    2. Strip whitespace (and turn the comma into a dot if decimal_comma)
    3. Extract the number
    4. Check bounds

    Args:
        amount_str: Amount string
        decimal_comma: True if a comma is the decimal separator ("1 234,56")

    Returns:
        float for a valid positive amount, otherwise None
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
    Converts an amount from statement text (control sum, transaction details) to float.
    Removes space thousands separators (regular and non-breaking). The sign is not checked.

    Args:
        number_str: Number string ("12 345.67" or "12 345,67")
        decimal_comma: True if a comma is the decimal separator

    Returns:
        float

    Raises:
        ValueError: If the string is not a number
    """
    cleaned = number_str.replace(' ', '').replace('\xa0', '')
    if decimal_comma:
        cleaned = cleaned.replace(',', '.')
    return float(cleaned)
