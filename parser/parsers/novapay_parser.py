# -*- coding: utf-8 -*-
"""
Парсер для виписок NovaPay
"""

from typing import List, Optional
from datetime import datetime
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants, validators


class NovaPayParser(BaseParser):
    """Парсер для виписок NovaPay."""

    def _extract_date_novapay(self, date_str: str) -> Optional[datetime]:
        """
        Витягує дату та час з рядка у форматі NovaPay (без секунд).

        Args:
            date_str: Рядок з датою (формат: "01.07.2025 10:30")

        Returns:
            datetime об'єкт або None якщо дату не знайдено
        """
        if not date_str:
            return None

        date_str_cleaned = str(date_str).strip()

        # Спочатку пробуємо формат NovaPay: dd.mm.yyyy HH:MM (без секунд)
        datetime_match = re.search(constants.DATETIME_PATTERN_SHORT, date_str_cleaned)
        if datetime_match:
            try:
                date_part = datetime_match.group(1)
                time_part = datetime_match.group(2)
                datetime_str = f"{date_part} {time_part}"
                return datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')
            except ValueError:
                pass

        # Якщо не вдалося, пробуємо стандартний формат з секундами
        datetime_match = re.search(constants.DATETIME_PATTERN, date_str_cleaned)
        if datetime_match:
            try:
                date_part = datetime_match.group(1)
                time_part = datetime_match.group(2)
                datetime_str = f"{date_part} {time_part}"
                return datetime.strptime(datetime_str, '%d.%m.%Y %H:%M:%S')
            except ValueError:
                pass

        # Якщо не вдалося витягти час, витягуємо тільки дату
        date_match = re.search(constants.DATE_PATTERN, date_str_cleaned)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%d.%m.%Y')
            except ValueError:
                pass

        return None

    def _extract_amount_novapay(self, amount_str: str) -> Optional[float]:
        """
        Витягує суму у форматі NovaPay (кома як десятковий розділювач).

        Args:
            amount_str: Рядок з сумою (формат: "1 234,56" або "-5 000,00")

        Returns:
            float якщо валідна позитивна сума, інакше None
        """
        if not amount_str:
            return None

        amount_str_cleaned = str(amount_str).strip()

        # Перевіряємо на негативність
        if validators.is_negative_amount(amount_str_cleaned):
            return None

        # Видаляємо пробіли та замінюємо кому на крапку
        cleaned = re.sub(constants.WHITESPACE_PATTERN, '', amount_str_cleaned)
        cleaned = cleaned.replace(',', '.')

        # Витягуємо число
        match = re.search(r'(\d+(?:\.\d{2})?)', cleaned)
        if not match:
            return None

        try:
            amount = float(match.group(1))
            return amount if validators.is_valid_amount(amount) else None
        except ValueError:
            return None

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму 'Обороти по кредиту' з останньої сторінки.

        Returns:
            Контрольна сума або None
        """
        try:
            # Шукаємо на останній сторінці
            last_page = pdf.pages[-1]
            text = last_page.extract_text()

            # Шукаємо "Обороти по кредиту: 12 345,67 грн"
            match = re.search(
                r'Обороти по кредиту:\s*([\d\s]+,\d{2})\s*грн',
                text,
                re.IGNORECASE
            )

            if match:
                amount_str = match.group(1)
                # Видаляємо пробіли та замінюємо кому на крапку
                cleaned = re.sub(r'[\s\xa0]', '', amount_str)
                cleaned = cleaned.replace(',', '.')
                return float(cleaned)
        except Exception:
            pass

        return None

    def parse(self, pdf) -> List[Transaction]:
        """Парсинг NovaPay виписки."""
        transactions = []

        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # Шукаємо заголовок
                header_row_idx = None
                date_col = self.saved_date_col
                amount_col = self.saved_amount_col

                for i, row in enumerate(table):
                    if not row:
                        continue

                    row_text = ' '.join([str(cell).lower() if cell else '' for cell in row])

                    # Характерні колонки NovaPay: "Дата/час операці", "Сума, UAH"
                    if 'дата' in row_text and 'сума' in row_text:
                        header_row_idx = i

                        # Знаходимо індекси колонок
                        for j, cell in enumerate(row):
                            if not cell:
                                continue
                            cell_lower = str(cell).lower()

                            # Колонка дати/часу операції
                            if 'дата' in cell_lower and ('час' in cell_lower or 'операц' in cell_lower):
                                date_col = j
                                self.saved_date_col = j
                            # Колонка суми
                            elif 'сума' in cell_lower and 'uah' in cell_lower:
                                amount_col = j
                                self.saved_amount_col = j

                        break

                # Парсимо дані
                if date_col is not None and amount_col is not None:
                    start_row = header_row_idx + 1 if header_row_idx is not None else 0

                    for i, row in enumerate(table):
                        if i < start_row or not row:
                            continue

                        try:
                            date_cell = row[date_col] if date_col < len(row) else None
                            amount_cell = row[amount_col] if amount_col < len(row) else None

                            # Якщо немає дати або суми - пропускаємо рядок
                            if not date_cell or not amount_cell:
                                continue

                            # Витягуємо дату/час та суму
                            date_obj = self._extract_date_novapay(date_cell)
                            amount = self._extract_amount_novapay(amount_cell)

                            # Додаємо транзакцію, якщо дата і сума валідні
                            if date_obj and amount:
                                transactions.append(Transaction(
                                    date=date_obj,
                                    amount=amount
                                ))

                        except (ValueError, TypeError, IndexError):
                            continue

        return transactions
