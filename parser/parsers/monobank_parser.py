# -*- coding: utf-8 -*-
"""
Парсер для виписок Monobank
"""

from typing import List, Optional, Tuple
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants


class MonobankParser(BaseParser):
    """Парсер для виписок Monobank."""

    def __init__(self):
        super().__init__()
        self.saved_details_col = None

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму 'Обіг за кредитом за період' з першої сторінки.

        Returns:
            Контрольна сума або None
        """
        try:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Шукаємо "Обіг за кредитом за період:687 454.00 UAH"
            match = re.search(r'Обіг за кредитом за період:\s*([\d\s]+\.?\d*)\s*UAH', text, re.IGNORECASE)

            if match:
                amount_str = match.group(1).replace(' ', '').replace('\xa0', '')
                return float(amount_str)
        except Exception:
            pass

        return None

    def _extract_commission_from_details(self, details: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Витягує суму та комісію з колонки "Деталі операції".

        Формат: "Еквайринг, MQ024663, Загалом 4000.00 грн. Комісія банку 52.00 грн."

        Args:
            details: Текст з деталями операції

        Returns:
            Tuple (gross_amount, commission) або (None, None) якщо не знайдено
        """
        if not details:
            return None, None

        gross_amount = None
        commission = None

        # Шукаємо "Загалом X грн"
        gross_match = re.search(constants.GROSS_AMOUNT_PATTERN, details, re.IGNORECASE)
        if gross_match:
            gross_str = gross_match.group(1).replace(' ', '').replace('\xa0', '')
            try:
                gross_amount = float(gross_str)
            except ValueError:
                pass

        # Шукаємо "Комісія банку X грн"
        commission_match = re.search(constants.COMMISSION_PATTERN, details, re.IGNORECASE)
        if commission_match:
            commission_str = commission_match.group(1).replace(' ', '').replace('\xa0', '')
            try:
                commission = float(commission_str)
            except ValueError:
                pass

        return gross_amount, commission

    def parse(self, pdf) -> List[Transaction]:
        """Парсинг Monobank виписки."""
        transactions = []

        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table_idx, table in enumerate(tables):
                if not table:
                    continue

                # Шукаємо заголовок
                header_row_idx = None
                date_col = self.saved_date_col
                amount_col = self.saved_amount_col
                details_col = self.saved_details_col

                for i, row in enumerate(table):
                    if not row:
                        continue

                    row_text = ' '.join([str(cell).lower() if cell else '' for cell in row])

                    # Характерні колонки Monobank
                    if 'дата' in row_text and 'сума' in row_text and 'операц' in row_text:
                        header_row_idx = i

                        # Знаходимо індекси колонок
                        indices = self._find_column_indices(row, {
                            'date': ['дата', 'час'],
                            'amount': ['сума', 'операц'],
                            'details': ['деталі']
                        })

                        date_col = indices.get('date')
                        amount_col = indices.get('amount')
                        details_col = indices.get('details')

                        if date_col is not None:
                            self.saved_date_col = date_col
                        if amount_col is not None:
                            self.saved_amount_col = amount_col
                        if details_col is not None:
                            self.saved_details_col = details_col

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
                            details_cell = row[details_col] if details_col is not None and details_col < len(row) else None

                            # Якщо немає дати або суми - пропускаємо рядок
                            if not date_cell or not amount_cell:
                                continue

                            # Витягуємо дату/час
                            date_obj = self._extract_date(date_cell)
                            if not date_obj:
                                continue

                            # Перевіряємо чи є комісія в деталях операції
                            gross_from_details, commission = self._extract_commission_from_details(details_cell)

                            # Витягуємо суму з колонки "Сума операції"
                            net_amount = self._extract_amount(amount_cell)
                            if not net_amount:
                                continue

                            # Визначаємо gross_amount та commission
                            if gross_from_details and commission:
                                # Еквайринг з комісією
                                gross_amount = gross_from_details
                            else:
                                # Звичайний переказ без комісії
                                gross_amount = net_amount
                                commission = 0.0

                            transactions.append(Transaction(
                                date=date_obj,
                                gross_amount=gross_amount,
                                commission=commission,
                                net_amount=net_amount
                            ))

                        except (ValueError, TypeError, IndexError):
                            continue

        return transactions
