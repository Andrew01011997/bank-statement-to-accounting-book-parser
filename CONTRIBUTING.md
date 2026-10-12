# Contributing

🇺🇦 [Українська версія](CONTRIBUTING.uk.md)

Thanks for helping! Bug reports, new bank formats and fixes are welcome.

## Ground rule: no real data

Never commit or attach real bank statements, CSV output or screenshots with real data. Describe layouts with made-up values. See [SECURITY.md](SECURITY.md).

## Setup

```bash
git clone https://github.com/Andrew01011997/bank-statement-to-accounting-book-parser.git
cd bank-statement-to-accounting-book-parser
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

## Before you open a pull request

```bash
python -m unittest discover -s tests -t .   # all tests must pass
ruff check .                                # no lint errors
```

If you changed a parser, also run `python main.py` on a real statement **locally** and check for "Control sum matches". Do not commit that statement.

## Conventions

- **Language:** code, comments, docstrings, console output and commit messages are in English. Keywords and regexes that match statement text stay in Ukrainian, and so do the CSV headers (they are the ledger's column names).
- **Configuration over code:** regexes, keywords and limits belong in `parser/utils/constants.py`.
- **Amounts:** never `float()` a cell directly; use `BaseParser._extract_amount`, which also filters out expenses.
- **Tests:** every change comes with a test on synthetic pages (`tests/fakes.py`). A known but unfixed bug can be pinned with `@unittest.expectedFailure`.
- **Docs:** update `CHANGELOG.md` and `CHANGELOG.uk.md`; when fixing a known issue, update both `docs/KNOWN_ISSUES*.md` files. Keep the English and Ukrainian versions of a document in sync.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Adding a bank

See [docs/ARCHITECTURE.md → Adding a bank](docs/ARCHITECTURE.md#adding-a-bank).
