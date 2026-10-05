# -*- coding: utf-8 -*-
"""
Менеджер для координації парсингу банківських виписок
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
    """Менеджер для координації парсингу банківських виписок."""

    def __init__(self, input_dir='input', output_dir='output'):
        """
        Ініціалізація менеджера.

        Args:
            input_dir: Папка з вхідними PDF файлами
            output_dir: Папка для вихідних CSV файлів
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Створюємо вихідну папку, якщо не існує
        self.output_dir.mkdir(exist_ok=True)

    def run(self) -> None:
        """Запуск парсера для всіх файлів у папці input."""
        print("=== Парсер банківських виписок ===\n")

        if not self.input_dir.exists():
            print(f"❌ Папка {self.input_dir} не існує!")
            return

        pdf_files = list(self.input_dir.glob('*.pdf'))

        if not pdf_files:
            print(f"❌ Не знайдено PDF файлів у папці {self.input_dir}")
            return

        print(f"Знайдено {len(pdf_files)} файл(ів) для обробки\n")

        for pdf_file in pdf_files:
            self.process_file(pdf_file)
            print()

        print("✓ Обробку завершено!")

    def process_file(self, pdf_file: Path) -> None:
        """
        Обробка одного PDF файлу: визначення банку -> парсинг -> перевірка -> CSV.

        Args:
            pdf_file: Шлях до PDF файлу
        """
        print(f"Обробка файлу: {pdf_file.name}")

        try:
            with PDFReader.open(str(pdf_file)) as pdf:
                bank_type = BankDetector.detect_from_pdf(pdf)
                print(f"  Тип банку: {bank_type.capitalize()}")

                parser = BankDetector.get_parser(bank_type)
                transactions = parser.parse(pdf)
                control_sum = parser.extract_control_sum(pdf)

            for warning in parser.warnings:
                print(f"  ⚠️  {warning}")

            if control_sum and transactions:
                self._report_control_sum(transactions, control_sum)

            self._write_csv(pdf_file, transactions)

        except Exception as e:
            print(f"Помилка при обробці файлу {pdf_file}: {e}")
            traceback.print_exc()

    @staticmethod
    def _report_control_sum(transactions: List[Transaction], control_sum: float) -> None:
        """
        Порівнює контрольну суму з випискою та звітує.

        Обіг за кредитом - це зараховані суми, тобто net_amount (після комісії).
        """
        actual_sum = sum(t.net_amount for t in transactions)
        difference = abs(control_sum - actual_sum)

        if difference > constants.CONTROL_SUM_TOLERANCE:
            print(f"  ⚠️  ПОПЕРЕДЖЕННЯ: Сума транзакцій не співпадає з контрольною сумою!")
            print(f"      Контрольна сума з виписки: {control_sum:.2f} UAH")
            print(f"      Сума розпарсених транзакцій (зараховано): {actual_sum:.2f} UAH")
            print(f"      Різниця: {difference:.2f} UAH")
            print(f"      Можливо, деякі транзакції не були розпізнані через формат PDF.")
        else:
            print(f"  ✓ Контрольна сума співпадає: {control_sum:.2f} UAH")

        # Додатково виводимо інформацію про комісії
        total_commission = sum(t.commission for t in transactions)
        if total_commission > 0:
            gross_sum = sum(t.gross_amount for t in transactions)
            print(f"  ℹ️  Загальна комісія: {total_commission:.2f} UAH")
            print(f"  ℹ️  Дохід до комісії (gross, у Книгу): {gross_sum:.2f} UAH")

    def _write_csv(self, pdf_file: Path, transactions: Optional[List[Transaction]]) -> None:
        """Записує CSV з тією ж назвою, що й PDF."""
        if not transactions:
            print(f"  ⚠️ Не знайдено транзакцій у файлі {pdf_file.name}")
            return

        output_path = self.output_dir / (pdf_file.stem + '.csv')
        CSVWriter.write(transactions, str(output_path))
        print(f"  ✓ Знайдено {len(transactions)} транзакцій")
