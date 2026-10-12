# -*- coding: utf-8 -*-
"""
Orchestrates parsing of bank statements.
"""

import traceback
from pathlib import Path
from typing import List, Optional
from .bank_detector import BankDetector
from .core.statement import Transaction
from .io.pdf_reader import PDFReader
from .io.csv_writer import CSVWriter
from .utils import constants


class StatementParserManager:
    """Orchestrates parsing of bank statements."""

    def __init__(self, input_dir='input', output_dir='output'):
        """
        Args:
            input_dir: Folder with input PDF statements
            output_dir: Folder for output CSV files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Create the output folder if it does not exist
        self.output_dir.mkdir(exist_ok=True)

    def run(self) -> int:
        """
        Parses every PDF in the input folder.

        Returns:
            Number of failures: files that raised an error, or 1 if the input folder is unusable
        """
        print("=== Bank statement parser ===\n")

        if not self.input_dir.exists():
            print(f"❌ Folder {self.input_dir} does not exist!")
            return 1

        if not self.input_dir.is_dir():
            print(f"❌ {self.input_dir} is not a folder!")
            return 1

        try:
            # Case-insensitive extension (*.PDF on Linux/macOS) and the same order on every OS
            pdf_files = sorted((p for p in self.input_dir.iterdir()
                                if p.is_file() and p.suffix.lower() == '.pdf'),
                               key=lambda p: (p.name.casefold(), p.name))
        except OSError as e:
            print(f"❌ Cannot read folder {self.input_dir}: {e}")
            return 1

        if not pdf_files:
            print(f"❌ No PDF files found in {self.input_dir}")
            return 0

        print(f"Found {len(pdf_files)} file(s) to process\n")

        failures = 0
        for pdf_file in pdf_files:
            if not self.process_file(pdf_file):
                failures += 1
            print()

        if failures:
            print(f"❌ Done with errors: {failures} of {len(pdf_files)} file(s) failed")
        else:
            print("✓ Done!")
        return failures

    def process_file(self, pdf_file: Path) -> bool:
        """
        Processes one PDF: detect bank -> parse -> verify -> CSV.

        Args:
            pdf_file: Path to the PDF file

        Returns:
            False if processing raised an error, True otherwise
        """
        print(f"Processing: {pdf_file.name}")

        try:
            with PDFReader.open(str(pdf_file)) as pdf:
                bank_type = BankDetector.detect_from_pdf(pdf)
                print(f"  Bank: {bank_type.capitalize()}")

                parser = BankDetector.get_parser(bank_type)
                transactions = parser.parse(pdf)
                control_sum = parser.extract_control_sum(pdf)

            for warning in parser.warnings:
                print(f"  ⚠️  {warning}")

            if control_sum and transactions:
                self._report_control_sum(transactions, control_sum)

            self._write_csv(pdf_file, transactions)

        except Exception as e:
            print(f"Error while processing {pdf_file}: {e}")
            traceback.print_exc()
            return False

        return True

    @staticmethod
    def _report_control_sum(transactions: List[Transaction], control_sum: float) -> None:
        """
        Compares the statement's control sum with the parsed transactions.

        The credit turnover counts what was credited, i.e. net_amount (after commission).
        """
        actual_sum = sum(t.net_amount for t in transactions)
        difference = abs(control_sum - actual_sum)

        if difference > constants.CONTROL_SUM_TOLERANCE:
            print("  ⚠️  WARNING: transaction total does not match the control sum!")
            print(f"      Control sum from statement: {control_sum:.2f} UAH")
            print(f"      Parsed transactions (credited): {actual_sum:.2f} UAH")
            print(f"      Difference: {difference:.2f} UAH")
            print("      Some transactions may not have been recognised due to the PDF layout.")
        else:
            print(f"  ✓ Control sum matches: {control_sum:.2f} UAH")

        total_commission = sum(t.commission for t in transactions)
        if total_commission > 0:
            gross_sum = sum(t.gross_amount for t in transactions)
            print(f"  ℹ️  Total commission: {total_commission:.2f} UAH")
            print(f"  ℹ️  Income before commission (gross, goes to the ledger): {gross_sum:.2f} UAH")

    def _write_csv(self, pdf_file: Path, transactions: Optional[List[Transaction]]) -> None:
        """Writes a CSV named after the PDF."""
        if not transactions:
            print(f"  ⚠️ No transactions found in {pdf_file.name}")
            return

        output_path = self.output_dir / (pdf_file.stem + '.csv')
        CSVWriter.write(transactions, str(output_path))
        print(f"  ✓ {len(transactions)} transaction(s) found")
