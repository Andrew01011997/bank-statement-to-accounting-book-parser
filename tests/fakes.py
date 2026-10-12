# -*- coding: utf-8 -*-
"""Fake PDF objects mimicking the pdfplumber interface (pages, extract_text, extract_tables, extract_words, edges)."""


class FakePage:
    def __init__(self, text=None, tables=None, words=None, edges=None):
        self._text = text
        self._tables = tables or []
        self._words = words or []
        self.edges = edges or []
        self.table_settings = None  # last settings passed to extract_tables

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
    """Transactions -> list of (ISO date, gross, commission, net) for comparison."""
    return [(t.date.isoformat(), t.gross_amount, t.commission, t.net_amount) for t in transactions]


def words(*lines):
    """
    pdfplumber words from lines (top, [(x0, text), ...]).
    Word width is 5 pt per character.
    """
    return [{'text': text, 'x0': x0, 'x1': x0 + 5 * len(text), 'top': top}
            for top, items in lines for x0, text in items]


def v_edges(xs, bottom):
    """Vertical table lines at positions xs down to bottom."""
    return [{'orientation': 'v', 'x0': x, 'top': 50, 'bottom': bottom} for x in xs]
