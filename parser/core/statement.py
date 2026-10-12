# -*- coding: utf-8 -*-
"""
Bank transaction data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    """
    A bank transaction (income only).

    Fields:
        date: Transaction date and time
        gross_amount: Amount before commission (CSV "Сума")
        commission: Bank / payment-system commission (0 if none)
        net_amount: Amount after commission (CSV "Сума з врахуванням комісії")
    """
    date: datetime
    gross_amount: float  # Amount before commission
    commission: float = 0.0  # Commission
    net_amount: Optional[float] = field(default=None)  # Amount after commission

    def __post_init__(self):
        """Computes net_amount when it is not given."""
        if self.net_amount is None:
            self.net_amount = self.gross_amount - self.commission

    @property
    def amount(self) -> float:
        """Backward compatibility: returns gross_amount."""
        return self.gross_amount

    def __repr__(self):
        if self.commission > 0:
            return (f"Transaction(date={self.date.strftime('%d.%m.%Y')}, "
                    f"gross={self.gross_amount:.2f}, commission={self.commission:.2f}, "
                    f"net={self.net_amount:.2f})")
        return f"Transaction(date={self.date.strftime('%d.%m.%Y')}, amount={self.gross_amount:.2f})"
