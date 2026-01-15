# -*- coding: utf-8 -*-
"""
Додатковий парсинг транзакцій безпосередньо з тексту PDF через regex
"""

import re
from typing import List, Tuple, Optional
from datetime import datetime
from . import constants


class TextTransactionParser:
    """Парсер для витягування транзакцій безпосередньо з тексту."""

    @staticmethod
    def extract_transactions_from_text(text: str) -> List[Tuple[datetime, float]]:
        """
        Витягує транзакції (дата+час, сума) з тексту.

        Args:
            text: Текст сторінки PDF

        Returns:
            Список кортежів (datetime, amount)
        """
        transactions = []
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Шукаємо дату
            date_match = re.search(constants.DATE_PATTERN, line)
            if date_match:
                date_str = date_match.group(1)

                # Шукаємо час в наступних 3 рядках
                time_str = None
                for offset in range(1, 4):
                    if i + offset < len(lines):
                        time_match = re.search(constants.TIME_PATTERN, lines[i + offset])
                        if time_match:
                            time_str = time_match.group(1)
                            break

                # Шукаємо суму в наступних 5 рядках
                amount = None
                for offset in range(0, 6):
                    if i + offset < len(lines):
                        search_line = lines[i + offset]
                        # Шукаємо позитивну суму (не з мінусом)
                        amount_pattern = r'(?<![−\-–])(\d{1,3}(?:[\s\xa0]\d{3})*\.\d{2})\s*UAH'
                        amount_match = re.search(amount_pattern, search_line)

                        if amount_match:
                            # Перевіряємо що перед сумою немає знаку мінуса
                            amount_str = amount_match.group(1)
                            pos = search_line.find(amount_str)

                            # Перевіряємо 20 символів перед знайденою сумою
                            context_before = search_line[max(0, pos-20):pos]
                            has_minus = any(sign in context_before for sign in constants.MINUS_SIGNS)

                            if not has_minus:
                                try:
                                    amount = float(amount_str.replace(' ', '').replace('\xa0', ''))
                                    break
                                except ValueError:
                                    pass

                # Якщо знайшли дату і суму - створюємо транзакцію
                if date_str and amount:
                    try:
                        if time_str:
                            dt = datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M:%S')
                        else:
                            dt = datetime.strptime(date_str, '%d.%m.%Y')

                        transactions.append((dt, amount))
                    except ValueError:
                        pass

            i += 1

        return transactions

    @staticmethod
    def deduplicate_transactions(
        table_transactions: List[Tuple[datetime, float]],
        text_transactions: List[Tuple[datetime, float]]
    ) -> List[Tuple[datetime, float]]:
        """
        Знаходить транзакції з тексту, які не знайдені в таблицях.

        Args:
            table_transactions: Транзакції з таблиць
            text_transactions: Транзакції з тексту

        Returns:
            Унікальні транзакції, які є в тексті, але відсутні в таблицях
        """
        # Створюємо set з транзакцій таблиць для швидкого пошуку
        table_set = set(table_transactions)

        # Знаходимо транзакції, яких немає в таблицях
        unique_transactions = []
        for trans in text_transactions:
            if trans not in table_set:
                unique_transactions.append(trans)

        return unique_transactions
