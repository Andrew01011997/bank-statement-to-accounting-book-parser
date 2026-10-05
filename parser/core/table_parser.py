# -*- coding: utf-8 -*-
"""
Базовий клас для парсерів, що читають таблиці PDF з рядком заголовка (Template Method)
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from .base_parser import BaseParser
from .statement import Transaction


class TableParser(BaseParser):
    """
    Парсинг таблиць pdfplumber з визначенням колонок за заголовком.

    Індекси колонок зберігаються між таблицями та сторінками, бо на наступних
    сторінках заголовок зазвичай відсутній. Тому екземпляр парсера
    використовується лише для одного файлу.

    Підкласи реалізують:
        _is_header(row_text) - чи є рядок заголовком таблиці
        _detect_columns(row, columns) - індекси колонок із заголовка
        _build_transaction(cells) - транзакція з комірок рядка (або None)
    """

    # Колонки, без яких таблицю неможливо розібрати
    REQUIRED_COLUMNS = ('date', 'amount')

    def __init__(self):
        self._saved_columns: Dict[str, int] = {}

    def parse(self, pdf) -> List[Transaction]:
        """Парсинг усіх таблиць на всіх сторінках."""
        transactions = []

        for page in pdf.pages:
            for table in page.extract_tables():
                if table:
                    transactions.extend(self._parse_table(table))

        return transactions

    def _parse_table(self, table) -> List[Transaction]:
        """Парсинг однієї таблиці."""
        columns: Dict[str, Optional[int]] = dict(self._saved_columns)
        header_row_idx = None

        # Шукаємо заголовок
        for i, row in enumerate(table):
            if not row:
                continue

            row_text = ' '.join(str(cell).lower() if cell else '' for cell in row)

            if self._is_header(row_text):
                header_row_idx = i
                columns = self._detect_columns(row, columns)

                for name, idx in columns.items():
                    if idx is not None:
                        self._saved_columns[name] = idx

                break

        if any(columns.get(name) is None for name in self.REQUIRED_COLUMNS):
            return []

        # Парсимо дані
        start_row = header_row_idx + 1 if header_row_idx is not None else 0
        transactions = []

        for row in table[start_row:]:
            if not row:
                continue

            cells = {
                name: row[idx] if idx is not None and idx < len(row) else None
                for name, idx in columns.items()
            }

            try:
                transaction = self._build_transaction(cells)
            except (ValueError, TypeError, IndexError):
                continue

            if transaction:
                transactions.append(transaction)

        return transactions

    @abstractmethod
    def _is_header(self, row_text: str) -> bool:
        """Чи є рядок (текст комірок у нижньому регістрі) заголовком таблиці."""

    @abstractmethod
    def _detect_columns(self, row, columns: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
        """
        Визначає індекси колонок за рядком заголовка.

        Args:
            row: Рядок заголовка
            columns: Поточні (збережені) індекси колонок

        Returns:
            Індекси колонок для цієї таблиці
        """

    @abstractmethod
    def _build_transaction(self, cells: Dict[str, Optional[str]]) -> Optional[Transaction]:
        """
        Створює транзакцію з комірок рядка.

        Args:
            cells: {назва колонки: значення комірки або None}

        Returns:
            Transaction або None якщо рядок не є доходом/транзакцією
        """

    @staticmethod
    def _find_column_indices(row, keywords: dict) -> dict:
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
