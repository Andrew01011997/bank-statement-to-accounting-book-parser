# -*- coding: utf-8 -*-
"""
Визначення типу банку та створення відповідного парсера (Factory Pattern)
"""

import pdfplumber
from .core.base_parser import BaseParser
from .parsers.monobank_parser import MonobankParser
from .parsers.privatbank_parser import PrivatBankParser
from .parsers.novapay_parser import NovaPayParser
from .parsers.generic_parser import GenericParser
from .utils import constants


UNKNOWN_BANK = 'unknown'

# Реєстр банків: (тип, ключові слова на першій сторінці, клас парсера).
# Порядок має значення - перевіряється по черзі, перший збіг перемагає.
BANKS = (
    ('monobank', constants.MONOBANK_KEYWORDS, MonobankParser),
    ('privatbank', constants.PRIVATBANK_KEYWORDS, PrivatBankParser),
    ('novapay', constants.NOVAPAY_KEYWORDS, NovaPayParser),
)


class BankDetector:
    """Визначення типу банку та створення відповідного парсера (Factory Pattern)."""

    @staticmethod
    def detect_from_pdf(pdf) -> str:
        """
        Визначає тип банку за текстом першої сторінки відкритого PDF.

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
        Визначає тип банку за вмістом PDF файлу.

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
        Повертає новий екземпляр парсера для типу банку (Factory Method).
        Невідомий тип -> GenericParser.
        """
        for registered_type, _, parser_class in BANKS:
            if registered_type == bank_type:
                return parser_class()

        return GenericParser()
