# -*- coding: utf-8 -*-
"""
Парсер для виписок Monobank з використанням Camelot
"""

from typing import List, Optional, Tuple
import re
import camelot
from datetime import datetime
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants


class MonobankParserCamelot(BaseParser):
    """Парсер для виписок Monobank з використанням Camelot."""

    def _extract_transaction_from_text(self, text: str) -> Optional[Tuple[datetime, float]]:
        """
        Витягує дату+час і суму транзакції з багаторядкового тексту Camelot.

        Структура тексту:
        Name
        Date (30.04.2025)
        Details
        IBAN:
        AMOUNT1   <-- Сума транзакції (ПЕРША після дати)
        UAH
        AMOUNT2   <-- Дублікат
        —
        —
        BALANCE   <-- Залишок (зазвичай набагато більший)
        ...
        Time (20:58:41)  <-- Час набагато пізніше

        Returns:
            (datetime, amount) або None
        """
        # Витягуємо дату окремо
        date_match = re.search(constants.DATE_PATTERN, text)
        if not date_match:
            return None

        date_str = date_match.group(1)
        date_end_pos = date_match.end()

        # Шукаємо час в всьому тексті
        time_match = re.search(constants.TIME_PATTERN, text)
        time_str = time_match.group(1) if time_match else "00:00:00"

        # Створюємо datetime об'єкт
        try:
            date_obj = datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M:%S')
        except ValueError:
            return None

        # Шукаємо ПЕРШУ суму ПІСЛЯ "IBAN:" (або після дати якщо IBAN немає)
        text_after_date = text[date_end_pos:]

        # Спробуємо знайти IBAN як орієнтир
        iban_match = re.search(r'IBAN:', text_after_date, re.IGNORECASE)

        if iban_match:
            # Якщо є IBAN, шукаємо ПЕРШУ суму після нього
            text_after_iban = text_after_date[iban_match.end():]
            amount_pattern = r'(\d[\d\s]*\.\d{2})'
            amount_match = re.search(amount_pattern, text_after_iban)
        else:
            # Якщо немає IBAN, шукаємо перше число + UAH після дати
            amount_pattern = r'(\d[\d\s]*\.\d{2})\s*\n?\s*UAH'
            amount_match = re.search(amount_pattern, text_after_date)

        if not amount_match:
            return None

        try:
            amount_str = amount_match.group(1).replace(' ', '').replace('\xa0', '')
            amount = float(amount_str)

            # Перевіряємо що сума позитивна і в розумних межах
            if amount > 0 and amount < 1000000:  # Максимум 1 млн
                return (date_obj, amount)

        except ValueError:
            pass

        return None

    def extract_control_sum(self, pdf_path: str) -> Optional[float]:
        """
        Витягує контрольну суму 'Обіг за кредитом за період'.
        Використовуємо pdfplumber для цього, бо camelot працює з таблицями.
        """
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                match = re.search(r'Обіг за кредитом за період:\s*([\d\s]+\.?\d*)\s*UAH', text, re.IGNORECASE)

                if match:
                    amount_str = match.group(1).replace(' ', '').replace('\xa0', '')
                    return float(amount_str)
        except Exception:
            pass

        return None

    def parse(self, pdf_path: str) -> List[Transaction]:
        """
        Парсинг Monobank виписки з використанням Camelot.

        Args:
            pdf_path: Шлях до PDF файлу

        Returns:
            Список транзакцій
        """
        transactions = []

        # Використовуємо lattice mode (для таблиць з лініями)
        tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')

        print(f"  Camelot знайшов {len(tables)} таблиць")

        for table_idx, table in enumerate(tables):
            df = table.df

            # Camelot часто зливає всі дані в одну колонку
            # Шукаємо заголовок для ідентифікації таблиці
            header_found = False

            for i, row in df.iterrows():
                row_text = ' '.join([str(cell).lower() if cell else '' for cell in row.values])

                # Якщо це заголовок - пропускаємо
                if 'дата' in row_text and 'сума' in row_text and 'операц' in row_text:
                    header_found = True
                    continue

                # Якщо заголовок знайдено - парсимо рядки даних
                if header_found:
                    try:
                        # Витягуємо весь текст з першої колонки
                        cell_text = str(row.iloc[0]) if len(row) > 0 else ''

                        if not cell_text or cell_text == 'nan':
                            continue

                        # Використовуємо спеціальний метод для Camelot тексту
                        result = self._extract_transaction_from_text(cell_text)

                        if result:
                            date_obj, amount = result
                            transactions.append(Transaction(
                                date=date_obj,
                                amount=amount
                            ))

                    except (ValueError, TypeError, IndexError):
                        continue

        return transactions
