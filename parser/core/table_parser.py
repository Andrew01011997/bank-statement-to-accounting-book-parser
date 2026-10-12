# -*- coding: utf-8 -*-
"""
Base class for parsers that read PDF tables with a header row (Template Method).
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from .base_parser import BaseParser
from .statement import Transaction


class TableParser(BaseParser):
    """
    Parses pdfplumber tables, detecting columns from the header row.

    Column indices are kept across tables and pages, because later pages
    usually have no header. A parser instance is therefore used for one
    file only.

    Subclasses implement:
        _is_header(row_text) - whether the row is a table header
        _detect_columns(row, columns) - column indices from the header
        _build_transaction(cells) - a transaction from the row cells (or None)
    """

    # Columns without which a table cannot be parsed
    REQUIRED_COLUMNS = ('date', 'amount')

    def __init__(self):
        super().__init__()
        self._saved_columns: Dict[str, int] = {}

    def parse(self, pdf) -> List[Transaction]:
        """Parses all tables on all pages."""
        transactions = []

        for page in pdf.pages:
            for table in self._extract_tables(page):
                if table:
                    transactions.extend(self._parse_table(table))

        return transactions

    @staticmethod
    def _extract_tables(page):
        """
        extract_tables() with the table closed at the bottom.

        When a table is split by a page break, there is no horizontal line under
        its last row and pdfplumber drops that row. We add a line at the bottom of
        the vertical column lines; where a bottom border exists, it coincides with it.
        """
        bottoms = [e['bottom'] for e in getattr(page, 'edges', None) or [] if e.get('orientation') == 'v']
        if not bottoms:
            return page.extract_tables()
        return page.extract_tables({'explicit_horizontal_lines': [max(bottoms)]})

    def _parse_table(self, table) -> List[Transaction]:
        """Parses a single table."""
        columns: Dict[str, Optional[int]] = dict(self._saved_columns)
        header_row_idx = None

        # Find the header
        for i, row in enumerate(table):
            if not row:
                continue

            row_text = ' '.join(str(cell).lower() if cell else '' for cell in row)

            if self._is_header(row_text):
                header_row_idx = i
                columns = self._detect_columns(row, columns)

                for name, idx in columns.items():
                    if idx is not None:
                        self._saved_columns[name] = idx

                break

        if any(columns.get(name) is None for name in self.REQUIRED_COLUMNS):
            return []

        # Parse the data rows
        start_row = header_row_idx + 1 if header_row_idx is not None else 0
        transactions = []

        for row in table[start_row:]:
            if not row:
                continue

            cells = {
                name: row[idx] if idx is not None and idx < len(row) else None
                for name, idx in columns.items()
            }

            try:
                transaction = self._build_transaction(cells)
            except (ValueError, TypeError, IndexError):
                continue

            if transaction:
                transactions.append(transaction)

        return transactions

    @abstractmethod
    def _is_header(self, row_text: str) -> bool:
        """Whether the row (lower-cased cell text) is a table header."""

    @abstractmethod
    def _detect_columns(self, row, columns: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
        """
        Detects column indices from the header row.

        Args:
            row: Header row
            columns: Current (saved) column indices

        Returns:
            Column indices for this table
        """

    @abstractmethod
    def _build_transaction(self, cells: Dict[str, Optional[str]]) -> Optional[Transaction]:
        """
        Builds a transaction from the row cells.

        Args:
            cells: {column name: cell value or None}

        Returns:
            Transaction, or None if the row is not an income transaction
        """

    @staticmethod
    def _find_column_indices(row, keywords: dict) -> dict:
        """
        Finds column indices by keywords.

        Args:
            row: Table row
            keywords: {'date': ['дата', 'час'], 'amount': ['сума', 'операц']}

        Returns:
            {'date': index, 'amount': index}
        """
        indices = {}

        for col_type, keyword_list in keywords.items():
            for j, cell in enumerate(row):
                if not cell:
                    continue

                cell_lower = str(cell).lower()

                # All keywords must be present.
                # For amount, prefer a column without "валют" (avoids "Сума у валюті рахунку")
                if all(keyword in cell_lower for keyword in keyword_list):
                    if col_type == 'amount' and 'валют' in cell_lower:
                        # Use the "account currency" column only if nothing better is found
                        if 'amount' not in indices:
                            indices[col_type] = j
                    else:
                        indices[col_type] = j
                        break  # Take the first match (unless it is a "валют" column)

        return indices
