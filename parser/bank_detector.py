# -*- coding: utf-8 -*-
"""
Bank detection and parser creation (Factory Pattern).
"""

import pdfplumber
from .core.base_parser import BaseParser
from .parsers.monobank_parser import MonobankParser
from .parsers.privatbank_parser import PrivatBankParser
from .parsers.novapay_parser import NovaPayParser
from .parsers.generic_parser import GenericParser
from .utils import constants


UNKNOWN_BANK = 'unknown'

# Bank registry: (type, first-page keywords, parser class).
# Order matters: banks are checked in turn and the first match wins.
BANKS = (
    ('monobank', constants.MONOBANK_KEYWORDS, MonobankParser),
    ('privatbank', constants.PRIVATBANK_KEYWORDS, PrivatBankParser),
    ('novapay', constants.NOVAPAY_KEYWORDS, NovaPayParser),
)


class BankDetector:
    """Detects the bank of a statement and creates the matching parser (Factory Pattern)."""

    @staticmethod
    def detect_from_pdf(pdf) -> str:
        """
        Detects the bank from the first page text of an open PDF.

        Returns:
            'monobank' | 'privatbank' | 'novapay' | 'unknown'
        """
        try:
            first_page_text = pdf.pages[0].extract_text()
        except Exception:
            return UNKNOWN_BANK

        if first_page_text:
            text_lower = first_page_text.lower()

            for bank_type, keywords, _ in BANKS:
                if any(keyword in text_lower for keyword in keywords):
                    return bank_type

        return UNKNOWN_BANK

    @staticmethod
    def detect(pdf_path: str) -> str:
        """
        Detects the bank from a PDF file on disk.

        Returns:
            'monobank' | 'privatbank' | 'novapay' | 'unknown'
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return BankDetector.detect_from_pdf(pdf)
        except Exception:
            return UNKNOWN_BANK

    @staticmethod
    def get_parser(bank_type: str) -> BaseParser:
        """
        Returns a new parser instance for the bank type (Factory Method).
        Unknown type -> GenericParser.
        """
        for registered_type, _, parser_class in BANKS:
            if registered_type == bank_type:
                return parser_class()

        return GenericParser()
