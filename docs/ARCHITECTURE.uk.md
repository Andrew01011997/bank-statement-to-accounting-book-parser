# Архітектура

🇬🇧 [English version](ARCHITECTURE.md)

Технічна документація парсера банківських виписок для Книги обліку доходів ФОП.

## Зміст

1. [Огляд](#огляд)
2. [Структура проекту](#структура-проекту)
3. [Модулі](#модулі)
4. [Потік даних](#потік-даних)
5. [Архітектурні рішення](#архітектурні-рішення)
6. [Як додати банк](#як-додати-банк)
7. [Тести](#тести)

---

## Огляд

```
┌─────────────────────────────────────────────────────────────┐
│                          main.py                            │
│                       (точка входу)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  StatementParserManager                     │
│                      (manager.py)                           │
│                                                             │
│  • Знаходить PDF у input/, відкриває кожен один раз         │
│  • BankDetector → Parser → перевірка контрольної суми → CSV │
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
│ BaseParser (ABC) — контрольна сума, дати, суми, комісія     │
│  ├── TableParser (ABC) — таблиці з заголовком               │
│  │    ├── MonobankParser                                    │
│  │    └── NovaPayParser                                     │
│  ├── PrivatBankParser — розбір тексту сторінок              │
│  └── GenericParser — fallback                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура проекту

```
bank-statement-to-accounting-book-parser/
├── main.py                 # Точка входу
├── run.sh / run.bat        # Скрипти запуску (встановлюють залежності, запускають main.py)
├── requirements.txt        # Залежність (pdfplumber)
├── requirements-dev.txt    # + ruff
├── pyproject.toml          # Налаштування інструментів (ruff)
├── input/                  # Вхідні PDF (ігноруються git)
├── output/                 # Вихідні CSV (ігноруються git)
├── docs/                   # Архітектура, відомі проблеми
├── tests/                  # Юніт-тести (unittest, синтетичні сторінки)
│
└── parser/                 # Головний пакет
    ├── __init__.py         # Публічний API
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

## Модулі

### `parser/manager.py`

**Клас:** `StatementParserManager`

| Метод | Опис |
|-------|------|
| `__init__(input_dir, output_dir)` | Папки input/output |
| `run()` | Парсинг усіх PDF у папці input (`.pdf` без урахування регістру, за алфавітом; другий файл, що записав би той самий CSV, пропускається). Повертає `False`, якщо папка input непридатна або якийсь файл не оброблено; `main.py` робить з цього код виходу 1 |
| `process_file(pdf_file)` | Обробка одного PDF; `False` при помилці або якщо транзакцій не знайдено |
| `_report_control_sum(transactions, control_sum)` | Звіт про збіг контрольної суми та комісії |
| `_write_csv(pdf_file, transactions)` | Запис CSV з назвою PDF |

**Алгоритм `process_file()`:**
1. Відкриває PDF через `PDFReader.open()` (один раз)
2. Визначає банк через `BankDetector.detect_from_pdf(pdf)`
3. Отримує новий парсер через `BankDetector.get_parser()`
4. `parser.parse(pdf)` та `parser.extract_control_sum(pdf)`
5. Виводить попередження парсера (`parser.warnings`, напр. неузгоджена комісія)
6. Порівнює контрольну суму із сумою `net_amount` (зараховане; допуск `CONTROL_SUM_TOLERANCE` = 0.01). Розбіжність — лише попередження, CSV записується в будь-якому разі
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

Про хибні збіги див. [відому проблему #2](KNOWN_ISSUES.uk.md#2-банк-визначається-за-будь-яким-збігом-на-першій-сторінці-включно-з-контрагентами).

---

### `parser/core/statement.py`

**Клас:** `Transaction` (dataclass)

| Поле | Тип | Опис |
|------|-----|------|
| `date` | `datetime` | Дата та час транзакції |
| `gross_amount` | `float` | Сума до вирахування комісії |
| `commission` | `float` | Комісія (0 за замовчуванням) |
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
| `_make_transaction(date, net, details)` | `Transaction` з gross/комісією з опису, якщо вони узгоджені |

**Комісія (`_make_transaction`).** Сума у виписці — зараховане (net). В описі можуть бути сума до комісії та комісія:
- переказ від платіжної системи: `(сума X грн, комісія - Y грн)` — `TRANSFER_COMMISSION_PATTERN` (ПриватБанк, Монобанк)
- еквайринг Монобанку: `Загалом X грн. Комісія банку Y грн.` — `GROSS_AMOUNT_PATTERN` / `COMMISSION_PATTERN`

Приймаються лише якщо `X − Y == net` (±0.01), інакше `gross = net` і попередження. Попередження й тоді, коли комісію згадано в нерозпізнаному форматі. У PDF українські слова можуть містити латинську `i`; шаблони це враховують.

---

### `parser/core/table_parser.py`

**Клас:** `TableParser(BaseParser)` — Template Method для таблиць з рядком заголовка.

`parse()` обходить усі таблиці всіх сторінок. Для кожної таблиці:
1. Шукає перший рядок, для якого `_is_header(row_text)` істинне
2. `_detect_columns(row, columns)` повертає індекси колонок; знайдені зберігаються в `_saved_columns`
3. Таблиці без заголовка (наступні сторінки) використовують збережені індекси та парсяться з першого рядка
4. Якщо немає колонок з `REQUIRED_COLUMNS` (`date`, `amount`), таблиця пропускається
5. Для кожного рядка `_build_transaction(cells)` повертає `Transaction` або `None`

Через збережені колонки екземпляр парсера обслуговує лише один файл (`get_parser` завжди створює новий).

`_extract_tables(page)` додає горизонтальну лінію по низу вертикальних ліній, щоб рядок, розірваний розривом сторінки (без нижньої межі), не губився.

`_find_column_indices(row, keywords)` — пошук колонок за ключовими словами; для `amount` колонки з «валют» мають нижчий пріоритет.

---

### `parser/parsers/privatbank_parser.py`

**Клас:** `PrivatBankParser(BaseParser)`

- Розбирає **текст** сторінок, а не таблиці: `pdfplumber.extract_tables()` губив рядки на розривах сторінок (рядок над рамкою таблиці)
- Рядок транзакції: `<номер> DD.MM.YYYY <сума> <призначення>` (`PRIVATBANK_TXN_LINE_PATTERN`)
- Час `HH:MM` — з наступного рядка (`PRIVATBANK_TIME_PATTERN`)
- Контрольна сума: `разом за кредитом: XXX` (перша сторінка)
- **Комісія платіжної системи:** «Призначення платежу» збирається зі слів `extract_words()` між вертикальними лініями таблиці праворуч від суми (`_page_descriptions`), бо `extract_text()` перемішує колонки. Рядок транзакції починається словом-датою, за яким іде сума (`_row_anchors`). Далі — `_make_transaction`

---

### `parser/parsers/monobank_parser.py`

**Клас:** `MonobankParser(TableParser)`

- Заголовок: рядок з `дата`, `сума`, `операц`
- Колонки: `дата`+`час`, `сума`+`операц` (уникає «Сума у валюті …»), `деталі`
- Заголовок повністю визначає колонки таблиці (відсутні стають `None`)
- Контрольна сума: `Обіг за кредитом за період: XXX UAH` (перша сторінка)
- **Комісія:** з «Деталі операції» — еквайринг або переказ від платіжної системи, через `_make_transaction`

---

### `parser/parsers/novapay_parser.py`

**Клас:** `NovaPayParser(TableParser)`

- `DECIMAL_COMMA = True` — суми `1 234,56`
- `DATE_FORMATS`: спочатку `dd.mm.yyyy HH:MM` (без секунд), потім з секундами, потім лише дата
- Заголовок: `дата` + `сума`; колонки `Дата/час операції`, `Сума, UAH`
- Колонки, яких немає в заголовку, лишаються збереженими
- Контрольна сума: `Обороти по кредиту: XXX грн` (**остання** сторінка)
- Комісії немає

---

### `parser/parsers/generic_parser.py`

**Клас:** `GenericParser(BaseParser)` — fallback для невідомих банків.

- Сканує всі рядки таблиць, бере першу дату і першу суму в рядку
- Без контрольної суми
- Відома проблема: сума може бути взята з комірки з датою (`15.01.2024` → `15,01`), див. [#3](KNOWN_ISSUES.uk.md#3-загальний-парсер-бере-суму-з-дати-часу-або-номера-рядка)

---

### `parser/io/pdf_reader.py`

`PDFReader.open(pdf_path)` — context manager над `pdfplumber.open()`. Помилка відкриття загортається в `Exception("Cannot open PDF file ...")`; помилки всередині блоку `with` прокидаються без змін.

---

### `parser/io/csv_writer.py`

`CSVWriter.write(transactions, output_path)`

```
Час,Дата,Сума,Комісія,Сума з врахуванням комісії
07:15:00,05.08.2026,"250,00","0,00","250,00"
```

- Заголовки колонок українською навмисно: це колонки Книги обліку
- Рядки у **зворотному** порядку парсингу: хронологічно для виписок «від нових до старих». Перевірено лише для ПриватБанку ([#11](KNOWN_ISSUES.uk.md#11-порядок-рядків-у-csv-залежить-від-порядку-у-виписці-потенційно))
- UTF-8 з BOM (`utf-8-sig`) для Excel
- Кома як десятковий розділювач, тому поля сум у лапках

---

### `parser/utils/constants.py`

| Назва | Опис |
|-------|------|
| `DATE_PATTERN`, `DATETIME_PATTERN`, `DATETIME_PATTERN_SHORT` | Regex дат (з секундами / без) |
| `AMOUNT_PATTERN`, `WHITESPACE_PATTERN` | Regex суми та пробілів (з nbsp) |
| `GROSS_AMOUNT_PATTERN`, `COMMISSION_PATTERN` | Еквайринг Монобанку |
| `TRANSFER_COMMISSION_PATTERN` | Переказ від платіжної системи `(сума X грн, комісія - Y грн)` (ПриватБанк, Монобанк) |
| `*_CONTROL_SUM_PATTERN` | Контрольні суми банків |
| `PRIVATBANK_TXN_LINE_PATTERN`, `PRIVATBANK_TIME_PATTERN` | Текстовий розбір ПриватБанку |
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
| `to_float(number_str, decimal_comma=False)` | Число з тексту виписки (контрольна сума, деталі); `ValueError`, якщо не число |

---

### `parser/utils/dates.py`

`extract_datetime(value, formats=DEFAULT_FORMATS)` пробує формати `(regex, strptime)` по черзі. Готові формати: `DATETIME_FULL`, `DATETIME_SHORT`, `DATE_ONLY`; `DEFAULT_FORMATS = (DATETIME_FULL, DATE_ONLY)`.

---

### `parser/utils/formatters.py`

| Функція | Опис |
|---------|------|
| `format_date(date, fmt)` | `dd.mm.yyyy` |
| `format_time(date)` | `HH:MM:SS` |
| `format_amount(amount)` | Кома як десятковий розділювач |
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

## Архітектурні рішення

- **Фільтрація доходів під час розбору суми.** `validators.extract_and_validate_amount` повертає `None` для рядків, що починаються з мінуса (`-`, `−` U+2212, `–` U+2013) або взяті в дужки; парсери пропускають `None`. Ніколи не робіть `float()` з комірки напряму.
- **Контрольна сума — головний сигнал коректності.** Кожен відомий банк друкує обіг за кредитом; порівняння з сумою розпарсених net-сум ловить пропущені чи зайві рядки. Розбіжність — попередження, а не помилка: користувачу все одно потрібен CSV, щоб виправити вручну.
- **Декларативні парсери.** Відмінності банків — в атрибутах класу та `constants.py`, тож новий табличний банк — переважно конфігурація.
- **Текстовий розбір для ПриватБанку.** Розбір таблиць губив рядки на розривах сторінок; рядки тексту плюс координати слів до цього стійкі.
- **Монобанк і NovaPay навмисно по-різному обробляють заголовок.** Заголовок Монобанку замінює всі колонки, NovaPay зберігає попередні.
- **Новий парсер на кожен файл.** Табличні парсери зберігають стан колонок між сторінками.

---

## Як додати банк

### 1. Константи в `utils/constants.py`

```python
NEWBANK_KEYWORDS = ['новий банк', 'newbank']
NEWBANK_CONTROL_SUM_PATTERN = r'Оборот по кредиту:\s*([\d\s]+\.?\d*)'
```

### 2. Парсер у `parsers/newbank_parser.py`

Для таблиць із заголовком — наслідуйте `TableParser`:

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

Для іншого формату (наприклад, текстового, як ПриватБанк) — наслідуйте `BaseParser` і реалізуйте `parse(pdf)`.

### 3. Зареєструвати в `bank_detector.py`

```python
BANKS = (
    ...,
    ('newbank', constants.NEWBANK_KEYWORDS, NewBankParser),
)
```

### 4. Завершення

Експорт у `parsers/__init__.py`, тест у `tests/test_parsers.py`, перевірка на реальній виписці локально: має бути «Control sum matches».

---

## Тести

```bash
python -m unittest discover -s tests -t .
```

Тести використовують підробні сторінки (`tests/fakes.py` імітує `pages`, `extract_text()`, `extract_tables()`, `extract_words()`, `edges` pdfplumber) із синтетичними даними. Реальні виписки в репозиторій не додаються.

---

## Залежності

- **pdfplumber** — витягування тексту, таблиць і слів з PDF
- **Python 3.10+**
