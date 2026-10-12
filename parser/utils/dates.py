# -*- coding: utf-8 -*-
"""
Date and time parsing for statement cells.
"""

from datetime import datetime
from typing import Optional, Sequence, Tuple
import re
from . import constants


# (regex, strptime format). Regex groups are joined with a space before strptime.
DATETIME_FULL = (constants.DATETIME_PATTERN, '%d.%m.%Y %H:%M:%S')
DATETIME_SHORT = (constants.DATETIME_PATTERN_SHORT, '%d.%m.%Y %H:%M')
DATE_ONLY = (constants.DATE_PATTERN, '%d.%m.%Y')

# Order matters: the first matching format wins
DEFAULT_FORMATS = (DATETIME_FULL, DATE_ONLY)


def extract_datetime(value, formats: Sequence[Tuple[str, str]] = DEFAULT_FORMATS) -> Optional[datetime]:
    """
    Extracts a date (and time, if present) from a string, trying formats in order.

    Args:
        value: String or table cell containing a date
        formats: Sequence of (regex, strptime format)

    Returns:
        datetime or None if no date was found
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
