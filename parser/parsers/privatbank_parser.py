# -*- coding: utf-8 -*-
"""
PrivatBank statement parser.
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

# Tolerance (pt) for words "on the same line" and at column boundaries
_LINE_TOLERANCE = 2


class PrivatBankParser(BaseParser):
    """PrivatBank statements (parses page text, not tables)."""

    CONTROL_SUM_PATTERN = constants.PRIVATBANK_CONTROL_SUM_PATTERN

    def parse(self, pdf) -> List[Transaction]:
        """
        Parses a PrivatBank statement from page text.

        page.extract_tables() used to be used, but pdfplumber consistently drops
        the row at a page break (it ends up outside the table frame), so the
        control sum did not match. Parsing the text captures every row.

        Each transaction spans several text lines:
            "<no> DD.MM.YYYY <amount> <description...>"   <- date and amount
            "<...> HH:MM <description continued...>"       <- transaction time
        The time is taken from the line after the date line.

        The commission is looked up in "Призначення платежу" (payment description).
        In the page text this column is interleaved with its neighbours, so the
        description is collected from words within the column (see _page_descriptions).
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

                # Income = positive amounts; negatives (expenses/fees) are dropped
                amount = self._extract_amount(match.group(2))
                if amount is None:
                    continue

                next_line = lines[i + 1] if i + 1 < len(lines) else ''
                time_match = _TIME_RE.search(next_line)
                time_str = time_match.group(1) if time_match else None

                date_obj = self._build_datetime(match.group(1), time_str)
                if not date_obj:
                    continue

                # The statement amount is what was credited (net); commission comes from the description
                queue = descriptions.get((match.group(1), amount))
                details = queue.pop(0) if queue else None
                transactions.append(self._make_transaction(date_obj, amount, details))

        return transactions

    def _page_descriptions(self, page) -> Dict[Tuple[str, float], List[str]]:
        """
        Texts of the page's "Призначення платежу" column, from word coordinates.

        A transaction row starts with a date word in the date column followed by the amount.
        The description column lies between the table's vertical lines right of the amount.
        A transaction's description is the column's words from its row to the next one
        (or to the bottom of the table).

        Returns:
            {(date, amount): [descriptions top to bottom]}; {} if the layout was not found
        """
        words = page.extract_words() if hasattr(page, 'extract_words') else []
        v_edges = [e for e in getattr(page, 'edges', None) or [] if e.get('orientation') == 'v']
        if not words or not v_edges:
            return {}

        anchors = self._row_anchors(words)
        if not anchors:
            return {}

        # Transaction-table lines only: the totals block above it (page 1) has its own lines
        v_edges = [e for e in v_edges if e['bottom'] > anchors[0][0]]
        if not v_edges:
            return {}

        # Description column: from the first vertical line right of the amount to the next one
        amount_right = max(right for _, _, _, right in anchors)
        xs = []
        for x in sorted(e['x0'] for e in v_edges):
            # Table lines have thickness: two edges side by side (248.5 and 249.0) are one boundary
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
        """Words -> text: group into lines by top (with tolerance), left to right within a line."""
        lines: List[List[dict]] = []
        for w in sorted(row_words, key=lambda w: w['top']):
            if lines and abs(w['top'] - lines[-1][0]['top']) < _LINE_TOLERANCE:
                lines[-1].append(w)
            else:
                lines.append([w])
        return ' '.join(w['text'] for line in lines for w in sorted(line, key=lambda w: w['x0']))

    def _row_anchors(self, words) -> List[Tuple[float, str, Optional[float], float]]:
        """
        Transaction row starts: (top, date, amount or None for expenses, amount right edge), top to bottom.

        Takes a date word followed by an amount on the same line (as in
        PRIVATBANK_TXN_LINE_PATTERN). Dates inside descriptions are discarded: anchors
        must share one column (the most common x0).
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
            # Words that make up the amount (with thousands separators)
            amount_words = len(match.group(0).split()) - 1
            amount_right = line[amount_words]['x1']
            # Negative rows stay anchors (they bound the previous description) but carry no amount
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
        """Builds a datetime from a date (DD.MM.YYYY) and an optional time (HH:MM)."""
        try:
            if time_str:
                return datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
            return datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            return None
