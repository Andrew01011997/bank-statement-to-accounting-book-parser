# -*- coding: utf-8 -*-
"""
Парсер для виписок Monobank
"""

from typing import Dict, Optional, Tuple
import re
from ..core.table_parser import TableParser
from ..core.statement import Transaction
from ..utils import constants, validators


class MonobankParser(TableParser):
    """Парсер для виписок Monobank (таблиці; комісія еквайрингу з "Деталі операції")."""

    CONTROL_SUM_PATTERN = constants.MONOBANK_CONTROL_SUM_PATTERN

    COLUMN_KEYWORDS = {
        'date': ['дата', 'час'],
        'amount': ['сума', 'операц'],
        'details': ['деталі'],
    }

    def _is_header(self, row_text: str) -> bool:
        return 'дата' in row_text and 'сума' in row_text and 'операц' in row_text

    def _detect_columns(self, row, columns: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
        indices = self._find_column_indices(row, self.COLUMN_KEYWORDS)
        # Заголовок повністю визначає колонки цієї таблиці (відсутні -> None)
        return {name: indices.get(name) for name in self.COLUMN_KEYWORDS}

    def _build_transaction(self, cells: Dict[str, Optional[str]]) -> Optional[Transaction]:
        date_cell = cells.get('date')
        amount_cell = cells.get('amount')

        if not date_cell or not amount_cell:
            return None

        date_obj = self._extract_date(date_cell)
        if not date_obj:
            return None

        # Колонка "Сума операції" - сума, що надійшла (після комісії)
        net_amount = self._extract_amount(amount_cell)
        if not net_amount:
            return None

        gross_from_details, commission = self._extract_commission_from_details(cells.get('details'))

        if gross_from_details and commission:
            # Еквайринг з комісією
            gross_amount = gross_from_details
        else:
            # Звичайний переказ без комісії
            gross_amount = net_amount
            commission = 0.0

        return Transaction(
            date=date_obj,
            gross_amount=gross_amount,
            commission=commission,
            net_amount=net_amount
        )

    def _extract_commission_from_details(self, details: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Витягує суму та комісію з колонки "Деталі операції".

        Формат: "Еквайринг, MQ000001, Загалом 1000.00 грн. Комісія банку 13.00 грн."

        Returns:
            Tuple (gross_amount, commission); None для того, що не знайдено
        """
        if not details:
            return None, None

        return (
            self._search_amount(constants.GROSS_AMOUNT_PATTERN, details),
            self._search_amount(constants.COMMISSION_PATTERN, details),
        )

    @staticmethod
    def _search_amount(pattern: str, text: str) -> Optional[float]:
        """Шукає суму за regex (група 1) у тексті."""
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None

        try:
            return validators.to_float(match.group(1))
        except ValueError:
            return None
