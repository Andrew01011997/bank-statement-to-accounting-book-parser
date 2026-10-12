# Bank Statement to Accounting Book Parser

[![CI](https://github.com/Andrew01011997/bank-statement-to-accounting-book-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Andrew01011997/bank-statement-to-accounting-book-parser/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

🇺🇦 [Українська версія](README.uk.md)

Turns Ukrainian bank statement PDFs into CSV files for the income ledger of a sole proprietor (FOP, "Книга обліку доходів"). Income is extracted, expenses are dropped, and every statement is checked against the bank's own credit total.

## Features

- **Automatic bank detection** from the PDF content
- **PrivatBank, Monobank, NovaPay** support, with a best-effort generic fallback
- **Income only**: debits, fees and refunds are filtered out
- **Commission handling**: acquiring and payment-system fees are split into gross amount, commission and credited amount
- **Control-sum verification** against the statement's credit turnover
- **Excel-ready CSV** (UTF-8 with BOM, comma decimals)
- **Fully offline**: statements never leave your machine

## Supported banks

| Bank / service | Status | Control sum line |
|----------------|--------|------------------|
| PrivatBank | ✅ | "Разом за кредитом" |
| Monobank | ✅ | "Обіг за кредитом за період" |
| NovaPay | ✅ | "Обороти по кредиту" |
| Other | ⚠️ Generic parser, no verification ([known issue #3](docs/KNOWN_ISSUES.md#3-generic-parser-takes-the-amount-from-a-date-time-or-row-number)) | — |

## Quick start

Requires **Python 3.10+**.

1. Download or clone the repository.
2. Put your PDF statements into the `input/` folder.
3. Run:
   - **Windows:** double-click `run.bat`
   - **macOS / Linux:** `./run.sh`
4. Collect the CSV files from `output/`.

The launchers install the only dependency (`pdfplumber`) on first run.

### Manual run

```bash
python -m pip install -r requirements.txt
python main.py
```

Each `input/<name>.pdf` produces `output/<name>.csv`.

## Output

| Час | Дата | Сума | Комісія | Сума з врахуванням комісії |
|-----|------|------|---------|----------------------------|
| 12:30:45 | 15.01.2024 | 1000,00 | 13,00 | 987,00 |

Column headers are in Ukrainian because they are the ledger's columns: time, date, amount (gross), commission, amount net of commission.

- **Commission** is filled for Monobank acquiring and for payment-system transfers ("сума X грн, комісія Y грн") at PrivatBank and Monobank; otherwise it is `0`
- **Encoding:** UTF-8 with BOM, so Excel opens it correctly
- **Amounts:** comma as the decimal separator
- **Order:** chronological (statements list newest first; the CSV is reversed)

## Verifying the result

For known banks the console shows whether the parsed total matches the statement:

```
Processing: statement.pdf
  Bank: Privatbank
  ✓ Control sum matches: 12345.67 UAH
CSV written: output/statement.csv
  ✓ 42 transaction(s) found
```

A `⚠️ WARNING: transaction total does not match the control sum!` means some rows were missed or misread. The CSV is still written so you can fix it by hand. Please [open an issue](https://github.com/Andrew01011997/bank-statement-to-accounting-book-parser/issues/new/choose) with an anonymised description of the layout.

## How it works

```
PDF statement
    │
    ▼
BankDetector   → detects the bank from first-page keywords
    │
    ▼
Parser         → extracts income transactions (Monobank / PrivatBank / NovaPay / Generic)
    │
    ▼
Control sum    → compares the parsed total with the statement's credit turnover
    │
    ▼
CSVWriter      → writes the ledger CSV
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Privacy

Bank statements contain personal financial data. This tool:

- runs locally and makes no network requests;
- git-ignores everything inside `input/` and `output/`;
- is tested only with synthetic data.

Never commit statements or CSV output, and never attach them to issues. See [SECURITY.md](SECURITY.md).

## Disclaimer

This software is provided as is. It is not tax or accounting advice. Always review the generated ledger before submitting anything to the tax authority.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -t .   # tests
ruff check .                                # lint
```

- [Contributing guide](CONTRIBUTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Known issues](docs/KNOWN_ISSUES.md)
- [Changelog](CHANGELOG.md)

## Roadmap

- More banks (PUMB, Oschadbank, …)
- Command-line options for the input/output folders
- Merging several statements into one CSV
- Excel (.xlsx) export

## License

[MIT](LICENSE)
