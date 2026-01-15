# -*- coding: utf-8 -*-
"""
Визначення типу банку та створення відповідного парсера (Factory Pattern)
"""

import pdfplumber
from .core.base_parser import BaseParser
from .parsers.monobank_parser import MonobankParser
from .parsers.privatbank_parser import PrivatBankParser
from .parsers.generic_parser import GenericParser
from .utils import constants


class BankDetector:
    """Визначення типу банку та створення відповідного парсера (Factory Pattern)."""

    @staticmethod
    def detect(pdf_path: str) -> str:
        """
        Визначає тип банку за вмістом PDF.

        Args:
            pdf_path: Шлях до PDF файлу

        Returns:
            'monobank' | 'privatbank' | 'unknown'
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page_text = pdf.pages[0].extract_text()

                if first_page_text:
                    text_lower = first_page_text.lower()

                    # Перевіряємо Monobank
                    if any(keyword in text_lower for keyword in constants.MONOBANK_KEYWORDS):
                        return 'monobank'

                    # Перевіряємо PrivatBank
                    if any(keyword in text_lower for keyword in constants.PRIVATBANK_KEYWORDS):
                        return 'privatbank'

        except Exception:
            pass

        return 'unknown'

    @staticmethod
    def get_parser(bank_type: str) -> BaseParser:
        """
        Повертає відповідний парсер на основі типу банку (Factory Method).

        Args:
            bank_type: 'monobank' | 'privatbank' | 'unknown'

        Returns:
            Екземпляр відповідного парсера
        """
        parsers = {
            'monobank': MonobankParser,
            'privatbank': PrivatBankParser,
            'unknown': GenericParser
        }

        parser_class = parsers.get(bank_type, GenericParser)
        return parser_class()
