# -*- coding: utf-8 -*-
"""Парсер банківських виписок для створення Книги обліку доходів."""

from .manager import StatementParserManager
from .core.statement import Transaction

__all__ = ['StatementParserManager', 'Transaction']
