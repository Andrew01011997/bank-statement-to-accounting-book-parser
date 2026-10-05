# -*- coding: utf-8 -*-
"""Підробні PDF-об'єкти з інтерфейсом pdfplumber (pages, extract_text, extract_tables)."""


class FakePage:
    def __init__(self, text=None, tables=None):
        self._text = text
        self._tables = tables or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


class FakePDF:
    def __init__(self, *pages):
        self.pages = list(pages)


def rows(transactions):
    """Транзакції -> список (дата ISO, gross, commission, net) для порівняння."""
    return [(t.date.isoformat(), t.gross_amount, t.commission, t.net_amount) for t in transactions]
