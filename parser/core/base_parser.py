# -*- coding: utf-8 -*-
"""
Abstract base class for all bank parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
import re

from .statement import Transaction
from ..utils import constants, dates, validators


class BaseParser(ABC):
    """
    Abstract base class for all bank parsers.

    Subclasses configure behaviour through class attributes:
        CONTROL_SUM_PATTERN: control-sum regex (group 1 = amount); None disables the check
        CONTROL_SUM_PAGE: index of the page with the control sum (0 = first, -1 = last)
        DECIMAL_COMMA: True if the statement uses a comma as the decimal separator
        DATE_FORMATS: date formats for _extract_date (see utils/dates.py)
    """

    CONTROL_SUM_PATTERN: Optional[str] = None
    CONTROL_SUM_PAGE: int = 0
    DECIMAL_COMMA: bool = False
    DATE_FORMATS = dates.DEFAULT_FORMATS

    def __init__(self):
        # Parsing warnings (e.g. inconsistent commission); printed by the manager
        self.warnings: List[str] = []

    @abstractmethod
    def parse(self, pdf) -> List[Transaction]:
        """Parses the statement (implemented by subclasses)."""
        pass

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Extracts the control sum (credit turnover) from the text of CONTROL_SUM_PAGE.

        Returns:
            Control sum or None
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
        Extracts a date (and time) using DATE_FORMATS.

        Returns:
            datetime or None if no date was found
        """
        return dates.extract_datetime(date_str, self.DATE_FORMATS)

    def _extract_amount(self, amount_str) -> Optional[float]:
        """
        Extracts and validates an amount (negative amounts are filtered out).

        Returns:
            float for a valid positive amount, otherwise None
        """
        if not amount_str:
            return None

        return validators.extract_and_validate_amount(str(amount_str), self.DECIMAL_COMMA)

    def _make_transaction(self, date: datetime, net_amount: float,
                          details: Optional[str] = None) -> Transaction:
        """
        Builds a transaction, taking the commission from the payment description.

        net_amount is what was credited to the account (the statement's amount column).
        If details contain a pre-commission amount and a commission that are consistent
        (gross - commission == net), gross is the pre-commission amount. Otherwise
        gross = net, and a warning is added when they are inconsistent.
        """
        gross, commission = self._extract_commission(details)

        if gross is None:
            if details and re.search(r'ком[iі]с[iі]я', str(details), re.IGNORECASE):
                self.warnings.append(
                    f"{date.strftime('%d.%m.%Y %H:%M')}: description mentions a commission in an "
                    f"unrecognised format; recorded the credited amount {net_amount:.2f}"
                )
            return Transaction(date=date, gross_amount=net_amount, net_amount=net_amount)

        if abs(gross - commission - net_amount) > constants.CONTROL_SUM_TOLERANCE:
            self.warnings.append(
                f"{date.strftime('%d.%m.%Y %H:%M')}: amount {gross:.2f} - commission {commission:.2f} "
                f"!= credited {net_amount:.2f}; commission ignored"
            )
            return Transaction(date=date, gross_amount=net_amount, net_amount=net_amount)

        return Transaction(date=date, gross_amount=gross, commission=commission, net_amount=net_amount)

    @staticmethod
    def _extract_commission(details: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Pre-commission amount and commission from the payment description.

        Formats:
            "(сума 1 234,56 грн , комiсiя - 12,34 грн.)" - payment-system transfer
            "Загалом 1000.00 грн. Комісія банку 13.00 грн." - Monobank acquiring

        Returns:
            (gross, commission) or (None, None) if there is no commission
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
