# -*- coding: utf-8 -*-
"""
Generic parser for unknown statement formats (fallback).
"""

from typing import List
from ..core.base_parser import BaseParser
from ..core.statement import Transaction


class GenericParser(BaseParser):
    """Generic parser for unknown statement formats (fallback, no control sum)."""

    def parse(self, pdf) -> List[Transaction]:
        """Best-effort parsing: the first date and the first amount in every table row."""
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
                            amount = self._extract_amount(cell)  # Filters out negatives!

                    # The generic parser does not support commissions: gross = net
                    if date_obj and amount:
                        transactions.append(Transaction(
                            date=date_obj,
                            gross_amount=amount,
                            commission=0.0
                        ))

        return transactions
