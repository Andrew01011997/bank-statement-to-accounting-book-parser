# Changelog

🇺🇦 [Українська версія](CHANGELOG.uk.md)

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- MIT license (`LICENSE`)
- English documentation with Ukrainian versions (`*.uk.md`): `README`, `CHANGELOG`, `CONTRIBUTING`, `SECURITY`, `docs/ARCHITECTURE`, `docs/KNOWN_ISSUES`
- GitHub Actions CI: ruff plus tests on Linux, Windows and macOS (Python 3.10 and 3.13); Dependabot for pip and Actions
- Issue and PR templates warning against attaching real statements
- `pyproject.toml` (ruff config), `requirements-dev.txt`, `.editorconfig`, `.gitattributes`
- `tests/test_manager.py`: input file discovery

### Changed
- Code, comments, docstrings and console messages are in English. CSV headers stay Ukrainian (they are the ledger's columns), as do keywords and regexes that match statement text
- Documentation moved from `.claude/` to `docs/`, changelog to the repository root
- Minimum Python version is 3.10
- `main.py` exits with code 1 when the input folder is missing or unreadable or any file fails; the launchers pass the code on
- Sample amounts in comments, docs and tests replaced with synthetic values

### Fixed
- `.gitignore` ignores everything in `input/` and `output/` (subfolders, `.PDF`, `.xlsx`) so real statements cannot be committed (KNOWN_ISSUES #9)
- Launcher scripts work from any folder and install dependencies with `python -m pip` (KNOWN_ISSUES #12)
- `*.PDF` is found on Linux and macOS; files are processed in the same case-insensitive name order on every OS (KNOWN_ISSUES #13)
- Output redirected to a file, pipe or scheduler on Windows (cp1251/cp1252) no longer breaks processing: `main.py` switches `stdout`/`stderr` to UTF-8 at startup (`configure_console()`) (KNOWN_ISSUES #1)
- **Payment-system commissions** for PrivatBank and Monobank. Credits like "Переказ коштів … (сума X грн, комісія - Y грн.)" used to go into the ledger net of commission. Now `Сума` = X, `Комісія` = Y, `Сума з врахуванням комісії` = credited amount
- Monobank: the last table row on a page without a bottom border was lost (control sum mismatch). `TableParser._extract_tables` closes the table with a line at the bottom of the vertical edges
- The control sum is compared with credited amounts (`net_amount`), not pre-commission amounts

### Added (commissions)
- `BaseParser._make_transaction` / `_extract_commission`: commission from the payment description for all parsers. Accepted only if `amount − commission == credited`, otherwise a warning (`parser.warnings`, KNOWN_ISSUES #14). Also warns when a commission is mentioned in an unrecognised format
- `constants.TRANSFER_COMMISSION_PATTERN` (Latin or Cyrillic "і", "1 234,56" and "1234, 56")
- `PrivatBankParser._page_descriptions`: the "Призначення платежу" column rebuilt from page words (`extract_words`) between the table's vertical lines
- `tests/fakes.py`: `FakePage(words=, edges=)`, `words()` and `v_edges()` helpers

### Removed
- Unused claude-memory-bank agents, commands and workflows from `.claude/`

## [1.3.0] - 2026-10-05

Refactoring with no change in output: on a real PrivatBank statement the CSV and console output are byte-identical to the previous version.

### Added
- `core/table_parser.py` — `TableParser`, a shared template for table parsers (Monobank, NovaPay): header detection, column state across pages, row iteration
- `utils/dates.py` — single date parser with an ordered list of formats
- `validators.to_float()` — amounts from statement text (control sums, transaction details)
- `BankDetector.detect_from_pdf(pdf)` and the `BANKS` registry
- Unit tests in `tests/` (unittest, synthetic pages)

### Changed
- `BaseParser.extract_control_sum()` implemented once; parsers only set `CONTROL_SUM_PATTERN`, `CONTROL_SUM_PAGE`, `DECIMAL_COMMA`, `DATE_FORMATS`
- `extract_and_validate_amount()` supports a comma decimal separator
- Control-sum and PrivatBank text regexes moved to `constants.py`; added `CONTROL_SUM_TOLERANCE`
- The PDF is opened once per file (previously twice: detection and parsing)
- `PDFReader.open()` wraps only file-open errors
- PrivatBank is parsed from page text instead of tables (pdfplumber dropped the last table row on every page)

### Removed
- `parsers/monobank_parser_camelot.py` (unused, depended on camelot)
- `utils/text_parser.py` (unused)
- Unused constants `TIME_PATTERN`, `TIME_PATTERN_SHORT`, `AMOUNT_PATTERN_COMMA`

## [1.2.0] - 2026-01-16

### Added
- Monobank **acquiring commission** from the "Деталі операції" column (`Загалом X грн. Комісія банку Y грн.`)
- `Transaction` model with `gross_amount`, `commission`, `net_amount`
- `GROSS_AMOUNT_PATTERN`, `COMMISSION_PATTERN` in `constants.py`

### Changed
- CSV has **5 columns**: Час, Дата, Сума, Комісія, Сума з врахуванням комісії
- `formatters.format_csv_row(transaction)`, headers in `CSVWriter`
- All parsers use the new `Transaction` model

## [1.1.0] - 2025-01-15

### Added
- **NovaPay** support (`novapay_parser.py`)
- Date format without seconds (`dd.mm.yyyy HH:MM`)
- Comma decimal separator (`1 234,56`)
- NovaPay control sum: "Обороти по кредиту"

## [1.0.0] - 2024-12-28

### Added
- First release: **PrivatBank**, **Monobank**, generic fallback parser
- Automatic bank detection from PDF content
- Control-sum verification
- Income only: negative amounts (expenses) are filtered out, including Unicode minus variants
- Ledger CSV (UTF-8 with BOM, comma decimal separator)
- `run.bat` and `run.sh` launchers
