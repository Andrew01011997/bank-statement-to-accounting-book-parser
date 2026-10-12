# -*- coding: utf-8 -*-
"""Bank statement parser that builds the FOP income ledger ("Книга обліку доходів")."""

from .manager import StatementParserManager
from .core.statement import Transaction

__all__ = ['StatementParserManager', 'Transaction']
