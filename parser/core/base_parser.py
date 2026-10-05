# -*- coding: utf-8 -*-
"""
Базовий абстрактний клас для всіх парсерів банків
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import re

from .statement import Transaction
from ..utils import dates, validators


class BaseParser(ABC):
    """
    Абстрактний базовий клас для всіх парсерів банків.

    Підкласи налаштовують поведінку через атрибути класу:
        CONTROL_SUM_PATTERN: regex контрольної суми (група 1 - сума), None - без перевірки
        CONTROL_SUM_PAGE: індекс сторінки з контрольною сумою (0 - перша, -1 - остання)
        DECIMAL_COMMA: True якщо у виписці кома - десятковий розділювач
        DATE_FORMATS: формати дат для _extract_date (див. utils/dates.py)
    """

    CONTROL_SUM_PATTERN: Optional[str] = None
    CONTROL_SUM_PAGE: int = 0
    DECIMAL_COMMA: bool = False
    DATE_FORMATS = dates.DEFAULT_FORMATS

    @abstractmethod
    def parse(self, pdf) -> List[Transaction]:
        """Основний метод парсингу (реалізується в підкласах)."""
        pass

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму (обіг за кредитом) з тексту сторінки CONTROL_SUM_PAGE.

        Returns:
            Контрольна сума або None
        """
        if not self.CONTROL_SUM_PATTERN:
            return None

        try:
            text = pdf.pages[self.CONTROL_SUM_PAGE].extract_text()
            match = re.search(self.CONTROL_SUM_PATTERN, text, re.IGNORECASE)

            if match:
                return validators.to_float(match.group(1), self.DECIMAL_COMMA)
        except Exception:
            pass

        return None

    def _extract_date(self, date_str) -> Optional[datetime]:
        """
        Витягує дату та час з рядка у форматах DATE_FORMATS.

        Returns:
            datetime об'єкт або None якщо дату не знайдено
        """
        return dates.extract_datetime(date_str, self.DATE_FORMATS)

    def _extract_amount(self, amount_str) -> Optional[float]:
        """
        Витягує та валідує суму (негативні суми відфільтровуються).

        Returns:
            float якщо валідна позитивна сума, інакше None
        """
        if not amount_str:
            return None

        return validators.extract_and_validate_amount(str(amount_str), self.DECIMAL_COMMA)
