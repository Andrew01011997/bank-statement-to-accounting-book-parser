# -*- coding: utf-8 -*-
"""
Constants and configuration for the bank statement parser.

Ukrainian literals below are matched against statement text and must stay as is.
"""

# Date regexes
DATE_PATTERN = r'(\d{2}\.\d{2}\.\d{4})'
DATETIME_PATTERN = r'(\d{2}\.\d{2}\.\d{4})[^\d]*(\d{2}:\d{2}:\d{2})'  # Date and time together
DATETIME_PATTERN_SHORT = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})'  # Date and time without seconds (NovaPay)

# Amount regexes
AMOUNT_PATTERN = r'(\d+(?:\.\d{2})?)'
WHITESPACE_PATTERN = r'\s'  # Unicode-aware: also matches no-break spaces (U+00A0, U+202F)

# Acquiring commission (Monobank)
GROSS_AMOUNT_PATTERN = r'Загалом\s+([\d\s]+\.?\d*)\s*грн'  # "Загалом 1000.00 грн"
COMMISSION_PATTERN = r'Комісія банку\s+([\d\s]+\.?\d*)\s*грн'  # "Комісія банку 13.00 грн"
# Payment-system transfer: "(сума 1 234,56 грн , комiсiя - 12,34 грн.)" (PrivatBank, Monobank).
# Group 1 - amount before commission, group 2 - commission. The "i" in PDFs may be Latin (U+0069);
# Monobank puts a space after the comma ("1234, 56").
TRANSFER_COMMISSION_PATTERN = (
    r'\(\s*сума\s+(\d[\d\s]*[.,]\s?\d{2})\s*грн\s*,\s*'
    r'ком[iі]с[iі]я\s*[-−–]?\s*(\d[\d\s]*[.,]\s?\d{2})\s*грн'
)

# Control-sum regexes (group 1 - amount)
MONOBANK_CONTROL_SUM_PATTERN = r'Обіг за кредитом за період:\s*([\d\s]+\.?\d*)\s*UAH'  # "...:12 345.67 UAH"
PRIVATBANK_CONTROL_SUM_PATTERN = r'разом за кредитом:\s*([\d\s]+\.?\d*)'  # "разом за кредитом: 12 345.67"
NOVAPAY_CONTROL_SUM_PATTERN = r'Обороти по кредиту:\s*([\d\s]+,\d{2})\s*грн'  # "...: 12 345,67 грн"

# PrivatBank: transaction line in the statement text "<no> DD.MM.YYYY <amount> <description...>".
# Amount: a number with a dot and 2 decimals, optionally signed, with space thousands separators.
PRIVATBANK_TXN_LINE_PATTERN = r'(\d{2}\.\d{2}\.\d{4})\s+([-−–]?\d[\d\s\xa0]*\.\d{2})(?!\d)'
# PrivatBank: transaction time (HH:MM) on the line after the date line.
PRIVATBANK_TIME_PATTERN = r'\b(\d{2}:\d{2})\b'

# Amount bounds
MIN_AMOUNT = 0.01
MAX_AMOUNT = 100000000

# Allowed difference between the control sum and the transaction total (1 kopiyka, rounding)
CONTROL_SUM_TOLERANCE = 0.01

# Bank keywords (matched against lower-cased first-page text)
MONOBANK_KEYWORDS = ['monobank', 'універсал банк']
PRIVATBANK_KEYWORDS = ['приватбанк']
NOVAPAY_KEYWORDS = ['novapay', 'новапей', '935871']

# Minus signs (Unicode variants)
MINUS_SIGNS = ['-', '−', '–']  # hyphen, minus sign U+2212, en dash U+2013

# CSV (UTF-8 with BOM so Excel detects the encoding)
CSV_ENCODING = 'utf-8-sig'
