# Known Issues

🇺🇦 [Українська версія](KNOWN_ISSUES.uk.md)

Results of a full code review (version 1.3.0, 2026-10-05; re-verified 2026-10-12). Every issue was reproduced on synthetic data unless stated otherwise. Items marked "potential" are inferred from the code and not reproduced.

Priorities:
- **P1 (high)**: the program crashes or silently writes wrong amounts into the ledger.
- **P2 (medium)**: transactions are lost or wrongly included. For known banks this usually shows up as a control-sum warning.
- **P3 (low)**: inconvenience, cosmetics, rare cases.

| # | Priority | Issue | Status |
|---|----------|-------|--------|
| 1 | P1 | Crash when console output is not UTF-8 | ✅ Fixed |
| 2 | P1 | Bank is detected from any match on the first page | Open |
| 3 | P1 | Generic parser takes the amount from a date, time or row number | Open |
| 4 | P2 | A missing control sum silently skips the check | Open |
| 5 | P2 | A data row that looks like a header swallows table rows | Open |
| 6 | P2 | Imprecise amount parsing | Open |
| 7 | P2 | Negative amounts are recognised only by a leading sign | Open |
| 8 | P2 | PrivatBank: any "date + amount" line is a transaction | Open |
| 9 | P2 | `.gitignore` did not protect all statements | ✅ Fixed |
| 10 | P3 | PrivatBank: transaction time taken from the next line blindly | Open |
| 11 | P3 | CSV row order depends on statement order | Open |
| 12 | P3 | Launcher scripts | ✅ Fixed |
| 13 | P3 | Input file discovery and order | ✅ Fixed |
| 14 | P3 | Monobank: commission consistency was not checked | ✅ Fixed |

---

## P1 — high

### 1. ✅ FIXED — Crash when console output is not UTF-8: no CSV is written
- **Status:** fixed. `main.configure_console()` switches `stdout`/`stderr` to UTF-8 with `errors='replace'`. Regression test: `tests/test_main.py` (`ConsoleEncodingTest`).
- **Where:** `parser/manager.py` (every `print` with `✓`, `⚠️`, `ℹ️`, `❌`)
- **Repro:** `python main.py > log.txt` on Windows. Output was encoded as cp1251/cp1252, a `print` with `✓` raised `UnicodeEncodeError`, and no CSV was written.
- **When it happens:** output redirected to a file or pipe, Task Scheduler, some IDEs.

### 2. Bank is detected from any match on the first page, counterparties included
- **Where:** `parser/bank_detector.py` (`detect_from_pdf`, `BANKS` order)
- **Repro:** a PrivatBank page containing `Переказ від АТ "УНІВЕРСАЛ БАНК"` is detected as `monobank`. A NovaPay page with `банк платника АТ КБ ПРИВАТБАНК` is detected as `privatbank`.
- **Why it is real:** names of other banks and payment services routinely appear in payment descriptions.
- **Impact:** the wrong parser is chosen, yielding 0 transactions ("No transactions found", no CSV) or wrong ones.
- **Fix:** look for keywords only in the page header (first N lines) or for bank-unique markers (document title, the bank's own MFO or EDRPOU code) rather than any mention of its name. Better still: verify that the chosen parser found a control sum.

### 3. Generic parser takes the amount from a date, time or row number
- **Where:** `parser/parsers/generic_parser.py`, `constants.AMOUNT_PATTERN`
- **Repro:**
  - `['15.01.2024 12:30:45', '100.00']` gives amount `15.01`
  - `['1', '15.01.2024', '100.00']` gives amount `1.00`
  - `['12:30', '15.01.2024', '100.00']` gives amount `12.00`
- **Impact:** for unknown banks the CSV has wrong amounts, and with no control sum there is no warning. Pinned by `GenericParserTest.test_amount_not_taken_from_date_cell` (`expectedFailure`).
- **Fix:** never look for the amount in the cell where the date was found. Accept as an amount only a cell that fully matches the amount format (`^\s*[-−–]?[\d\s\xa0]+[.,]\d{2}\s*$`). Possibly refuse to write a CSV for an unknown bank without confirmation.

---

## P2 — medium

### 4. When the control sum is not found, the check is silently skipped
- **Where:** `parser/manager.py` (`if control_sum and transactions`), `BaseParser.extract_control_sum` (`except Exception: pass`)
- **Repro:** the "разом за кредитом" label on page 2, or a number broken by a line wrap (`12\n345.67`), yields `None` with no message.
- **Impact:** if a bank changes its statement template, the main verification mechanism turns off silently.
- **Fix:** for parsers with a `CONTROL_SUM_PATTERN`, print "⚠️ Control sum not found — check manually".

### 5. A data row that looks like a header swallows preceding table rows
- **Where:** `parser/core/table_parser.py` (`_parse_table`), `NovaPayParser._is_header` (the words `дата` and `сума` anywhere in the row are enough)
- **Repro:** in a header-less NovaPay table, a row with the description `Оплата, сума згідно рахунку, дата поставки 01.08` is taken for a header. It and every row before it are lost.
- **Impact:** lost transactions. Visible through the control-sum warning.
- **Fix:** look for the header only among the first rows of a table, or require the keywords in separate cells (as `_find_column_indices` does) rather than in the joined row text.

### 6. Imprecise amount parsing
- **Where:** `constants.AMOUNT_PATTERN = r'(\d+(?:\.\d{2})?)'`, `validators.extract_and_validate_amount`
- **Repro:**
  - `'15.5'` gives `15.0`, and `'15,5'` (NovaPay) also gives `15.0`: a single decimal digit is dropped
  - `'1,200.50'` gives `1.0`: comma as thousands separator
  - `'1.200,50'` with `decimal_comma` gives `1.2`: dot as thousands separator
  - `'100.123'` gives `100.12`
- **Impact:** for known banks it shows up in the control sum (current formats use 2 decimals and space separators); for the generic parser it is silent.
- **Fix:** parse the whole amount (fullmatch, 1–2 decimals, thousands separators) and reject unrecognised values with a warning instead of truncating them.

### 7. Negative amounts are recognised only by a leading sign
- **Where:** `validators.is_negative_amount`
- **Repro:** `'100.00-'`, `'UAH -100.00'`, `'Dr 100.00'` are treated as income `100.0`.
- **Impact:** expenses end up in the income ledger. Does not occur with the current formats of the three banks; with the generic parser or a format change it would happen silently.
- **Fix:** look for a minus before the first digit (after a currency or spaces) and at the end of the string. For table formats, prefer separate debit and credit columns.

### 8. PrivatBank: any "date + amount" line is treated as a transaction
- **Where:** `constants.PRIVATBANK_TXN_LINE_PATTERN`, `PrivatBankParser.parse`
- **Repro:** lines `Вхідний залишок на 01.08.2026 15 000.00` and `Вихідний залишок 05.08.2026 15 100.00` become income.
- **Current state:** known statement layouts contain no such lines. If they appear, the control-sum warning will show it.
- **Fix:** require a row number at the start of the line (`^\d+\s+DD.MM.YYYY`) or drop lines containing "залишок", "разом", "обіг".

### 9. ✅ FIXED — `.gitignore` did not protect all statements
- **Status:** fixed. `.gitignore` ignores everything in `input/` and `output/` (any extension, any nesting) except `.gitkeep`.
- **Before:** `input/*.pdf`, `output/*.csv` did not ignore `input/2026/x.pdf`, `output/x.xlsx` or (on Linux/macOS) `input/x.PDF`.
- **Impact:** risk of committing a real statement with personal data.

---

## P3 — low

### 10. PrivatBank: the transaction time is taken from the next line blindly
- **Where:** `PrivatBankParser.parse` (first `HH:MM` on the next line)
- **Repro:** if no time line follows a transaction line, the time is taken from the next transaction's description (`…о 09:30` gives `09:30`). If the transaction line is the last on the page, the time is lost (`00:00:00`).
- **Current state:** in known layouts no page ends with a transaction line. Amounts are unaffected.
- **Fix:** take the time only if the next line is not a transaction line; carry the last line of a page over to the next page.

### 11. CSV row order depends on statement order (potential)
- **Where:** `parser/io/csv_writer.py` (`reversed(transactions)`)
- **Summary:** the CSV is chronological only for newest-first statements. Verified for PrivatBank; not verified for Monobank and NovaPay.
- **Fix:** sort by `date` instead of `reversed`.

### 12. ✅ FIXED — Launcher scripts
- **Status:** fixed. The scripts `cd` into their own folder (`cd /d "%~dp0"` / `cd "$(dirname "$0")"`), install dependencies with `python -m pip` (the same interpreter that runs `main.py`), and print English messages, so the `cmd` code page no longer garbles them.
- **Before:** running from another folder or a shortcut failed with "input folder does not exist"; `pip` could install into a different Python; Ukrainian messages in `run.bat` were garbled in `cmd` (code page 866).

### 13. ✅ FIXED — Input file discovery and order
- **Status:** fixed. `StatementParserManager.run` matches `*.pdf` case-insensitively and processes files in case-insensitive name order, the same on every OS. A missing or non-directory `input` prints a message instead of crashing. Test: `tests/test_manager.py`.
- **Before:** `glob('*.pdf')` missed `*.PDF` on Linux and macOS; processing order was unsorted.

### 14. ✅ FIXED — Monobank: commission consistency was not checked
- **Status:** fixed. `BaseParser._make_transaction` accepts a commission only when `gross − commission == net` (tolerance 0.01); otherwise `gross = net` and a console warning is printed. Applies to the parsers that read commissions (PrivatBank, Monobank); NovaPay and the generic parser build transactions without a commission. Tests: `test_transfer_commission`, `test_commission_from_description_column`.
- **Before:** `gross` came from "Деталі операції" and `net` from the amount column, but `gross − commission == net` was not checked. A details-parsing error would silently change the ledger amount.
