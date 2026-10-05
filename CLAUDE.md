# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Parses Ukrainian bank-statement PDFs (PrivatBank, Monobank, NovaPay, generic fallback) and produces CSV files for the FOP income ledger ("Книга обліку доходів"). Only **income** (positive amounts) is kept; expenses are dropped. User-facing output, comments and docs are in Ukrainian — keep that convention.

## Commands

```bash
pip install -r requirements.txt               # only dependency: pdfplumber (a local venv/ is gitignored)
python main.py                                # processes every input/*.pdf -> output/<same-name>.csv
python -m unittest discover -s tests -t .     # all tests
python -m unittest tests.test_parsers.NovaPayParserTest.test_parse   # single test
```

`run.bat` / `run.sh` wrap `main.py` and auto-install deps. No linter or build step. Tests use synthetic fake pages (`tests/fakes.py` mimics pdfplumber's `pages` / `extract_text()` / `extract_tables()`); real statements are still the final check — run `main.py` and look for "Контрольна сума співпадає". `input/*.pdf` and `output/*.csv` are gitignored — never commit statements or put real statement data into tests (personal financial data).

## Architecture

Pipeline per PDF, orchestrated by `StatementParserManager.process_file` (`parser/manager.py`); the PDF is opened once via `PDFReader.open`:

1. `BankDetector.detect_from_pdf` — lowercases page 1 text and matches keywords from the ordered `BANKS` registry in `parser/bank_detector.py` (Monobank → PrivatBank → NovaPay; first match wins, else `unknown`).
2. `BankDetector.get_parser` — new parser instance from `BANKS` (`GenericParser` for unknown). Always a fresh instance: table parsers keep column state across pages.
3. `parser.parse(pdf)` returns `List[Transaction]`; `parser.extract_control_sum(pdf)` returns the statement's own credit total.
4. Manager compares control sum against `sum(t.gross_amount)` (`CONTROL_SUM_TOLERANCE` = 0.01) and prints a warning on mismatch — the main correctness signal. CSV is written regardless.
5. `CSVWriter.write` — UTF-8 with BOM, 5 columns (`Час, Дата, Сума, Комісія, Сума з врахуванням комісії`), comma decimals, rows in **reversed** parse order.

Parser hierarchy (`parser/core/`, `parser/parsers/`):

- `BaseParser` is configured by class attributes: `CONTROL_SUM_PATTERN` (regex, group 1; `None` = no check), `CONTROL_SUM_PAGE` (0 or -1), `DECIMAL_COMMA`, `DATE_FORMATS` (ordered `(regex, strptime)` tuples from `parser/utils/dates.py`). `extract_control_sum`, `_extract_date`, `_extract_amount` are generic and driven by those.
- `TableParser(BaseParser)` is a template method for `extract_tables()` with a header row: subclasses implement `_is_header(row_text)`, `_detect_columns(row, columns)`, `_build_transaction(cells)`. Column indices found in a header are saved and reused for header-less tables on later pages. Monobank and NovaPay use it; they differ in subtle ways that are intentional (Monobank's header replaces all columns, NovaPay's keeps previously saved ones).
- `PrivatBankParser(BaseParser)` parses raw `extract_text()` lines with `PRIVATBANK_TXN_LINE_PATTERN` (date + amount on one line, `HH:MM` on the next) because pdfplumber dropped the last table row on each page.
- `GenericParser(BaseParser)` takes the first date and first amount in any table row; has a known bug where the amount is taken from the date cell (pinned by an `expectedFailure` test).

Cross-cutting rules:

- Income filtering happens at amount extraction: `validators.extract_and_validate_amount` returns `None` for strings starting with a minus variant (`-`, `−` U+2212, `–` U+2013) or wrapped in parentheses; parsers skip `None`. Never `float()` a cell directly.
- `Transaction` has `gross_amount`, `commission`, `net_amount` (auto = gross − commission); `.amount` is a back-compat alias for gross. Only Monobank fills commission (from "Деталі операції" via `GROSS_AMOUNT_PATTERN` / `COMMISSION_PATTERN`).
- NovaPay: comma decimals, dates without seconds tried first, control sum on the **last** page.
- All regexes, keywords and limits live in `parser/utils/constants.py`.

Adding a bank: keywords + control-sum regex in `constants.py`; subclass `TableParser` (or `BaseParser` for non-table formats); add a `BANKS` entry; export from `parser/parsers/__init__.py`; add a test in `tests/test_parsers.py`. Record changes in `.claude/CHANGELOG.md`; detailed technical docs live in `.claude/DOCS.md`; known bugs, prioritised P1–P3 with repro steps, are in `.claude/BUGS.md` (update it when fixing one).

## Memory Bank System

This project uses the [claude-memory-bank](https://github.com/russbeye/claude-memory-bank) system (agents in `.claude/agents/`, commands in `.claude/commands/context/`, workflows in `.claude/workflows/memory-bank/`). Check the memory bank for relevant context before starting work.

Granular files (authoritative for day-to-day work):

- `.claude/memory_bank/decisions/**` — ADRs and trade-offs
- `.claude/memory_bank/patterns/**` — cross-cutting patterns and conventions
- `.claude/memory_bank/architecture/**` — module topology and data flow
- `.claude/memory_bank/troubleshooting/**` — known issues and proven fixes
- `.claude/memory_bank/stash/**` — temporary scratch pad (read only when referenced)

Rules:

- Context order: memory bank → `code-searcher` agent → archive (last resort). Use `/context-query` with path scopes and a small `--limit`.
- `.claude/memory_bank/archive/**` is read-only historical snapshots; never modify it and don't load it for routine tasks.
- After meaningful code changes run `/context-diff` (delta) or `/update-memory-bank`; `/stale-context-check` for hygiene; `/cleanup-context` to snapshot milestones.
