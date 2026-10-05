# -*- coding: utf-8 -*-
"""
Парсер для виписок PrivatBank
"""

from typing import List, Optional
from datetime import datetime
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants


_TXN_LINE_RE = re.compile(constants.PRIVATBANK_TXN_LINE_PATTERN)
_TIME_RE = re.compile(constants.PRIVATBANK_TIME_PATTERN)


class PrivatBankParser(BaseParser):
    """Парсер для виписок PrivatBank (розбір тексту сторінок, не таблиць)."""

    CONTROL_SUM_PATTERN = constants.PRIVATBANK_CONTROL_SUM_PATTERN

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

                # Доходи = позитивні суми; негативи (витрати/комісії) відсіюються
                amount = self._extract_amount(match.group(2))
                if amount is None:
                    continue

                next_line = lines[i + 1] if i + 1 < len(lines) else ''
                time_match = _TIME_RE.search(next_line)
                time_str = time_match.group(1) if time_match else None

                date_obj = self._build_datetime(match.group(1), time_str)
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
