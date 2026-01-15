# -*- coding: utf-8 -*-
"""
Загальний парсер для невідомих форматів банків (fallback)
"""

from typing import List
from ..core.base_parser import BaseParser
from ..core.statement import Transaction


class GenericParser(BaseParser):
    """Загальний парсер для невідомих форматів банків (fallback)."""

    def parse(self, pdf) -> List[Transaction]:
        """Універсальний парсинг."""
        transactions = []

        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                for row in table:
                    if not row or len(row) < 2:
                        continue

                    # Шукаємо дату та суму в будь-якій комірці
                    date_obj = None
                    amount = None

                    for cell in row:
                        if not cell:
                            continue

                        # Пробуємо витягти дату
                        if not date_obj:
                            date_obj = self._extract_date(cell)

                        # Пробуємо витягти суму
                        if not amount:
                            amount = self._extract_amount(cell)  # Фільтрує негативні!

                    # Додаємо транзакцію, якщо знайшли обидва поля
                    if date_obj and amount:
                        transactions.append(Transaction(
                            date=date_obj,
                            amount=amount
                        ))

        return transactions
