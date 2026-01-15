# -*- coding: utf-8 -*-
"""
Форматування дат та сум для парсера банківських виписок
"""

from datetime import datetime


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


def format_csv_row(date: datetime, amount: float) -> list:
    """
    Генерує рядок CSV.

    Структура (3 колонки):
    1. Час
    2. Дата
    3. Сума, грн

    Args:
        date: Дата та час транзакції
        amount: Сума транзакції

    Returns:
        Список з 3 елементами для CSV рядка
    """
    time_str = format_time(date)
    date_str = format_date(date)
    amount_str = format_amount(amount)

    return [
        time_str,      # Час
        date_str,      # Дата
        amount_str     # Сума
    ]
