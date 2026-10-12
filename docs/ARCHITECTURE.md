# Architecture

🇺🇦 [Українська версія](ARCHITECTURE.uk.md)

Technical reference for the bank statement parser that builds the FOP income ledger ("Книга обліку доходів").

## Contents

1. [Overview](#overview)
2. [Project layout](#project-layout)
3. [Modules](#modules)
4. [Data flow](#data-flow)
5. [Design decisions](#design-decisions)
6. [Adding a bank](#adding-a-bank)
7. [Testing](#testing)

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          main.py                            │
│                       (entry point)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  StatementParserManager                     │
│                      (manager.py)                           │
│                                                             │
│  • Finds PDFs in input/, opens each one once                │
│  • BankDetector → Parser → control-sum check → CSV          │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ BankDetector│   │  PDFReader  │   │  CSVWriter  │
│ (registry + │   │    (I/O)    │   │    (I/O)    │
│   Factory)  │   └─────────────┘   └─────────────┘
└──────┬──────┘
       │
       ▼ (creates)
┌─────────────────────────────────────────────────────────────┐
│ BaseParser (ABC) — control sum, dates, amounts, commission  │
│  ├── TableParser (ABC) — tables with a header row           │
│  │    ├── MonobankParser                                    │
│  │    └── NovaPayParser                                     │
│  ├── PrivatBankParser — parses page text                    │
│  └── GenericParser — fallback                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Project layout

```
bank-statement-to-accounting-book-parser/
├── main.py                 # Entry point
├── run.sh / run.bat        # Launchers (install deps, run main.py)
├── requirements.txt        # Runtime dependency (pdfplumber)
├── requirements-dev.txt    # + ruff
├── pyproject.toml          # Tool configuration (ruff)
├── input/                  # Input PDF statements (git-ignored)
├── output/                 # Output CSV files (git-ignored)
├── docs/                   # Architecture, known issues
├── tests/                  # Unit tests (unittest, synthetic pages)
│
└── parser/                 # Main package
    ├── __init__.py         # Public API
    ├── manager.py          # Orchestration
    ├── bank_detector.py    # Bank registry + parser Factory
    │
    ├── core/               # Base classes
    │   ├── base_parser.py  # Abstract parser
    │   ├── table_parser.py # Template for table parsers
    │   └── statement.py    # Transaction model
    │
    ├── parsers/            # Concrete parsers
    │   ├── monobank_parser.py
    │   ├── privatbank_parser.py
    │   ├── novapay_parser.py
    │   └── generic_parser.py
    │
    ├── io/                 # File I/O
    │   ├── pdf_reader.py   # pdfplumber wrapper
    │   └── csv_writer.py   # CSV generation
    │
    └── utils/              # Helpers
        ├── constants.py    # Regexes, keywords, limits
        ├── validators.py   # Amount parsing and validation
        ├── dates.py        # Date parsing
        └── formatters.py   # Date/amount formatting for CSV
```

---

## Modules

### `parser/manager.py`

**Class:** `StatementParserManager`

| Method | Description |
|--------|-------------|
| `__init__(input_dir, output_dir)` | Sets the input/output folders |
| `run()` | Parses every PDF in the input folder (case-insensitive `.pdf`, sorted; a second file that would write the same CSV is skipped). Returns `False` if the input folder is unusable or any file failed; `main.py` turns that into exit code 1 |
| `process_file(pdf_file)` | Processes one PDF; `False` on an error or when no transactions were found |
| `_report_control_sum(transactions, control_sum)` | Reports the control-sum match and commission totals |
| `_write_csv(pdf_file, transactions)` | Writes a CSV named after the PDF |

**`process_file()` algorithm:**
1. Opens the PDF via `PDFReader.open()` (once)
2. Detects the bank via `BankDetector.detect_from_pdf(pdf)`
3. Gets a fresh parser via `BankDetector.get_parser()`
4. `parser.parse(pdf)` and `parser.extract_control_sum(pdf)`
5. Prints parser warnings (`parser.warnings`, e.g. an inconsistent commission)
6. Compares the control sum with the sum of `net_amount` (credited amounts; tolerance `CONTROL_SUM_TOLERANCE` = 0.01). A mismatch is a warning only; the CSV is written regardless
7. Writes the CSV via `CSVWriter.write()`

An error in one file is printed with a traceback; the remaining files are still processed.

---

### `parser/bank_detector.py`

**`BANKS` registry:** tuples `(type, keywords, parser class)`. Checked in order (Monobank → PrivatBank → NovaPay); the first match wins.

| Method | Description |
|--------|-------------|
| `detect_from_pdf(pdf) -> str` | Bank type from the first page text of an open PDF |
| `detect(pdf_path) -> str` | Same, but opens the file itself |
| `get_parser(bank_type) -> BaseParser` | New parser instance; unknown type → `GenericParser` |

Keywords (`constants.py`):
- `monobank`, `універсал банк` → MonobankParser
- `приватбанк` → PrivatBankParser
- `novapay`, `новапей`, `935871` → NovaPayParser
- anything else → GenericParser

See [known issue #2](KNOWN_ISSUES.md#2-bank-is-detected-from-any-match-on-the-first-page-counterparties-included) about false matches.

---

### `parser/core/statement.py`

**Class:** `Transaction` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `date` | `datetime` | Transaction date and time |
| `gross_amount` | `float` | Amount before commission |
| `commission` | `float` | Commission (0 by default) |
| `net_amount` | `float` | Amount after commission (defaults to `gross - commission`) |

`amount` is a backward-compatible property returning `gross_amount`.

---

### `parser/core/base_parser.py`

**Class:** `BaseParser` (ABC), configured by class attributes:

| Attribute | Default | Description |
|-----------|---------|-------------|
| `CONTROL_SUM_PATTERN` | `None` | Control-sum regex (group 1); `None` disables the check |
| `CONTROL_SUM_PAGE` | `0` | Page with the control sum (`-1` = last) |
| `DECIMAL_COMMA` | `False` | Comma as the decimal separator |
| `DATE_FORMATS` | `dates.DEFAULT_FORMATS` | Date formats, tried in order |

| Method | Description |
|--------|-------------|
| `parse(pdf)` | Abstract |
| `extract_control_sum(pdf)` | Searches `CONTROL_SUM_PATTERN` on `CONTROL_SUM_PAGE` |
| `_extract_date(value)` | `dates.extract_datetime(value, DATE_FORMATS)` |
| `_extract_amount(value)` | `validators.extract_and_validate_amount(value, DECIMAL_COMMA)` — **filters out negative amounts** |
| `_make_transaction(date, net, details)` | Builds a `Transaction`, taking gross/commission from the description when consistent |

**Commission handling (`_make_transaction`).** The statement amount is what was credited (net). The description may contain the pre-commission amount and the commission:
- payment-system transfer: `(сума X грн, комісія - Y грн)` — `TRANSFER_COMMISSION_PATTERN` (PrivatBank, Monobank)
- Monobank acquiring: `Загалом X грн. Комісія банку Y грн.` — `GROSS_AMOUNT_PATTERN` / `COMMISSION_PATTERN`

They are accepted only if `X − Y == net` (±0.01); otherwise `gross = net` and a warning is added. A warning is also added when the description mentions a commission in an unrecognised format. PDFs may use the Latin `i` inside Ukrainian words; the patterns allow for it.

---

### `parser/core/table_parser.py`

**Class:** `TableParser(BaseParser)` — Template Method for tables with a header row.

`parse()` walks every table on every page. For each table:
1. Finds the first row where `_is_header(row_text)` is true
2. `_detect_columns(row, columns)` returns column indices; found ones are saved in `_saved_columns`
3. Tables without a header (later pages) reuse the saved indices and are parsed from the first row
4. If any of `REQUIRED_COLUMNS` (`date`, `amount`) is missing, the table is skipped
5. `_build_transaction(cells)` returns a `Transaction` or `None` for each row

Because of the saved columns, a parser instance serves one file only (`get_parser` always creates a new one).

`_extract_tables(page)` adds an explicit horizontal line at the bottom of the vertical edges, so a row cut by a page break (no bottom border) is not dropped.

`_find_column_indices(row, keywords)` finds columns by keywords; for `amount`, columns containing "валют" have lower priority.

---

### `parser/parsers/privatbank_parser.py`

**Class:** `PrivatBankParser(BaseParser)`

- Parses page **text**, not tables: `pdfplumber.extract_tables()` lost rows at page breaks (the row above the table frame)
- Transaction line: `<no> DD.MM.YYYY <amount> <description>` (`PRIVATBANK_TXN_LINE_PATTERN`)
- Time `HH:MM` comes from the next line (`PRIVATBANK_TIME_PATTERN`)
- Control sum: `разом за кредитом: XXX` (first page)
- **Payment-system commission:** the "Призначення платежу" column is rebuilt from `extract_words()` between the table's vertical lines right of the amount (`_page_descriptions`), because `extract_text()` interleaves columns. A transaction row starts with a date word followed by an amount (`_row_anchors`). Then `_make_transaction` applies

---

### `parser/parsers/monobank_parser.py`

**Class:** `MonobankParser(TableParser)`

- Header: a row with `дата`, `сума`, `операц`
- Columns: `дата`+`час`, `сума`+`операц` (avoids "Сума у валюті …"), `деталі`
- The header fully defines the table's columns (missing ones become `None`)
- Control sum: `Обіг за кредитом за період: XXX UAH` (first page)
- **Commission:** from "Деталі операції", acquiring or payment-system transfer, via `_make_transaction`

---

### `parser/parsers/novapay_parser.py`

**Class:** `NovaPayParser(TableParser)`

- `DECIMAL_COMMA = True` — amounts like `1 234,56`
- `DATE_FORMATS`: `dd.mm.yyyy HH:MM` (no seconds) first, then with seconds, then date only
- Header: `дата` + `сума`; columns `Дата/час операції`, `Сума, UAH`
- Columns missing from a header keep their previously saved indices
- Control sum: `Обороти по кредиту: XXX грн` (**last** page)
- No commission

---

### `parser/parsers/generic_parser.py`

**Class:** `GenericParser(BaseParser)` — fallback for unknown banks.

- Scans every table row and takes the first date and the first amount
- No control sum
- Known issue: the amount can be taken from the date cell (`15.01.2024` → `15,01`), see [#3](KNOWN_ISSUES.md#3-generic-parser-takes-the-amount-from-a-date-time-or-row-number)

---

### `parser/io/pdf_reader.py`

`PDFReader.open(pdf_path)` is a context manager over `pdfplumber.open()`. An open failure is wrapped in `Exception("Cannot open PDF file ...")`; errors inside the `with` block propagate unchanged.

---

### `parser/io/csv_writer.py`

`CSVWriter.write(transactions, output_path)`

```
Час,Дата,Сума,Комісія,Сума з врахуванням комісії
07:15:00,05.08.2026,"250,00","0,00","250,00"
```

- Column headers are Ukrainian on purpose: they are the ledger's columns (time, date, amount, commission, amount net of commission)
- Rows in **reverse** parse order: chronological for newest-first statements. Verified for PrivatBank only ([#11](KNOWN_ISSUES.md#11-csv-row-order-depends-on-statement-order-potential))
- UTF-8 with BOM (`utf-8-sig`) so Excel detects the encoding
- Comma decimal separator, so amount fields are quoted

---

### `parser/utils/constants.py`

| Name | Description |
|------|-------------|
| `DATE_PATTERN`, `DATETIME_PATTERN`, `DATETIME_PATTERN_SHORT` | Date regexes (with / without seconds) |
| `AMOUNT_PATTERN`, `WHITESPACE_PATTERN` | Amount and whitespace (incl. nbsp) regexes |
| `GROSS_AMOUNT_PATTERN`, `COMMISSION_PATTERN` | Monobank acquiring |
| `TRANSFER_COMMISSION_PATTERN` | Payment-system transfer `(сума X грн, комісія - Y грн)` (PrivatBank, Monobank) |
| `*_CONTROL_SUM_PATTERN` | Bank control sums |
| `PRIVATBANK_TXN_LINE_PATTERN`, `PRIVATBANK_TIME_PATTERN` | PrivatBank text parsing |
| `MIN_AMOUNT` / `MAX_AMOUNT` | Valid amount bounds |
| `CONTROL_SUM_TOLERANCE` | Allowed control-sum difference |
| `*_KEYWORDS` | Bank detection keywords |
| `MINUS_SIGNS` | Unicode minus variants |
| `CSV_ENCODING` | `utf-8-sig` |

---

### `parser/utils/validators.py`

| Function | Description |
|----------|-------------|
| `is_negative_amount(amount_str)` | Leading minus (`-`, `−`, `–`) or parentheses |
| `is_valid_amount(amount)` | Within `MIN_AMOUNT..MAX_AMOUNT` |
| `extract_and_validate_amount(amount_str, decimal_comma=False)` | `None` for negative, out-of-bounds or invalid values |
| `to_float(number_str, decimal_comma=False)` | Number from statement text (control sum, details); `ValueError` if not a number |

---

### `parser/utils/dates.py`

`extract_datetime(value, formats=DEFAULT_FORMATS)` tries `(regex, strptime)` formats in order. Ready-made formats: `DATETIME_FULL`, `DATETIME_SHORT`, `DATE_ONLY`; `DEFAULT_FORMATS = (DATETIME_FULL, DATE_ONLY)`.

---

### `parser/utils/formatters.py`

| Function | Description |
|----------|-------------|
| `format_date(date, fmt)` | `dd.mm.yyyy` |
| `format_time(date)` | `HH:MM:SS` |
| `format_amount(amount)` | Comma decimal separator |
| `format_csv_row(transaction)` | 5-column CSV row |

---

## Data flow

```
input/statement.pdf
        │
        ▼
┌───────────────────┐
│  PDFReader.open   │ ← the file is opened once
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  BankDetector     │ ← monobank | privatbank | novapay | unknown
└─────────┬─────────┘
          ▼ (creates)
┌───────────────────┐
│  Parser           │ ← parse(pdf) + extract_control_sum(pdf)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ List[Transaction] │ ← income only; gross / commission / net
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ Control sum       │ ← Σ net vs statement, warning on mismatch
└─────────┬─────────┘
          ▼
┌───────────────────┐
│    CSVWriter      │
└─────────┬─────────┘
          ▼
output/statement.csv
```

---

## Design decisions

- **Income filtering at amount extraction.** `validators.extract_and_validate_amount` returns `None` for strings starting with a minus variant (`-`, `−` U+2212, `–` U+2013) or wrapped in parentheses; parsers skip `None`. Never `float()` a cell directly.
- **Control sum is the correctness signal.** Each known bank prints its own credit turnover; matching it against the parsed net total catches dropped or extra rows. It warns rather than fails, because the user still needs a CSV to fix by hand.
- **Declarative parsers.** Bank differences live in class attributes and `constants.py`, so a new table-based bank is mostly configuration.
- **Text parsing for PrivatBank.** Table extraction lost rows at page breaks; text lines plus word coordinates are robust to that.
- **Monobank vs NovaPay header handling differs on purpose.** Monobank's header replaces all columns; NovaPay's keeps previously saved ones.
- **Fresh parser per file.** Table parsers carry column state across pages.

---

## Adding a bank

### 1. Constants in `utils/constants.py`

```python
NEWBANK_KEYWORDS = ['новий банк', 'newbank']
NEWBANK_CONTROL_SUM_PATTERN = r'Оборот по кредиту:\s*([\d\s]+\.?\d*)'
```

### 2. Parser in `parsers/newbank_parser.py`

For tables with a header, subclass `TableParser`:

```python
from ..core.table_parser import TableParser
from ..utils import constants


class NewBankParser(TableParser):
    CONTROL_SUM_PATTERN = constants.NEWBANK_CONTROL_SUM_PATTERN

    def _is_header(self, row_text):
        return 'дата' in row_text and 'сума' in row_text

    def _detect_columns(self, row, columns):
        indices = self._find_column_indices(row, {'date': ['дата'], 'amount': ['сума']})
        return {'date': indices.get('date'), 'amount': indices.get('amount')}

    def _build_transaction(self, cells):
        date_obj = self._extract_date(cells.get('date'))
        amount = self._extract_amount(cells.get('amount'))
        if date_obj and amount:
            return self._make_transaction(date_obj, amount)
        return None
```

For other formats (e.g. text-based, like PrivatBank), subclass `BaseParser` and implement `parse(pdf)`.

### 3. Register in `bank_detector.py`

```python
BANKS = (
    ...,
    ('newbank', constants.NEWBANK_KEYWORDS, NewBankParser),
)
```

### 4. Finish

Export from `parsers/__init__.py`, add a test in `tests/test_parsers.py`, and check a real statement locally: the run must print "Control sum matches".

---

## Testing

```bash
python -m unittest discover -s tests -t .
```

Tests use fake pages (`tests/fakes.py` mimics pdfplumber's `pages`, `extract_text()`, `extract_tables()`, `extract_words()`, `edges`) with synthetic data. Real statements never go into the repository.

---

## Dependencies

- **pdfplumber** — PDF text, table and word extraction
- **Python 3.10+**
