# -*- coding: utf-8 -*-
"""
Базовий абстрактний клас для всіх парсерів банків
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import re

from .statement import Transaction
from ..utils import constants, validators


class BaseParser(ABC):
    """Абстрактний базовий клас для всіх парсерів банків."""

    def __init__(self):
        # Збереження індексів колонок між сторінками
        self.saved_date_col: Optional[int] = None
        self.saved_amount_col: Optional[int] = None

    @abstractmethod
    def parse(self, pdf) -> List[Transaction]:
        """Основний метод парсингу (реалізується в підкласах)."""
        pass

    def _extract_date(self, date_str: str) -> Optional[datetime]:
        """
        Витягує дату та час з рядка.

        Args:
            date_str: Рядок з датою (може містити час)

        Returns:
            datetime об'єкт або None якщо дату не знайдено
        """
        if not date_str:
            return None

        date_str_cleaned = str(date_str).strip()

        # Спочатку пробуємо витягти і дату, і час
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

    def _extract_amount(self, amount_str: str) -> Optional[float]:
        """
        Витягує та валідує суму.
        Використовує validators.extract_and_validate_amount() для фільтрації негативів.

        Args:
            amount_str: Рядок з сумою

        Returns:
            float якщо валідна позитивна сума, інакше None
        """
        if not amount_str:
            return None

        return validators.extract_and_validate_amount(str(amount_str))

    def _find_column_indices(self, row, keywords: dict) -> dict:
        """
        Знаходить індекси колонок за ключовими словами.

        Args:
            row: Рядок таблиці
            keywords: {'date': ['дата', 'час'], 'amount': ['сума', 'операц']}

        Returns:
            {'date': index, 'amount': index}
        """
        indices = {}

        for col_type, keyword_list in keywords.items():
            for j, cell in enumerate(row):
                if not cell:
                    continue

                cell_lower = str(cell).lower()

                # Перевіряємо чи всі ключові слова присутні
                # Для amount віддаємо перевагу колонці без "валют" (щоб уникнути "Сума у валюті рахунку")
                if all(keyword in cell_lower for keyword in keyword_list):
                    if col_type == 'amount' and 'валют' in cell_lower:
                        # Пропускаємо колонку "Сума у валюті рахунку", якщо є інша
                        if 'amount' not in indices:
                            indices[col_type] = j
                    else:
                        indices[col_type] = j
                        break  # Беремо першу знайдену (якщо це не "валют")

        return indices

    def extract_control_sum(self, pdf) -> Optional[float]:
        """
        Витягує контрольну суму з першої сторінки PDF.
        Має бути перевизначений в підкласах для конкретних банків.

        Returns:
            Контрольна сума або None
        """
        return None
