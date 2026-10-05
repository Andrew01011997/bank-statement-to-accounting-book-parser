# Документація проекту Bank Statement to Accounting Book Parser

Парсер банківських виписок PDF для автоматичної генерації Книги обліку доходів.

---

## Зміст

1. [Огляд архітектури](#огляд-архітектури)
2. [Структура файлів](#структура-файлів)
3. [Детальний опис модулів](#детальний-опис-модулів)
4. [Потік даних](#потік-даних)
5. [Як додати новий банк](#як-додати-новий-банк)
6. [Тести](#тести)

---

## Огляд архітектури

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (точка входу)                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  StatementParserManager                      │
│                     (manager.py)                             │
│                                                              │
│  • Знаходить PDF у input/, відкриває кожен один раз          │
│  • BankDetector → Parser → перевірка контрольної суми → CSV  │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ BankDetector│   │  PDFReader  │   │  CSVWriter  │
│  (реєстр +  │   │    (I/O)    │   │    (I/O)    │
│   Factory)  │   └─────────────┘   └─────────────┘
└──────┬──────┘
       │
       ▼ (створює)
┌─────────────────────────────────────────────────────────────┐
│ BaseParser (ABC) — контрольна сума, дати, суми               │
│  ├── TableParser (ABC) — таблиці з заголовком                │
│  │    ├── MonobankParser                                     │
│  │    └── NovaPayParser                                      │
│  ├── PrivatBankParser — розбір тексту сторінок               │
│  └── GenericParser — fallback                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура файлів

```
bank-statement-to-accounting-book-parser/
├── main.py                 # Точка входу
├── run.sh / run.bat        # Скрипти запуску
├── requirements.txt        # Залежності (pdfplumber)
├── input/                  # Вхідні PDF файли
├── output/                 # Вихідні CSV файли
├── tests/                  # Юніт-тести (unittest, синтетичні сторінки)
│
└── parser/                 # Головний модуль
    ├── __init__.py         # Експорт публічного API
    ├── manager.py          # Координатор процесу
    ├── bank_detector.py    # Реєстр банків + Factory для парсерів
    │
    ├── core/               # Базові класи
    │   ├── base_parser.py  # Абстрактний парсер
    │   ├── table_parser.py # Шаблон для табличних парсерів
    │   └── statement.py    # Модель Transaction
    │
    ├── parsers/            # Конкретні парсери
    │   ├── monobank_parser.py
    │   ├── privatbank_parser.py
    │   ├── novapay_parser.py
    │   └── generic_parser.py
    │
    ├── io/                 # Читання/запис файлів
    │   ├── pdf_reader.py   # Обгортка pdfplumber
    │   └── csv_writer.py   # Генерація CSV
    │
    └── utils/              # Допоміжні утиліти
        ├── constants.py    # Regex, ключові слова, межі
        ├── validators.py   # Розбір і валідація сум
        ├── dates.py        # Розбір дат
        └── formatters.py   # Форматування дат/сум для CSV
```

---

## Детальний опис модулів

### `parser/manager.py`

**Клас:** `StatementParserManager`

| Метод | Опис |
|-------|------|
| `__init__(input_dir, output_dir)` | Ініціалізація з папками input/output |
| `run()` | Запуск парсингу всіх PDF у папці input |
| `process_file(pdf_file)` | Обробка одного PDF файлу |
| `_report_control_sum(transactions, control_sum)` | Звіт про збіг контрольної суми та комісії |
| `_write_csv(pdf_file, transactions)` | Запис CSV з назвою PDF |

**Алгоритм `process_file()`:**
1. Відкриває PDF через `PDFReader.open()` (один раз)
2. Визначає банк через `BankDetector.detect_from_pdf(pdf)`
3. Отримує новий парсер через `BankDetector.get_parser()`
4. `parser.parse(pdf)` та `parser.extract_control_sum(pdf)`
5. Виводить попередження парсера (`parser.warnings`, напр. неузгоджена комісія)
6. Порівнює контрольну суму із сумою `net_amount` — зарахованого (допуск `CONTROL_SUM_TOLERANCE` = 0.01) — лише попередження, CSV записується в будь-якому разі
7. Записує CSV через `CSVWriter.write()`

Помилка в одному файлі виводиться з traceback, обробка решти продовжується.

---

### `parser/bank_detector.py`

**Реєстр `BANKS`:** кортежі `(тип, ключові слова, клас парсера)`. Перевіряються по черзі (Monobank → PrivatBank → NovaPay), перший збіг перемагає.

| Метод | Опис |
|-------|------|
| `detect_from_pdf(pdf) -> str` | Тип банку за текстом першої сторінки відкритого PDF |
| `detect(pdf_path) -> str` | Те саме, але відкриває файл сам |
| `get_parser(bank_type) -> BaseParser` | Новий екземпляр парсера; невідомий тип → `GenericParser` |

Ключові слова (`constants.py`):
- `monobank`, `універсал банк` → MonobankParser
- `приватбанк` → PrivatBankParser
- `novapay`, `новапей`, `935871` → NovaPayParser
- інше → GenericParser

---

### `parser/core/statement.py`

**Клас:** `Transaction` (dataclass)

| Поле | Тип | Опис |
|------|-----|------|
| `date` | `datetime` | Дата та час транзакції |
| `gross_amount` | `float` | Сума до вирахування комісії |
| `commission` | `float` | Комісія банку (0 за замовчуванням) |
| `net_amount` | `float` | Сума після комісії (якщо не вказано — `gross - commission`) |

`amount` — властивість для зворотної сумісності, повертає `gross_amount`.

---

### `parser/core/base_parser.py`

**Клас:** `BaseParser` (ABC). Налаштовується атрибутами класу:

| Атрибут | За замовчуванням | Опис |
|---------|------------------|------|
| `CONTROL_SUM_PATTERN` | `None` | Regex контрольної суми (група 1); `None` — без перевірки |
| `CONTROL_SUM_PAGE` | `0` | Сторінка з контрольною сумою (`-1` — остання) |
| `DECIMAL_COMMA` | `False` | Кома як десятковий розділювач |
| `DATE_FORMATS` | `dates.DEFAULT_FORMATS` | Формати дат по черзі |

| Метод | Опис |
|-------|------|
| `parse(pdf)` | Абстрактний |
| `extract_control_sum(pdf)` | Шукає `CONTROL_SUM_PATTERN` на `CONTROL_SUM_PAGE` |
| `_extract_date(value)` | `dates.extract_datetime(value, DATE_FORMATS)` |
| `_extract_amount(value)` | `validators.extract_and_validate_amount(value, DECIMAL_COMMA)` — **фільтрує негативні суми** |

---

### `parser/core/table_parser.py`

**Клас:** `TableParser(BaseParser)` — Template Method для таблиць з рядком заголовка.

`parse()` обходить усі таблиці всіх сторінок. Для кожної таблиці:
1. Шукає перший рядок, для якого `_is_header(row_text)` істинне
2. `_detect_columns(row, columns)` повертає індекси колонок; знайдені зберігаються в `_saved_columns`
3. Таблиці без заголовка (наступні сторінки) використовують збережені індекси та парсяться з першого рядка
4. Якщо немає колонок з `REQUIRED_COLUMNS` (`date`, `amount`) — таблиця пропускається
5. Для кожного рядка `_build_transaction(cells)` повертає `Transaction` або `None`

Через збережені колонки екземпляр парсера використовується лише для одного файлу (`get_parser` завжди створює новий).

`_find_column_indices(row, keywords)` — пошук колонок за ключовими словами; для `amount` колонки з "валют" мають нижчий пріоритет.

---

### `parser/parsers/privatbank_parser.py`

**Клас:** `PrivatBankParser(BaseParser)`

- Розбирає **текст** сторінок, а не таблиці: `pdfplumber.extract_tables()` губив рядки на розривах сторінок (рядок над рамкою таблиці)
- Рядок транзакції: `<номер> DD.MM.YYYY <сума> <призначення>` (`PRIVATBANK_TXN_LINE_PATTERN`)
- Час `HH:MM` — з наступного рядка (`PRIVATBANK_TIME_PATTERN`)
- Контрольна сума: `разом за кредитом: XXX` (перша сторінка)
- **Комісія платіжної системи:** «Призначення платежу» збирається зі слів `extract_words()` між вертикальними лініями таблиці праворуч від суми (`_page_descriptions`; у тексті сторінки колонки перемішані). Рядок транзакції починається словом-датою, за яким іде сума (`_row_anchors`). Далі `_make_transaction` (див. нижче)

---

### `parser/parsers/monobank_parser.py`

**Клас:** `MonobankParser(TableParser)`

- Заголовок: рядок з `дата`, `сума`, `операц`
- Колонки: `дата`+`час`, `сума`+`операц` (уникає "Сума у валюті …"), `деталі`
- Контрольна сума: `Обіг за кредитом за період: XXX UAH` (перша сторінка)
- **Комісія:** з "Деталі операції" — еквайринг (`Загалом X грн. Комісія банку Y грн.`) або переказ від платіжної системи (`(сума X грн, комісія - Y грн.)`). Тоді `gross = X`, `commission = Y`, `net` = сума з таблиці, якщо `X − Y == net` (`BaseParser._make_transaction`)

---

### `parser/parsers/novapay_parser.py`

**Клас:** `NovaPayParser(TableParser)`

- `DECIMAL_COMMA = True` — суми `1 234,56`
- `DATE_FORMATS`: спочатку `dd.mm.yyyy HH:MM` (без секунд), потім з секундами, потім лише дата
- Заголовок: `дата` + `сума`; колонки `Дата/час операції`, `Сума, UAH`
- Контрольна сума: `Обороти по кредиту: XXX грн` (**остання** сторінка)
- Комісії немає

---

### `parser/parsers/generic_parser.py`

**Клас:** `GenericParser(BaseParser)` — fallback для невідомих банків.

- Сканує всі рядки таблиць, бере першу дату і першу суму в рядку
- Без контрольної суми
- Відома проблема: сума може бути взята з комірки з датою (`15.01.2024` → `15,01`)

---

### `parser/io/pdf_reader.py`

`PDFReader.open(pdf_path)` — context manager над `pdfplumber.open()`. Помилка відкриття загортається у `Exception("Помилка відкриття PDF файлу ...")`; помилки всередині блоку `with` прокидаються без змін.

---

### `parser/io/csv_writer.py`

`CSVWriter.write(transactions, output_path)`

```
Час,Дата,Сума,Комісія,Сума з врахуванням комісії
07:15:00,05.08.2026,"250,00","0,00","250,00"
```

- Транзакції у **зворотному порядку** (reversed відносно порядку парсингу)
- Кодування UTF-8 з BOM (`utf-8-sig`) для Excel
- Суми в європейському форматі (кома), тому поля сум у лапках

---

### `parser/utils/constants.py`

| Назва | Опис |
|-------|------|
| `DATE_PATTERN`, `DATETIME_PATTERN`, `DATETIME_PATTERN_SHORT` | Regex дат (з секундами / без) |
| `AMOUNT_PATTERN`, `WHITESPACE_PATTERN` | Regex суми та пробілів (з nbsp) |
| `GROSS_AMOUNT_PATTERN`, `COMMISSION_PATTERN` | Еквайринг Monobank |
| `TRANSFER_COMMISSION_PATTERN` | Переказ від платіжної системи `(сума X грн, комісія - Y грн)` (PrivatBank, Monobank) |
| `*_CONTROL_SUM_PATTERN` | Контрольні суми банків |
| `PRIVATBANK_TXN_LINE_PATTERN`, `PRIVATBANK_TIME_PATTERN` | Текстовий розбір PrivatBank |
| `MIN_AMOUNT` / `MAX_AMOUNT` | Межі валідних сум |
| `CONTROL_SUM_TOLERANCE` | Допуск розбіжності контрольної суми |
| `*_KEYWORDS` | Ключові слова банків |
| `MINUS_SIGNS` | Unicode символи мінуса |
| `CSV_ENCODING` | `utf-8-sig` |

---

### `parser/utils/validators.py`

| Функція | Опис |
|---------|------|
| `is_negative_amount(amount_str)` | Мінус (`-`, `−`, `–`) на початку або дужки |
| `is_valid_amount(amount)` | Межі `MIN_AMOUNT..MAX_AMOUNT` |
| `extract_and_validate_amount(amount_str, decimal_comma=False)` | `None` для негативних, поза межами, невалідних |
| `to_float(number_str, decimal_comma=False)` | Число з тексту виписки (контрольна сума, деталі); `ValueError` якщо не число |

---

### `parser/utils/dates.py`

`extract_datetime(value, formats=DEFAULT_FORMATS)` — пробує формати `(regex, strptime)` по черзі. Готові формати: `DATETIME_FULL`, `DATETIME_SHORT`, `DATE_ONLY`; `DEFAULT_FORMATS = (DATETIME_FULL, DATE_ONLY)`.

---

### `parser/utils/formatters.py`

| Функція | Опис |
|---------|------|
| `format_date(date, fmt)` | `dd.mm.yyyy` |
| `format_time(date)` | `HH:MM:SS` |
| `format_amount(amount)` | Європейський формат (кома) |
| `format_csv_row(transaction)` | Рядок CSV з 5 колонок |

---

## Потік даних

```
input/statement.pdf
        │
        ▼
┌───────────────────┐
│  PDFReader.open   │ ← файл відкривається один раз
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  BankDetector     │ ← monobank | privatbank | novapay | unknown
└─────────┬─────────┘
          ▼ (створює)
┌───────────────────┐
│  Parser           │ ← parse(pdf) + extract_control_sum(pdf)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ List[Transaction] │ ← тільки доходи; gross / commission / net
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ Контрольна сума   │ ← Σ net vs виписка, попередження при розбіжності
└─────────┬─────────┘
          ▼
┌───────────────────┐
│    CSVWriter      │
└─────────┬─────────┘
          ▼
output/statement.csv
```

---

## Як додати новий банк

### 1. Константи в `utils/constants.py`

```python
NEWBANK_KEYWORDS = ['новий банк', 'newbank']
NEWBANK_CONTROL_SUM_PATTERN = r'Оборот по кредиту:\s*([\d\s]+\.?\d*)'
```

### 2. Парсер в `parsers/newbank_parser.py`

Для таблиць із заголовком — наслідуйте `TableParser`:

```python
from ..core.table_parser import TableParser
from ..core.statement import Transaction
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
            return Transaction(date=date_obj, gross_amount=amount)
        return None
```

Для іншого формату (наприклад, текстового, як PrivatBank) — наслідуйте `BaseParser` і реалізуйте `parse(pdf)`.

### 3. Зареєструвати в `bank_detector.py`

```python
BANKS = (
    ...,
    ('newbank', constants.NEWBANK_KEYWORDS, NewBankParser),
)
```

### 4. Експорт в `parsers/__init__.py`, тест у `tests/test_parsers.py`, перевірка на реальній виписці (має бути "Контрольна сума співпадає").

---

## Тести

```bash
python -m unittest discover -s tests -t .
```

Тести використовують підробні сторінки (`tests/fakes.py`) з синтетичними даними — реальні виписки в репозиторій не додаються.

---

## Залежності

- **pdfplumber** — парсинг PDF та витягування таблиць/тексту
- **Python 3.7+** — dataclasses, type hints
