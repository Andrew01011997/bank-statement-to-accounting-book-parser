# -*- coding: utf-8 -*-
"""Тести парсерів банків на синтетичних сторінках."""

import unittest

from parser.bank_detector import BankDetector
from parser.parsers import MonobankParser, PrivatBankParser, NovaPayParser, GenericParser
from tests.fakes import FakePage, FakePDF, rows, words, v_edges


MONO_HEADER = ['Дата i час операції', 'Деталі операції', 'MCC', 'Сума у валюті операції',
               'Сума операції', 'Валюта']


class MonobankParserTest(unittest.TestCase):
    def setUp(self):
        self.pdf = FakePDF(
            FakePage('Виписка monobank\nОбіг за кредитом за період:5 200.50 UAH\n', [[
                MONO_HEADER,
                ['05.08.2026\n07:15:01', 'Еквайринг, MQ1, Загалом 1000.00 грн. Комісія банку 13.00 грн.',
                 '', '987.00', '987.00', 'UAH'],
                ['05.08.2026 09:16:02', 'Переказ', '', '1 200.50', '1 200.50', 'UAH'],
                ['05.08.2026 10:00:00', 'Покупка', '', '-100.00', '−100.00', 'UAH'],
                [None] * 6,
                ['06.08.2026', 'Короткий'],
                ['bad date', 'x', '', '10.00', '10.00', 'UAH'],
            ]]),
            # Таблиця без заголовка - колонки з попередньої сторінки
            FakePage('page 2', [[
                ['08.08.2026 13:00:00', 'Без заголовка', '', '52.00', '52.00', 'UAH'],
            ]]),
        )

    def test_parse(self):
        self.assertEqual(rows(MonobankParser().parse(self.pdf)), [
            ('2026-08-05T07:15:01', 1000.0, 13.0, 987.0),
            ('2026-08-05T09:16:02', 1200.5, 0.0, 1200.5),
            ('2026-08-08T13:00:00', 52.0, 0.0, 52.0),
        ])

    def test_control_sum(self):
        self.assertEqual(MonobankParser().extract_control_sum(self.pdf), 5200.5)

    def test_transfer_commission(self):
        # Переказ від платіжної системи: пробіл після коми, перенос рядків у комірці
        pdf = FakePDF(FakePage('monobank', [[
            MONO_HEADER,
            ['05.08.2026 07:15:01', 'Переказ коштів за 04.08.2026 згідно договору на\n'
             'переказ № ВП-1 від 01.01.26 (сума 1234, 56 грн, комісія -\n12, 34 грн.), без ПДВ',
             '', '1 222.22', '1 222.22', 'UAH'],
            # Неузгоджено: 600 - 50 != 500 -> комісію не враховано, попередження
            ['06.08.2026 08:00:00', '(сума 600,00 грн, комісія - 50,00 грн.)', '', '500.00', '500.00', 'UAH'],
            # Комісія згадана, але формат невідомий -> попередження
            ['07.08.2026 09:00:00', 'Переказ, комісія 5 грн', '', '95.00', '95.00', 'UAH'],
        ]]))
        parser = MonobankParser()

        self.assertEqual(rows(parser.parse(pdf)), [
            ('2026-08-05T07:15:01', 1234.56, 12.34, 1222.22),
            ('2026-08-06T08:00:00', 500.0, 0.0, 500.0),
            ('2026-08-07T09:00:00', 95.0, 0.0, 95.0),
        ])
        self.assertEqual(len(parser.warnings), 2)


class TableParserTest(unittest.TestCase):
    def test_table_closed_at_bottom_of_column_lines(self):
        # Таблиця без нижньої межі (розрив сторінки): лінія по низу вертикальних ліній
        page = FakePage('monobank', edges=v_edges([10, 90], 500) + v_edges([200], 816)
                        + [{'orientation': 'h', 'x0': 10, 'top': 900, 'bottom': 900}])
        MonobankParser().parse(FakePDF(page))
        self.assertEqual(page.table_settings, {'explicit_horizontal_lines': [816]})

    def test_no_edges_default_settings(self):
        page = FakePage('monobank')
        MonobankParser().parse(FakePDF(page))
        self.assertIsNone(page.table_settings)


class NovaPayParserTest(unittest.TestCase):
    def setUp(self):
        self.pdf = FakePDF(
            FakePage('NovaPay виписка', [[
                ['№', 'Дата/час операції', 'Сума, UAH', 'Призначення платежу'],
                ['1', '01.07.2025 10:30', '1 234,56', 'Оплата'],
                ['2', '01.07.2025 11:00', '-5 000,00', 'Списання'],
                ['3', '28.07.2025', '15,5', 'Без часу'],
                ['4', '', '10,00', 'Без дати'],
            ]]),
            FakePage('Обороти по кредиту: 1 250,06 грн', [[
                ['5', '31.07.2025 11:11', '15,50', 'Продовження'],
            ]]),
        )

    def test_parse(self):
        self.assertEqual(rows(NovaPayParser().parse(self.pdf)), [
            ('2025-07-01T10:30:00', 1234.56, 0.0, 1234.56),
            ('2025-07-28T00:00:00', 15.0, 0.0, 15.0),
            ('2025-07-31T11:11:00', 15.5, 0.0, 15.5),
        ])

    def test_control_sum_from_last_page(self):
        self.assertAlmostEqual(NovaPayParser().extract_control_sum(self.pdf), 1250.06)


class PrivatBankParserTest(unittest.TestCase):
    def setUp(self):
        self.pdf = FakePDF(
            FakePage(
                'АТ КБ ПРИВАТБАНК\nразом за кредитом: 2 500.00\n'
                '1 05.08.2026 2 000.00 Оплата від клієнта\n'
                'ФОП 07:15 продовження\n'
                '2 05.08.2026 -1 500.00 Переказ на картку\n'
                '10:00\n'
                '3 06.08.2026 500.00 Без часу\n'
            ),
            FakePage(None),
        )

    def test_parse(self):
        self.assertEqual(rows(PrivatBankParser().parse(self.pdf)), [
            ('2026-08-05T07:15:00', 2000.0, 0.0, 2000.0),
            ('2026-08-06T00:00:00', 500.0, 0.0, 500.0),
        ])

    def test_control_sum(self):
        self.assertEqual(PrivatBankParser().extract_control_sum(self.pdf), 2500.0)

    def test_commission_from_description_column(self):
        # Колонки: номер | дата | сума | призначення (249..403) | платник.
        # У тексті сторінки колонки перемішані (ЄДРПОУ платника між "(сума" і числом),
        # тому опис береться зі слів у межах колонки. "i" - латинська, як у PDF.
        text = ('1 05.08.2026 990.00 Переказ коштiв ТОВ\n'
                '07:15 (сума 12345678\n'
                '1 000,00 грн ,\n'
                'комiсiя - 10,00 грн.)\n'
                '2 05.08.2026 -1 500.00 Комiсiя за обслуговування\n'
                '10:00\n'
                '3 06.08.2026 500.00 Переказ (сума 600,00 грн , комiсiя - 50,00 грн.)\n'
                '4 06.08.2026 70.00 Оплата\n')
        page_words = words(
            (100, [(90, '1'), (135, '05.08.2026'), (185, '990.00'), (255, 'Переказ'), (300, 'коштiв'), (410, 'ТОВ')]),
            (110, [(135, '07:15'), (255, '(сума'), (410, '12345678')]),
            (120, [(255, '1'), (265, '000,00'), (300, 'грн'), (320, ',')]),
            (130, [(255, 'комiсiя'), (300, '-'), (310, '10,00'), (340, 'грн.)')]),
            (150, [(90, '2'), (135, '05.08.2026'), (185, '-22'), (200, '000.00'), (255, 'Комiсiя'), (300, 'за')]),
            (160, [(135, '10:00')]),
            (170, [(90, '3'), (135, '06.08.2026'), (185, '500.00'), (255, '(сума')]),
            (178, [(255, '600,00'), (290, 'грн'), (305, ','), (310, 'комiсiя'), (350, '-'), (355, '50,00')]),
            (186, [(255, 'грн.)')]),
            (200, [(90, '4'), (135, '06.08.2026'), (185, '70.00'), (255, 'Оплата')]),
            (210, [(255, '05.08.2026'), (310, '1.00')]),  # дата і число в описі - не початок рядка
        )
        # Лінії таблиці подвійні (дві грані поруч), як у реальному PDF
        edges = v_edges([85, 133, 181, 248.5, 249, 402.6, 403.1, 470], 300)
        # Блок підсумків над таблицею (1-а сторінка) зі своєю лінією всередині колонки опису
        edges += v_edges([302], 80)
        parser = PrivatBankParser()

        result = parser.parse(FakePDF(FakePage(text, words=page_words, edges=edges)))

        self.assertEqual(rows(result), [
            ('2026-08-05T07:15:00', 1000.0, 10.0, 990.0),
            ('2026-08-06T00:00:00', 500.0, 0.0, 500.0),  # 600 - 50 != 500
            ('2026-08-06T00:00:00', 70.0, 0.0, 70.0),
        ])
        self.assertEqual(len(parser.warnings), 1)


class GenericParserTest(unittest.TestCase):
    def test_no_control_sum(self):
        self.assertIsNone(GenericParser().extract_control_sum(FakePDF(FakePage('x'))))

    @unittest.expectedFailure
    def test_amount_not_taken_from_date_cell(self):
        # Відома проблема: AMOUNT_PATTERN знаходить "15.01" у даті "15.01.2024"
        pdf = FakePDF(FakePage('x', [[['15.01.2024 12:30:45', '100.00']]]))
        self.assertEqual(rows(GenericParser().parse(pdf)), [('2024-01-15T12:30:45', 100.0, 0.0, 100.0)])


class BankDetectorTest(unittest.TestCase):
    def test_detect(self):
        cases = {
            'Виписка Monobank / Універсал Банк': 'monobank',
            'АТ КБ ПРИВАТБАНК': 'privatbank',
            'NovaPay': 'novapay',
            'Інший банк': 'unknown',
        }
        for text, expected in cases.items():
            self.assertEqual(BankDetector.detect_from_pdf(FakePDF(FakePage(text))), expected)

    def test_detect_empty_page(self):
        self.assertEqual(BankDetector.detect_from_pdf(FakePDF(FakePage(None))), 'unknown')

    def test_get_parser_returns_fresh_instances(self):
        self.assertIsInstance(BankDetector.get_parser('novapay'), NovaPayParser)
        self.assertIsInstance(BankDetector.get_parser('unknown'), GenericParser)
        self.assertIsNot(BankDetector.get_parser('monobank'), BankDetector.get_parser('monobank'))


if __name__ == '__main__':
    unittest.main()
