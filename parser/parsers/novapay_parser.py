# -*- coding: utf-8 -*-
"""
NovaPay statement parser.
"""

from typing import Dict, Optional
from ..core.table_parser import TableParser
from ..core.statement import Transaction
from ..utils import constants, dates


class NovaPayParser(TableParser):
    """NovaPay statements (tables; comma decimal separator; time without seconds)."""

    CONTROL_SUM_PATTERN = constants.NOVAPAY_CONTROL_SUM_PATTERN
    CONTROL_SUM_PAGE = -1  # "Обороти по кредиту" is on the last page
    DECIMAL_COMMA = True
    # NovaPay's format without seconds ("01.07.2025 10:30") is tried first
    DATE_FORMATS = (dates.DATETIME_SHORT, dates.DATETIME_FULL, dates.DATE_ONLY)

    def _is_header(self, row_text: str) -> bool:
        # NovaPay columns: "Дата/час операції", "Сума, UAH"
        return 'дата' in row_text and 'сума' in row_text

    def _detect_columns(self, row, columns: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
        # Columns missing from this header keep their indices from earlier tables
        columns = dict(columns)

        for j, cell in enumerate(row):
            if not cell:
                continue
            cell_lower = str(cell).lower()

            if 'дата' in cell_lower and ('час' in cell_lower or 'операц' in cell_lower):
                columns['date'] = j
            elif 'сума' in cell_lower and 'uah' in cell_lower:
                columns['amount'] = j

        return columns

    def _build_transaction(self, cells: Dict[str, Optional[str]]) -> Optional[Transaction]:
        date_cell = cells.get('date')
        amount_cell = cells.get('amount')

        if not date_cell or not amount_cell:
            return None

        date_obj = self._extract_date(date_cell)
        amount = self._extract_amount(amount_cell)

        if not (date_obj and amount):
            return None

        # NovaPay statements carry no commission: gross = net
        return Transaction(date=date_obj, gross_amount=amount, commission=0.0)
