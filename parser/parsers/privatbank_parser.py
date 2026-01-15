# -*- coding: utf-8 -*-
"""
Парсер для виписок PrivatBank
"""

from typing import List, Optional
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction


class PrivatBankParser(BaseParser):
    """Парсер для виписок PrivatBank."""

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму 'разом за кредитом' з першої сторінки.

        Returns:
            Контрольна сума або None
        """
        try:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Шукаємо "разом за кредитом: 12 345.67"
            match = re.search(r'разом за кредитом:\s*([\d\s]+\.?\d*)', text, re.IGNORECASE)

            if match:
                amount_str = match.group(1).replace(' ', '').replace('\xa0', '')
                return float(amount_str)
        except Exception:
            pass

        return None

    def parse(self, pdf) -> List[Transaction]:
        """Парсинг PrivatBank виписки."""
        transactions = []

        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # Шукаємо заголовок
                header_row_idx = None
                date_col = self.saved_date_col
                amount_col = self.saved_amount_col

                for i, row in enumerate(table):
                    if not row:
                        continue

                    row_text = ' '.join([str(cell).lower() if cell else '' for cell in row])

                    # Характерні колонки PrivatBank
                    if 'дата' in row_text and 'сума' in row_text and ('призначення' in row_text or 'документ' in row_text):
                        header_row_idx = i

                        # Знаходимо індекси
                        for j, cell in enumerate(row):
                            if not cell:
                                continue
                            cell_lower = str(cell).lower()

                            if 'дата' in cell_lower and ('час' in cell_lower or 'операц' in cell_lower):
                                date_col = j
                                self.saved_date_col = j
                            elif cell_lower.strip() == 'сума':
                                amount_col = j
                                self.saved_amount_col = j

                        break

                # Парсимо дані
                if date_col is not None and amount_col is not None:
                    start_row = header_row_idx + 1 if header_row_idx is not None else 0

                    for i, row in enumerate(table):
                        if i < start_row or not row:
                            continue

                        try:
                            date_cell = row[date_col] if date_col < len(row) else None
                            amount_cell = row[amount_col] if amount_col < len(row) else None

                            # Якщо немає дати або суми - пропускаємо рядок
                            # (це може бути продовження рядка з попередньої сторінки)
                            if not date_cell or not amount_cell:
                                continue

                            # Витягуємо дату/час та суму
                            date_obj = self._extract_date(date_cell)
                            amount = self._extract_amount(amount_cell)

                            # Додаємо транзакцію, якщо дата і сума валідні
                            if date_obj and amount:
                                transactions.append(Transaction(
                                    date=date_obj,
                                    amount=amount
                                ))

                        except (ValueError, TypeError, IndexError):
                            continue

        return transactions
