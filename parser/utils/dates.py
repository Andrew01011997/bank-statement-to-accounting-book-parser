# -*- coding: utf-8 -*-
"""
Розбір дат та часу з комірок банківських виписок
"""

from datetime import datetime
from typing import Optional, Sequence, Tuple
import re
from . import constants


# (regex, формат strptime). Групи regex з'єднуються пробілом перед strptime.
DATETIME_FULL = (constants.DATETIME_PATTERN, '%d.%m.%Y %H:%M:%S')
DATETIME_SHORT = (constants.DATETIME_PATTERN_SHORT, '%d.%m.%Y %H:%M')
DATE_ONLY = (constants.DATE_PATTERN, '%d.%m.%Y')

# Порядок має значення: перший формат, що підійшов, перемагає
DEFAULT_FORMATS = (DATETIME_FULL, DATE_ONLY)


def extract_datetime(value, formats: Sequence[Tuple[str, str]] = DEFAULT_FORMATS) -> Optional[datetime]:
    """
    Витягує дату (та час, якщо є) з рядка, пробуючи формати по черзі.

    Args:
        value: Рядок або комірка таблиці з датою
        formats: Послідовність (regex, формат strptime)

    Returns:
        datetime об'єкт або None якщо дату не знайдено
    """
    if not value:
        return None

    text = str(value).strip()

    for pattern, fmt in formats:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(' '.join(match.groups()), fmt)
            except ValueError:
                pass

    return None
