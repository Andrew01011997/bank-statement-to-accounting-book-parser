# -*- coding: utf-8 -*-
"""Підробні PDF-об'єкти з інтерфейсом pdfplumber (pages, extract_text, extract_tables, extract_words, edges)."""


class FakePage:
    def __init__(self, text=None, tables=None, words=None, edges=None):
        self._text = text
        self._tables = tables or []
        self._words = words or []
        self.edges = edges or []
        self.table_settings = None  # останні налаштування, передані в extract_tables

    def extract_text(self):
        return self._text

    def extract_tables(self, table_settings=None):
        self.table_settings = table_settings
        return self._tables

    def extract_words(self):
        return self._words


class FakePDF:
    def __init__(self, *pages):
        self.pages = list(pages)


def rows(transactions):
    """Транзакції -> список (дата ISO, gross, commission, net) для порівняння."""
    return [(t.date.isoformat(), t.gross_amount, t.commission, t.net_amount) for t in transactions]


def words(*lines):
    """
    Слова pdfplumber з рядків (top, [(x0, текст), ...]).
    Ширина слова - 5 pt на символ.
    """
    return [{'text': text, 'x0': x0, 'x1': x0 + 5 * len(text), 'top': top}
            for top, items in lines for x0, text in items]


def v_edges(xs, bottom):
    """Вертикальні лінії таблиці на позиціях xs до висоти bottom."""
    return [{'orientation': 'v', 'x0': x, 'top': 50, 'bottom': bottom} for x in xs]
