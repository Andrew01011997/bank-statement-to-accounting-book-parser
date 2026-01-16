# -*- coding: utf-8 -*-
"""
Форматування дат та сум для парсера банківських виписок
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.statement import Transaction


# Заголовки CSV колонок
CSV_HEADERS = ['Час', 'Дата', 'Сума', 'Комісія', 'Сума з врахуванням комісії']


def format_date(date: datetime, fmt: str = '%d.%m.%Y') -> str:
    """
    Форматує дату.

    Args:
        date: Об'єкт datetime
        fmt: Формат дати (за замовчуванням '%d.%m.%Y')

    Returns:
        Відформатована дата як рядок
    """
    return date.strftime(fmt)


def format_amount(amount: float) -> str:
    """
    Форматує суму в європейському форматі (кома як розділювач).

    Args:
        amount: Сума для форматування

    Returns:
        Відформатована сума (наприклад: 123.45 -> "123,45")

    Examples:
        >>> format_amount(123.45)
        '123,45'
        >>> format_amount(1234.56)
        '1234,56'
    """
    float_string = f"{amount:.2f}"
    # Замінюємо крапку на кому
    return float_string.replace('.', ',')


def format_time(date: datetime) -> str:
    """
    Форматує час.

    Args:
        date: Об'єкт datetime

    Returns:
        Відформатований час як рядок (HH:MM:SS)
    """
    return date.strftime('%H:%M:%S')


def format_csv_row(transaction: 'Transaction') -> list:
    """
    Генерує рядок CSV з транзакції.

    Структура (5 колонок):
    1. Час
    2. Дата
    3. Сума (gross_amount - до комісії)
    4. Комісія
    5. Сума з врахуванням комісії (net_amount - після комісії)

    Args:
        transaction: Транзакція

    Returns:
        Список з 5 елементами для CSV рядка
    """
    time_str = format_time(transaction.date)
    date_str = format_date(transaction.date)
    gross_str = format_amount(transaction.gross_amount)
    commission_str = format_amount(transaction.commission)
    net_str = format_amount(transaction.net_amount)

    return [
        time_str,        # Час
        date_str,        # Дата
        gross_str,       # Сума
        commission_str,  # Комісія
        net_str          # Сума з врахуванням комісії
    ]
