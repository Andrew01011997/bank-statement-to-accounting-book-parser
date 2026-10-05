# -*- coding: utf-8 -*-
"""
Парсер для виписок Monobank
"""

from typing import Dict, Optional
from ..core.table_parser import TableParser
from ..core.statement import Transaction
from ..utils import constants


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

        # Комісія - з "Деталі операції" (еквайринг або переказ від платіжної системи)
        return self._make_transaction(date_obj, net_amount, cells.get('details'))
