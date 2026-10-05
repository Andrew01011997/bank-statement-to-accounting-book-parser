# -*- coding: utf-8 -*-
"""
Загальний парсер для невідомих форматів банків (fallback)
"""

from typing import List
from ..core.base_parser import BaseParser
from ..core.statement import Transaction


class GenericParser(BaseParser):
    """Загальний парсер для невідомих форматів банків (fallback, без контрольної суми)."""

    def parse(self, pdf) -> List[Transaction]:
        """Універсальний парсинг: перша дата і перша сума в кожному рядку таблиці."""
        transactions = []

        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue

                for row in table:
                    if not row or len(row) < 2:
                        continue

                    date_obj = None
                    amount = None

                    for cell in row:
                        if not cell:
                            continue
                        if not date_obj:
                            date_obj = self._extract_date(cell)
                        if not amount:
                            amount = self._extract_amount(cell)  # Фільтрує негативні!

                    # Generic парсер не підтримує комісію - gross = net
                    if date_obj and amount:
                        transactions.append(Transaction(
                            date=date_obj,
                            gross_amount=amount,
                            commission=0.0
                        ))

        return transactions
