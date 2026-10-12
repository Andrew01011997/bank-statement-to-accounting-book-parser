# Security and Privacy Policy

🇺🇦 [Українська версія](SECURITY.uk.md)

## Personal data

Bank statements and the generated CSV files contain personal financial data: names, tax IDs, IBANs, counterparties and amounts.

- **Never** commit files from `input/` or `output/`. Both folders are git-ignored except for their `.gitkeep` placeholders.
- **Never** attach real statements, CSV output or unredacted screenshots to issues, pull requests or discussions.
- Tests must use synthetic data only (see `tests/fakes.py`).
- If you accidentally published personal data, delete it right away and rewrite the git history (for example with [`git filter-repo`](https://github.com/newren/git-filter-repo)); deleting the file in a new commit is not enough.

The parser runs fully offline and makes no network requests.

## Supported versions

Only the latest commit on `main` receives fixes.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub: **Security → Report a vulnerability** on the repository page. Do not open a public issue.

Include a description, steps to reproduce with synthetic data, and the impact. You should get a response within 14 days.
