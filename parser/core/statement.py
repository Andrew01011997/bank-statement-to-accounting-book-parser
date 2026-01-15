# -*- coding: utf-8 -*-
"""
Модель даних для банківської транзакції
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    """Модель банківської транзакції."""
    date: datetime
    amount: float

    def __repr__(self):
        return f"Transaction(date={self.date.strftime('%d.%m.%Y')}, amount={self.amount:.2f})"
