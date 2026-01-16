# -*- coding: utf-8 -*-
"""
Модель даних для банківської транзакції
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    """
    Модель банківської транзакції.

    Поля:
        date: Дата та час транзакції
        gross_amount: Повна сума до вирахування комісії (Сума)
        commission: Комісія банку (0 якщо немає)
        net_amount: Сума після вирахування комісії (Сума з врахуванням комісії)
    """
    date: datetime
    gross_amount: float  # Сума (до комісії)
    commission: float = 0.0  # Комісія
    net_amount: Optional[float] = field(default=None)  # Сума з врахуванням комісії

    def __post_init__(self):
        """Обчислює net_amount якщо не вказано."""
        if self.net_amount is None:
            self.net_amount = self.gross_amount - self.commission

    @property
    def amount(self) -> float:
        """Зворотна сумісність - повертає gross_amount."""
        return self.gross_amount

    def __repr__(self):
        if self.commission > 0:
            return (f"Transaction(date={self.date.strftime('%d.%m.%Y')}, "
                    f"gross={self.gross_amount:.2f}, commission={self.commission:.2f}, "
                    f"net={self.net_amount:.2f})")
        return f"Transaction(date={self.date.strftime('%d.%m.%Y')}, amount={self.gross_amount:.2f})"
