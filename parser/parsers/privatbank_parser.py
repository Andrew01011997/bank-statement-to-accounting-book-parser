# -*- coding: utf-8 -*-
"""
Парсер для виписок PrivatBank
"""

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from ..core.base_parser import BaseParser
from ..core.statement import Transaction
from ..utils import constants


_TXN_LINE_RE = re.compile(constants.PRIVATBANK_TXN_LINE_PATTERN)
_TIME_RE = re.compile(constants.PRIVATBANK_TIME_PATTERN)
_DATE_WORD_RE = re.compile(r'\d{2}\.\d{2}\.\d{4}')

# Допуск (pt) для слів "на одному рядку" та на межах колонки
_LINE_TOLERANCE = 2


class PrivatBankParser(BaseParser):
    """Парсер для виписок PrivatBank (розбір тексту сторінок, не таблиць)."""

    CONTROL_SUM_PATTERN = constants.PRIVATBANK_CONTROL_SUM_PATTERN

    def parse(self, pdf) -> List[Transaction]:
        """
        Парсинг PrivatBank виписки з тексту сторінок.

        Раніше використовувалось page.extract_tables(), але pdfplumber стабільно
        губить рядок на розриві сторінки (він опиняється поза рамкою таблиці),
        через що контрольна сума не сходилась. Розбір за текстом захоплює всі рядки.

        Кожна транзакція займає кілька текстових рядків:
            "<номер> DD.MM.YYYY <сума> <призначення...>"   <- дата і сума
            "<...> HH:MM <призначення-продовження...>"       <- час операції
        Час беремо з наступного рядка після рядка з датою.

        Комісію шукаємо в "Призначенні платежу". У тексті сторінки ця колонка
        перемішана з сусідніми, тому опис збираємо зі слів у межах колонки
        (див. _page_descriptions).
        """
        transactions = []

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            descriptions = self._page_descriptions(page)
            lines = text.splitlines()
            for i, line in enumerate(lines):
                match = _TXN_LINE_RE.search(line)
                if not match:
                    continue

                # Доходи = позитивні суми; негативи (витрати/комісії) відсіюються
                amount = self._extract_amount(match.group(2))
                if amount is None:
                    continue

                next_line = lines[i + 1] if i + 1 < len(lines) else ''
                time_match = _TIME_RE.search(next_line)
                time_str = time_match.group(1) if time_match else None

                date_obj = self._build_datetime(match.group(1), time_str)
                if not date_obj:
                    continue

                # Сума у виписці - зараховано (net); комісія - з призначення платежу
                queue = descriptions.get((match.group(1), amount))
                details = queue.pop(0) if queue else None
                transactions.append(self._make_transaction(date_obj, amount, details))

        return transactions

    def _page_descriptions(self, page) -> Dict[Tuple[str, float], List[str]]:
        """
        Тексти колонки "Призначення платежу" сторінки за координатами слів.

        Рядок транзакції починається словом-датою в колонці дати, за яким іде сума.
        Колонка опису - між вертикальними лініями таблиці праворуч від суми.
        Опис транзакції - слова колонки від її рядка до наступного (або до низу таблиці).

        Returns:
            {(дата, сума): [описи у порядку зверху вниз]}; {} якщо розмітку не знайдено
        """
        words = page.extract_words() if hasattr(page, 'extract_words') else []
        v_edges = [e for e in getattr(page, 'edges', None) or [] if e.get('orientation') == 'v']
        if not words or not v_edges:
            return {}

        anchors = self._row_anchors(words)
        if not anchors:
            return {}

        # Лише лінії таблиці транзакцій: блок підсумків над нею (1-а сторінка) має свої лінії
        v_edges = [e for e in v_edges if e['bottom'] > anchors[0][0]]
        if not v_edges:
            return {}

        # Колонка опису: від першої вертикальної лінії праворуч від суми до наступної
        amount_right = max(right for _, _, _, right in anchors)
        xs = []
        for x in sorted(e['x0'] for e in v_edges):
            # Лінія таблиці має товщину: дві грані поруч (248.5 і 249.0) - одна межа
            if not xs or x - xs[-1] > _LINE_TOLERANCE:
                xs.append(x)
        right_of_amount = [x for x in xs if x >= amount_right - _LINE_TOLERANCE]
        if len(right_of_amount) < 2:
            return {}
        col_x0, col_x1 = right_of_amount[0], right_of_amount[1]
        table_bottom = max(e['bottom'] for e in v_edges)

        result: Dict[Tuple[str, float], List[str]] = defaultdict(list)
        for k, (top, date_str, amount, _) in enumerate(anchors):
            bottom = anchors[k + 1][0] if k + 1 < len(anchors) else table_bottom
            row_words = [w for w in words
                         if top - _LINE_TOLERANCE <= w['top'] < bottom - _LINE_TOLERANCE
                         and w['x0'] >= col_x0 - _LINE_TOLERANCE and w['x1'] <= col_x1 + _LINE_TOLERANCE]
            if amount is not None:
                result[(date_str, amount)].append(self._join_lines(row_words))

        return result

    @staticmethod
    def _join_lines(row_words) -> str:
        """Слова -> текст: групуємо в рядки за top (з допуском), у рядку - зліва направо."""
        lines: List[List[dict]] = []
        for w in sorted(row_words, key=lambda w: w['top']):
            if lines and abs(w['top'] - lines[-1][0]['top']) < _LINE_TOLERANCE:
                lines[-1].append(w)
            else:
                lines.append([w])
        return ' '.join(w['text'] for line in lines for w in sorted(line, key=lambda w: w['x0']))

    def _row_anchors(self, words) -> List[Tuple[float, str, Optional[float], float]]:
        """
        Початки рядків транзакцій: (top, дата, сума або None для витрат, права межа суми), зверху вниз.

        Береться слово-дата, за яким на тому ж рядку стоїть сума (як у
        PRIVATBANK_TXN_LINE_PATTERN). Дати з опису відкидаються: якорі мають бути
        в одній колонці (найчастіший x0).
        """
        candidates = []
        for w in words:
            if not _DATE_WORD_RE.fullmatch(w['text']):
                continue
            line = sorted((o for o in words
                           if abs(o['top'] - w['top']) < _LINE_TOLERANCE and o['x0'] >= w['x0']),
                          key=lambda o: o['x0'])
            line_text = ' '.join(o['text'] for o in line)
            match = _TXN_LINE_RE.match(line_text)
            if not match:
                continue
            # Слова, з яких складається сума (з роздільниками тисяч)
            amount_words = len(match.group(0).split()) - 1
            amount_right = line[amount_words]['x1']
            # Від'ємні рядки лишаються якорями (межа попереднього опису), але без суми
            amount = self._extract_amount(match.group(2))
            candidates.append((w['top'], round(w['x0']), match.group(1), amount, amount_right))

        if not candidates:
            return []

        column_x = Counter(c[1] for c in candidates).most_common(1)[0][0]
        anchors = [(top, date_str, amount, right) for top, x, date_str, amount, right in candidates
                   if abs(x - column_x) <= _LINE_TOLERANCE]
        return sorted(anchors)

    @staticmethod
    def _build_datetime(date_str: str, time_str: Optional[str]) -> Optional[datetime]:
        """Будує datetime з дати (DD.MM.YYYY) та часу (HH:MM, опційно)."""
        try:
            if time_str:
                return datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
            return datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            return None
