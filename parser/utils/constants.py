# -*- coding: utf-8 -*-
"""
Константи та конфігурація для парсера банківських виписок
"""

# Regex паттерни
DATE_PATTERN = r'(\d{2}\.\d{2}\.\d{4})'
TIME_PATTERN = r'(\d{2}:\d{2}:\d{2})'
TIME_PATTERN_SHORT = r'(\d{2}:\d{2})'  # Час без секунд (для NovaPay)
DATETIME_PATTERN = r'(\d{2}\.\d{2}\.\d{4})[^\d]*(\d{2}:\d{2}:\d{2})'  # Дата і час разом
DATETIME_PATTERN_SHORT = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})'  # Дата і час без секунд (для NovaPay)
AMOUNT_PATTERN = r'(\d+(?:\.\d{2})?)'
AMOUNT_PATTERN_COMMA = r'([\d\s]+,\d{2})'  # Сума з комою як десятковий (для NovaPay)
WHITESPACE_PATTERN = r'[\s\xa0\u00a0]'

# Межі сум
MIN_AMOUNT = 0.01
MAX_AMOUNT = 100000000

# Ключові слова банків
MONOBANK_KEYWORDS = ['monobank', 'універсал банк']
PRIVATBANK_KEYWORDS = ['приватбанк']
NOVAPAY_KEYWORDS = ['novapay', 'новапей', '935871']

# Знаки мінуса (різні Unicode варіанти)
MINUS_SIGNS = ['-', '−', '–']  # hyphen, minus sign U+2212, en dash U+2013

# CSV
CSV_ENCODING = 'utf-8-sig'
