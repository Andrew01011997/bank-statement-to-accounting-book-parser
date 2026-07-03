# -*- coding: utf-8 -*-
"""
Парсер для виписок PrivatBank
"""

from typing import List, Optional
from datetime import datetime
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants, validators


# Рядок транзакції у тексті виписки: "<номер> DD.MM.YYYY <сума> <призначення...>"
# Дата і сума йдуть поруч; сума — число з крапкою і 2 знаками, можливо з мінусом
# та пробілами-роздільниками тисяч (напр. "-1 500.00", "2 000.00").
_TXN_LINE_RE = re.compile(
    r'(\d{2}\.\d{2}\.\d{4})\s+([-−–]?\d[\d\s\xa0]*\.\d{2})(?!\d)'
)
# Час операції (HH:MM) — знаходиться на наступному рядку після рядка з датою.
_TIME_RE = re.compile(r'\b(\d{2}:\d{2})\b')


class PrivatBankParser(BaseParser):
    """Парсер для виписок PrivatBank."""

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму 'разом за кредитом' з першої сторінки.

        Returns:
            Контрольна сума або None
        """
        try:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Шукаємо "разом за кредитом: 12 345.67"
            match = re.search(r'разом за кредитом:\s*([\d\s]+\.?\d*)', text, re.IGNORECASE)

            if match:
                amount_str = match.group(1).replace(' ', '').replace('\xa0', '')
                return float(amount_str)
        except Exception:
            pass

        return None

    def parse(self, pdf) -> List[Transaction]:
        """
        Парсинг PrivatBank виписки з тексту сторінок.

        Раніше використовувалось page.extract_tables(), але pdfplumber стабільно
        втрачає останній рядок таблиці на кожній сторінці (через розрив сторінки),
        через що контрольна сума не сходилась. Розбір за текстом захоплює всі рядки.

        Кожна транзакція займає кілька текстових рядків:
            "<номер> DD.MM.YYYY <сума> <призначення...>"   <- дата і сума
            "<...> HH:MM <призначення-продовження...>"       <- час операції
        Час беремо з наступного рядка після рядка з датою.
        """
        transactions = []

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.splitlines()
            for i, line in enumerate(lines):
                match = _TXN_LINE_RE.search(line)
                if not match:
                    continue

                date_str = match.group(1)
                amount_str = match.group(2)

                # PrivatBank: доходи = позитивні суми. Негативи (витрати/комісії)
                # відсіюються validators.extract_and_validate_amount().
                amount = validators.extract_and_validate_amount(amount_str)
                if amount is None:
                    continue

                # Час операції — перший HH:MM на наступному рядку.
                time_str = None
                if i + 1 < len(lines):
                    time_match = _TIME_RE.search(lines[i + 1])
                    if time_match:
                        time_str = time_match.group(1)

                date_obj = self._build_datetime(date_str, time_str)
                if not date_obj:
                    continue

                # PrivatBank не підтримує комісію - gross = net
                transactions.append(Transaction(
                    date=date_obj,
                    gross_amount=amount,
                    commission=0.0
                ))

        return transactions

    @staticmethod
    def _build_datetime(date_str: str, time_str: Optional[str]) -> Optional[datetime]:
        """Будує datetime з дати (DD.MM.YYYY) та часу (HH:MM, опційно)."""
        try:
            if time_str:
                return datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
            return datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            return None
