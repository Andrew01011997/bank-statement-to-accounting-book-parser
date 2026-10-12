# -*- coding: utf-8 -*-
"""
Date and amount formatting for the ledger CSV.
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.statement import Transaction


# CSV column headers. Kept in Ukrainian: they are the income ledger's column names
# (time, date, amount, commission, amount net of commission).
CSV_HEADERS = ['Час', 'Дата', 'Сума', 'Комісія', 'Сума з врахуванням комісії']


def format_date(date: datetime, fmt: str = '%d.%m.%Y') -> str:
    """
    Formats a date.

    Args:
        date: datetime object
        fmt: Date format (default '%d.%m.%Y')

    Returns:
        Formatted date string
    """
    return date.strftime(fmt)


def format_amount(amount: float) -> str:
    """
    Formats an amount with a comma as the decimal separator.

    Args:
        amount: Amount to format

    Returns:
        Formatted amount (e.g. 123.45 -> "123,45")

    Examples:
        >>> format_amount(123.45)
        '123,45'
        >>> format_amount(1234.56)
        '1234,56'
    """
    return f"{amount:.2f}".replace('.', ',')


def format_time(date: datetime) -> str:
    """
    Formats a time.

    Args:
        date: datetime object

    Returns:
        Formatted time string (HH:MM:SS)
    """
    return date.strftime('%H:%M:%S')


def format_csv_row(transaction: 'Transaction') -> list:
    """
    Builds a CSV row from a transaction.

    Layout (5 columns):
    1. Час - time
    2. Дата - date
    3. Сума - gross_amount (before commission)
    4. Комісія - commission
    5. Сума з врахуванням комісії - net_amount (after commission)

    Args:
        transaction: Transaction

    Returns:
        List of 5 values for the CSV row
    """
    return [
        format_time(transaction.date),
        format_date(transaction.date),
        format_amount(transaction.gross_amount),
        format_amount(transaction.commission),
        format_amount(transaction.net_amount),
    ]
