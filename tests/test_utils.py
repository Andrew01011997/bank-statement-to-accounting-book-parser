# -*- coding: utf-8 -*-
"""Тести утиліт: суми, дати, форматування CSV."""

import unittest
from datetime import datetime

from parser.core.statement import Transaction
from parser.utils import dates, formatters, validators


class AmountTest(unittest.TestCase):
    def test_negative_amounts_filtered(self):
        for value in ['-1200.50', '−500', '–300', '(1200)']:
            self.assertIsNone(validators.extract_and_validate_amount(value), value)

    def test_positive_amounts(self):
        self.assertEqual(validators.extract_and_validate_amount('1 200.50'), 1200.5)
        self.assertEqual(validators.extract_and_validate_amount('1\xa0234,56', decimal_comma=True), 1234.56)

    def test_out_of_bounds(self):
        self.assertIsNone(validators.extract_and_validate_amount('0.00'))

    def test_to_float(self):
        self.assertEqual(validators.to_float('12 345.67'), 12345.67)
        self.assertEqual(validators.to_float('12\xa0345,67', decimal_comma=True), 12345.67)
        with self.assertRaises(ValueError):
            validators.to_float('12\n34')


class DateTest(unittest.TestCase):
    def test_default_formats(self):
        self.assertEqual(dates.extract_datetime('05.08.2026\n07:15:01'), datetime(2026, 8, 5, 7, 15, 1))
        self.assertEqual(dates.extract_datetime('05.08.2026'), datetime(2026, 8, 5))
        self.assertIsNone(dates.extract_datetime('no date'))
        self.assertIsNone(dates.extract_datetime(None))

    def test_format_order_matters(self):
        short_first = (dates.DATETIME_SHORT, dates.DATETIME_FULL, dates.DATE_ONLY)
        self.assertEqual(dates.extract_datetime('02.07.2025 08:05:33', short_first), datetime(2025, 7, 2, 8, 5))


class CsvRowTest(unittest.TestCase):
    def test_format_csv_row(self):
        t = Transaction(date=datetime(2026, 8, 5, 7, 15, 1), gross_amount=1000.0, commission=13.0)
        self.assertEqual(formatters.format_csv_row(t), ['07:15:01', '05.08.2026', '1000,00', '13,00', '987,00'])


if __name__ == '__main__':
    unittest.main()
