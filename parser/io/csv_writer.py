# -*- coding: utf-8 -*-
"""
CSV generation for the income ledger ("Книга обліку доходів").
"""

import csv
from typing import List
from ..core.statement import Transaction
from ..utils import constants, formatters


class CSVWriter:
    """Writes ledger CSV files."""

    @staticmethod
    def write(transactions: List[Transaction], output_path: str) -> None:
        """
        Writes transactions to a CSV file.

        CSV layout (5 columns, Ukrainian headers as required by the ledger):
        1. Час - time
        2. Дата - date
        3. Сума - gross amount (before commission)
        4. Комісія - commission
        5. Сума з врахуванням комісії - net amount (after commission)

        Transactions are written in reverse parse order. That is chronological only for
        newest-first statements (verified for PrivatBank only, see docs/KNOWN_ISSUES.md #11).

        Args:
            transactions: Transactions to write
            output_path: Path to the output CSV file
        """
        with open(output_path, 'w', newline='', encoding=constants.CSV_ENCODING) as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(formatters.CSV_HEADERS)

            # Chronological for newest-first statements; unverified for Monobank/NovaPay (KNOWN_ISSUES #11)
            for trans in reversed(transactions):
                row = formatters.format_csv_row(trans)
                writer.writerow(row)

        print(f"CSV written: {output_path}")
