# -*- coding: utf-8 -*-
"""Парсери для різних банків."""

from .monobank_parser import MonobankParser
from .privatbank_parser import PrivatBankParser
from .novapay_parser import NovaPayParser
from .generic_parser import GenericParser

__all__ = ['MonobankParser', 'PrivatBankParser', 'NovaPayParser', 'GenericParser']
