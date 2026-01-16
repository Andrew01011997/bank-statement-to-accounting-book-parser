# -*- coding: utf-8 -*-
"""
Генерація CSV файлів для Книги обліку доходів
"""

import csv
from typing import List
from ..core.statement import Transaction
from ..utils import constants, formatters


class CSVWriter:
    """Генерація CSV файлів."""

    @staticmethod
    def write(transactions: List[Transaction], output_path: str) -> None:
        """
        Записує транзакції у CSV файл.

        Структура CSV (5 колонок):
        1. Час
        2. Дата
        3. Сума (gross - до комісії)
        4. Комісія
        5. Сума з врахуванням комісії (net - після комісії)

        Транзакції записуються у зворотному порядку (reversed).

        Args:
            transactions: Список транзакцій
            output_path: Шлях до вихідного CSV файлу
        """
        with open(output_path, 'w', newline='', encoding=constants.CSV_ENCODING) as csvfile:
            writer = csv.writer(csvfile)

            # Записуємо заголовки
            writer.writerow(formatters.CSV_HEADERS)

            # Записуємо транзакції у зворотному порядку
            for trans in reversed(transactions):
                row = formatters.format_csv_row(trans)
                writer.writerow(row)

        print(f"CSV файл створено: {output_path}")
