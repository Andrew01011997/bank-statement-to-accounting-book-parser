# -*- coding: utf-8 -*-
"""
Менеджер для координації парсингу банківських виписок
"""

from pathlib import Path
from .bank_detector import BankDetector
from .io.pdf_reader import PDFReader
from .io.csv_writer import CSVWriter


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

    def process_file(self, pdf_file: Path) -> None:
        """
        Обробка одного PDF файлу.

        Args:
            pdf_file: Шлях до PDF файлу
        """
        print(f"Обробка файлу: {pdf_file.name}")

        try:
            # 1. Визначаємо тип банку
            bank_type = BankDetector.detect(str(pdf_file))
            print(f"  Тип банку: {bank_type.capitalize()}")

            # 2. Отримуємо відповідний парсер
            parser = BankDetector.get_parser(bank_type)

            # 3. Парсимо PDF та отримуємо контрольну суму
            with PDFReader.open(str(pdf_file)) as pdf:
                transactions = parser.parse(pdf)
                control_sum = parser.extract_control_sum(pdf)

            # 4. Валідація контрольної суми (по gross_amount - сума до комісії)
            if control_sum and transactions:
                actual_sum = sum(t.gross_amount for t in transactions)
                difference = abs(control_sum - actual_sum)

                if difference > 0.01:  # Допускаємо різницю в 1 копійку через округлення
                    print(f"  ⚠️  ПОПЕРЕДЖЕННЯ: Сума транзакцій не співпадає з контрольною сумою!")
                    print(f"      Контрольна сума з виписки: {control_sum:.2f} UAH")
                    print(f"      Сума розпарсених транзакцій (gross): {actual_sum:.2f} UAH")
                    print(f"      Різниця: {difference:.2f} UAH")
                    print(f"      Можливо, деякі транзакції не були розпізнані через формат PDF.")
                else:
                    print(f"  ✓ Контрольна сума співпадає: {control_sum:.2f} UAH")

                # Додатково виводимо інформацію про комісії
                total_commission = sum(t.commission for t in transactions)
                if total_commission > 0:
                    net_sum = sum(t.net_amount for t in transactions)
                    print(f"  ℹ️  Загальна комісія: {total_commission:.2f} UAH")
                    print(f"  ℹ️  Сума після комісії (net): {net_sum:.2f} UAH")

            # 5. Генеруємо CSV
            if transactions:
                output_filename = pdf_file.stem + '.csv'
                output_path = self.output_dir / output_filename

                CSVWriter.write(transactions, str(output_path))
                print(f"  ✓ Знайдено {len(transactions)} транзакцій")
            else:
                print(f"  ⚠️ Не знайдено транзакцій у файлі {pdf_file.name}")

        except Exception as e:
            print(f"Помилка при обробці файлу {pdf_file}: {e}")
            import traceback
            traceback.print_exc()

    def run(self) -> None:
        """Запуск парсера для всіх файлів у папці input."""
        print("=== Парсер банківських виписок ===\n")

        # Перевіряємо наявність вхідної папки
        if not self.input_dir.exists():
            print(f"❌ Папка {self.input_dir} не існує!")
            return

        # Знаходимо всі PDF файли
        pdf_files = list(self.input_dir.glob('*.pdf'))

        if not pdf_files:
            print(f"❌ Не знайдено PDF файлів у папці {self.input_dir}")
            return

        print(f"Знайдено {len(pdf_files)} файл(ів) для обробки\n")

        # Обробляємо кожен файл
        for pdf_file in pdf_files:
            self.process_file(pdf_file)
            print()

        print("✓ Обробку завершено!")
