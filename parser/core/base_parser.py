# -*- coding: utf-8 -*-
"""
Базовий абстрактний клас для всіх парсерів банків
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
import re

from .statement import Transaction
from ..utils import constants, dates, validators


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

    def __init__(self):
        # Попередження розбору (напр. неузгоджена комісія); виводить менеджер
        self.warnings: List[str] = []

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

    def _make_transaction(self, date: datetime, net_amount: float,
                          details: Optional[str] = None) -> Transaction:
        """
        Транзакція з урахуванням комісії з призначення платежу.

        net_amount - сума, що надійшла на рахунок (колонка суми виписки).
        Якщо в details знайдено суму до комісії та комісію, і вони узгоджені
        (gross - commission == net), то gross = сума до комісії. Інакше gross = net,
        а при неузгодженості додається попередження.
        """
        gross, commission = self._extract_commission(details)

        if gross is None:
            if details and re.search(r'ком[iі]с[iі]я', str(details), re.IGNORECASE):
                self.warnings.append(
                    f"{date.strftime('%d.%m.%Y %H:%M')}: в описі є комісія, але формат не розпізнано; "
                    f"записано зараховану суму {net_amount:.2f}"
                )
            return Transaction(date=date, gross_amount=net_amount, net_amount=net_amount)

        if abs(gross - commission - net_amount) > constants.CONTROL_SUM_TOLERANCE:
            self.warnings.append(
                f"{date.strftime('%d.%m.%Y %H:%M')}: сума {gross:.2f} - комісія {commission:.2f} "
                f"!= зараховано {net_amount:.2f}; комісію не враховано"
            )
            return Transaction(date=date, gross_amount=net_amount, net_amount=net_amount)

        return Transaction(date=date, gross_amount=gross, commission=commission, net_amount=net_amount)

    @staticmethod
    def _extract_commission(details: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Сума до комісії та комісія з призначення платежу.

        Формати:
            "(сума 1 234,56 грн , комiсiя - 9,99 грн.)" - переказ від платіжної системи
            "Загалом 4000.00 грн. Комісія банку 52.00 грн." - еквайринг Monobank

        Returns:
            (gross, commission) або (None, None), якщо комісії немає
        """
        if not details:
            return None, None

        text = ' '.join(str(details).split())
        try:
            match = re.search(constants.TRANSFER_COMMISSION_PATTERN, text, re.IGNORECASE)
            if match:
                return (validators.to_float(match.group(1), decimal_comma=True),
                        validators.to_float(match.group(2), decimal_comma=True))

            gross = re.search(constants.GROSS_AMOUNT_PATTERN, text, re.IGNORECASE)
            commission = re.search(constants.COMMISSION_PATTERN, text, re.IGNORECASE)
            if gross and commission:
                return validators.to_float(gross.group(1)), validators.to_float(commission.group(1))
        except ValueError:
            pass

        return None, None
