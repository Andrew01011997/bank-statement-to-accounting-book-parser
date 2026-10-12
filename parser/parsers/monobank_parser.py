# -*- coding: utf-8 -*-
"""
Monobank statement parser.
"""

from typing import Dict, Optional
from ..core.table_parser import TableParser
from ..core.statement import Transaction
from ..utils import constants


class MonobankParser(TableParser):
    """Monobank statements (tables; acquiring commission from "Деталі операції")."""

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
        # The header fully defines this table's columns (missing ones -> None)
        return {name: indices.get(name) for name in self.COLUMN_KEYWORDS}

    def _build_transaction(self, cells: Dict[str, Optional[str]]) -> Optional[Transaction]:
        date_cell = cells.get('date')
        amount_cell = cells.get('amount')

        if not date_cell or not amount_cell:
            return None

        date_obj = self._extract_date(date_cell)
        if not date_obj:
            return None

        # "Сума операції" is the credited amount (after commission)
        net_amount = self._extract_amount(amount_cell)
        if not net_amount:
            return None

        # Commission comes from "Деталі операції" (acquiring or payment-system transfer)
        return self._make_transaction(date_obj, net_amount, cells.get('details'))
