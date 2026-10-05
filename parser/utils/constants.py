# -*- coding: utf-8 -*-
"""
Константи та конфігурація для парсера банківських виписок
"""

# Regex паттерни дат
DATE_PATTERN = r'(\d{2}\.\d{2}\.\d{4})'
DATETIME_PATTERN = r'(\d{2}\.\d{2}\.\d{4})[^\d]*(\d{2}:\d{2}:\d{2})'  # Дата і час разом
DATETIME_PATTERN_SHORT = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})'  # Дата і час без секунд (для NovaPay)

# Regex паттерни сум
AMOUNT_PATTERN = r'(\d+(?:\.\d{2})?)'
WHITESPACE_PATTERN = r'[\s\xa0 ]'

# Паттерни для еквайрингу (комісії)
GROSS_AMOUNT_PATTERN = r'Загалом\s+([\d\s]+\.?\d*)\s*грн'  # "Загалом 1000.00 грн"
COMMISSION_PATTERN = r'Комісія банку\s+([\d\s]+\.?\d*)\s*грн'  # "Комісія банку 13.00 грн"

# Паттерни контрольних сум (група 1 - сума)
MONOBANK_CONTROL_SUM_PATTERN = r'Обіг за кредитом за період:\s*([\d\s]+\.?\d*)\s*UAH'  # "...:12 345.67 UAH"
PRIVATBANK_CONTROL_SUM_PATTERN = r'разом за кредитом:\s*([\d\s]+\.?\d*)'  # "разом за кредитом: 12 345.67"
NOVAPAY_CONTROL_SUM_PATTERN = r'Обороти по кредиту:\s*([\d\s]+,\d{2})\s*грн'  # "...: 12 345,67 грн"

# PrivatBank: рядок транзакції у тексті виписки "<номер> DD.MM.YYYY <сума> <призначення...>".
# Сума — число з крапкою і 2 знаками, можливо з мінусом та пробілами-роздільниками тисяч.
PRIVATBANK_TXN_LINE_PATTERN = r'(\d{2}\.\d{2}\.\d{4})\s+([-−–]?\d[\d\s\xa0]*\.\d{2})(?!\d)'
# PrivatBank: час операції (HH:MM) — на наступному рядку після рядка з датою.
PRIVATBANK_TIME_PATTERN = r'\b(\d{2}:\d{2})\b'

# Межі сум
MIN_AMOUNT = 0.01
MAX_AMOUNT = 100000000

# Допустима різниця між контрольною сумою та сумою транзакцій (1 копійка через округлення)
CONTROL_SUM_TOLERANCE = 0.01

# Ключові слова банків
MONOBANK_KEYWORDS = ['monobank', 'універсал банк']
PRIVATBANK_KEYWORDS = ['приватбанк']
NOVAPAY_KEYWORDS = ['novapay', 'новапей', '935871']

# Знаки мінуса (різні Unicode варіанти)
MINUS_SIGNS = ['-', '−', '–']  # hyphen, minus sign U+2212, en dash U+2013

# CSV
CSV_ENCODING = 'utf-8-sig'
