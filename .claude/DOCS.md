# Документація проекту Bank Statement to Accounting Book Parser

Парсер банківських виписок PDF для автоматичної генерації Книги обліку доходів.

---

## Зміст

1. [Огляд архітектури](#огляд-архітектури)
2. [Структура файлів](#структура-файлів)
3. [Детальний опис модулів](#детальний-опис-модулів)
4. [Потік даних](#потік-даних)
5. [Як додати новий банк](#як-додати-новий-банк)

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
│  • Координує весь процес                                     │
│  • Знаходить PDF у input/                                    │
│  • Викликає BankDetector → Parser → CSVWriter                │
│  • Валідує контрольні суми                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ BankDetector│   │  PDFReader  │   │  CSVWriter  │
│   (Factory) │   │    (I/O)    │   │    (I/O)    │
└──────┬──────┘   └─────────────┘   └─────────────┘
       │
       ▼ (створює)
┌─────────────────────────────────────────────────────────────┐
│                      BaseParser (ABC)                        │
│                                                              │
│  ├── MonobankParser                                          │
│  ├── PrivatBankParser                                        │
│  ├── NovaPayParser                                           │
│  └── GenericParser                                           │
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
│
└── parser/                 # Головний модуль
    ├── __init__.py         # Експорт публічного API
    ├── manager.py          # Координатор процесу
    ├── bank_detector.py    # Factory для парсерів
    │
    ├── core/               # Базові класи
    │   ├── __init__.py
    │   ├── base_parser.py  # Абстрактний парсер
    │   └── statement.py    # Модель Transaction
    │
    ├── parsers/            # Конкретні парсери
    │   ├── __init__.py
    │   ├── monobank_parser.py
    │   ├── privatbank_parser.py
    │   ├── novapay_parser.py
    │   └── generic_parser.py
    │
    ├── io/                 # Читання/запис файлів
    │   ├── __init__.py
    │   ├── pdf_reader.py   # Обгортка pdfplumber
    │   └── csv_writer.py   # Генерація CSV
    │
    └── utils/              # Допоміжні утиліти
        ├── __init__.py
        ├── constants.py    # Regex, ключові слова
        ├── validators.py   # Валідація сум
        ├── formatters.py   # Форматування дат/сум
        └── text_parser.py  # Парсинг тексту (fallback)
```

---

## Детальний опис модулів

### `main.py`

**Призначення:** Точка входу в програму.

**Що робить:**
- Імпортує `StatementParserManager`
- Викликає `manager.run()`

```python
from parser import StatementParserManager

def main():
    manager = StatementParserManager()
    manager.run()
```

---

### `parser/__init__.py`

**Призначення:** Публічний API модуля.

**Експортує:**
- `StatementParserManager` - головний клас
- `Transaction` - модель даних

---

### `parser/manager.py`

**Призначення:** Координатор всього процесу парсингу.

**Клас:** `StatementParserManager`

**Методи:**

| Метод | Опис |
|-------|------|
| `__init__(input_dir, output_dir)` | Ініціалізація з папками input/output |
| `run()` | Запуск парсингу всіх PDF у папці input |
| `process_file(pdf_file)` | Обробка одного PDF файлу |

**Алгоритм `process_file()`:**
1. Визначає тип банку через `BankDetector.detect()`
2. Отримує парсер через `BankDetector.get_parser()`
3. Відкриває PDF через `PDFReader.open()`
4. Парсить транзакції через `parser.parse(pdf)`
5. Витягує контрольну суму через `parser.extract_control_sum(pdf)`
6. Валідує суму транзакцій vs контрольна сума
7. Записує CSV через `CSVWriter.write()`

---

### `parser/bank_detector.py`

**Призначення:** Factory Pattern для визначення банку та створення парсера.

**Клас:** `BankDetector`

**Методи:**

| Метод | Опис |
|-------|------|
| `detect(pdf_path) -> str` | Визначає тип банку за вмістом PDF |
| `get_parser(bank_type) -> BaseParser` | Створює відповідний парсер |

**Логіка визначення:**
- Читає текст першої сторінки PDF
- Шукає ключові слова з `constants.py`:
  - `monobank`, `універсал банк` → MonobankParser
  - `приватбанк` → PrivatBankParser
  - `novapay`, `новапей`, `935871` → NovaPayParser
  - інше → GenericParser

---

### `parser/core/statement.py`

**Призначення:** Модель даних для транзакції.

**Клас:** `Transaction` (dataclass)

**Поля:**

| Поле | Тип | Опис |
|------|-----|------|
| `date` | `datetime` | Дата та час транзакції |
| `amount` | `float` | Сума (тільки позитивні!) |

---

### `parser/core/base_parser.py`

**Призначення:** Абстрактний базовий клас для всіх парсерів.

**Клас:** `BaseParser` (ABC)

**Абстрактні методи:**
- `parse(pdf) -> List[Transaction]` - реалізується в підкласах

**Конкретні методи:**

| Метод | Опис |
|-------|------|
| `_extract_date(date_str)` | Витягує datetime з рядка |
| `_extract_amount(amount_str)` | Витягує та валідує суму |
| `_find_column_indices(row, keywords)` | Знаходить індекси колонок |
| `extract_control_sum(pdf)` | Витягує контрольну суму (перевизначається) |

**Важливо:** `_extract_amount()` використовує `validators.extract_and_validate_amount()`, який фільтрує негативні суми!

---

### `parser/parsers/privatbank_parser.py`

**Призначення:** Парсер для виписок ПриватБанку.

**Клас:** `PrivatBankParser` extends `BaseParser`

**Особливості:**
- Шукає колонки: `дата час/операц`, `сума`
- Контрольна сума: `разом за кредитом: XXX`
- Зберігає індекси колонок між сторінками

---

### `parser/parsers/monobank_parser.py`

**Призначення:** Парсер для виписок Монобанку.

**Клас:** `MonobankParser` extends `BaseParser`

**Особливості:**
- Шукає колонки: `дата час`, `сума операц`
- Контрольна сума: `Обіг за кредитом за період: XXX UAH`
- Уникає колонки "Сума у валюті рахунку"

---

### `parser/parsers/novapay_parser.py`

**Призначення:** Парсер для виписок NovaPay (небанківський платіжний сервіс).

**Клас:** `NovaPayParser` extends `BaseParser`

**Методи:**

| Метод | Опис |
|-------|------|
| `_extract_date_novapay(date_str)` | Парсинг дати без секунд (`dd.mm.yyyy HH:MM`) |
| `_extract_amount_novapay(amount_str)` | Парсинг суми з комою (`2 267,80`) |
| `extract_control_sum(pdf)` | Витягує "Обороти по кредиту" з останньої сторінки |
| `parse(pdf)` | Основний метод парсингу |

**Особливості:**
- Формат дати: `26.07.2025 20:51` (без секунд)
- Формат суми: `2 267,80` (кома як десятковий, пробіл як тисячний)
- Контрольна сума: `Обороти по кредиту: XXX грн`
- Шукає колонки: `Дата/час операц`, `Сума, UAH`

---

### `parser/parsers/generic_parser.py`

**Призначення:** Fallback парсер для невідомих форматів.

**Клас:** `GenericParser` extends `BaseParser`

**Особливості:**
- Сканує всі комірки таблиць
- Шукає дату та суму в будь-якій позиції
- Не витягує контрольну суму

---

### `parser/io/pdf_reader.py`

**Призначення:** Обгортка для безпечного читання PDF.

**Клас:** `PDFReader`

**Методи:**

| Метод | Опис |
|-------|------|
| `open(pdf_path)` | Context manager для відкриття PDF |

**Використання:**
```python
with PDFReader.open('file.pdf') as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
```

---

### `parser/io/csv_writer.py`

**Призначення:** Генерація CSV файлів.

**Клас:** `CSVWriter`

**Методи:**

| Метод | Опис |
|-------|------|
| `write(transactions, output_path)` | Записує транзакції у CSV |

**Формат CSV:**
```
Час,Дата,Сума
12:30:45,15.01.2024,1234,56
```

**Особливості:**
- Транзакції у **зворотному порядку** (reversed)
- Кодування UTF-8 з BOM
- Сума в європейському форматі (кома)

---

### `parser/utils/constants.py`

**Призначення:** Всі константи та конфігурація.

**Константи:**

| Назва | Опис |
|-------|------|
| `DATE_PATTERN` | Regex для дати `dd.mm.yyyy` |
| `TIME_PATTERN` | Regex для часу `hh:mm:ss` |
| `TIME_PATTERN_SHORT` | Regex для часу без секунд `hh:mm` |
| `DATETIME_PATTERN` | Regex для дати+часу з секундами |
| `DATETIME_PATTERN_SHORT` | Regex для дати+часу без секунд (NovaPay) |
| `AMOUNT_PATTERN` | Regex для суми з крапкою |
| `AMOUNT_PATTERN_COMMA` | Regex для суми з комою (NovaPay) |
| `WHITESPACE_PATTERN` | Regex для пробілів (включаючи nbsp) |
| `MIN_AMOUNT` / `MAX_AMOUNT` | Межі валідних сум |
| `MONOBANK_KEYWORDS` | Ключові слова Монобанку |
| `PRIVATBANK_KEYWORDS` | Ключові слова ПриватБанку |
| `NOVAPAY_KEYWORDS` | Ключові слова NovaPay |
| `MINUS_SIGNS` | Різні Unicode символи мінуса |
| `CSV_ENCODING` | `utf-8-sig` |

---

### `parser/utils/validators.py`

**Призначення:** Валідація та фільтрація сум.

**Функції:**

| Функція | Опис |
|---------|------|
| `is_negative_amount(amount_str)` | Перевіряє знак мінуса |
| `is_valid_amount(amount)` | Перевіряє межі суми |
| `extract_and_validate_amount(amount_str)` | Комплексна валідація |

**Важливо:** `extract_and_validate_amount()` повертає `None` для:
- Негативних сум (витрат)
- Сум поза межами MIN/MAX
- Невалідних рядків

---

### `parser/utils/formatters.py`

**Призначення:** Форматування для виводу.

**Функції:**

| Функція | Опис |
|---------|------|
| `format_date(date, fmt)` | Форматування дати |
| `format_time(date)` | Форматування часу |
| `format_amount(amount)` | Європейський формат (кома) |
| `format_csv_row(date, amount)` | Генерує рядок CSV |

---

### `parser/utils/text_parser.py`

**Призначення:** Fallback парсинг з тексту PDF (не таблиць).

**Клас:** `TextTransactionParser`

**Методи:**

| Метод | Опис |
|-------|------|
| `extract_transactions_from_text(text)` | Витягує транзакції з тексту |
| `deduplicate_transactions(table, text)` | Знаходить унікальні з тексту |

**Примітка:** Цей клас використовується як fallback, коли таблиці PDF не розпізнаються коректно.

---

## Потік даних

```
input/statement.pdf
        │
        ▼
┌───────────────────┐
│  BankDetector     │ ← Визначає: monobank | privatbank | novapay | unknown
└─────────┬─────────┘
          │
          ▼ (створює)
┌───────────────────┐
│  Parser           │ ← MonobankParser / PrivatBankParser / NovaPayParser / GenericParser
└─────────┬─────────┘
          │
          ▼ (парсить)
┌───────────────────┐
│ List[Transaction] │ ← Тільки позитивні суми (доходи)
│  date + amount    │
└─────────┬─────────┘
          │
          ▼ (записує)
┌───────────────────┐
│    CSVWriter      │
└─────────┬─────────┘
          │
          ▼
output/statement.csv
```

---

## Як додати новий банк

### 1. Додати ключові слова в `utils/constants.py`:

```python
NEWBANK_KEYWORDS = ['новий банк', 'newbank']
```

### 2. Створити парсер в `parsers/newbank_parser.py`:

```python
from ..core.base_parser import BaseParser
from ..core.statement import Transaction

class NewBankParser(BaseParser):
    def extract_control_sum(self, pdf):
        # Витягти контрольну суму з PDF
        pass

    def parse(self, pdf):
        transactions = []
        # Логіка парсингу таблиць PDF
        return transactions
```

### 3. Зареєструвати в `bank_detector.py`:

```python
from .parsers.newbank_parser import NewBankParser

# В detect():
if any(keyword in text_lower for keyword in constants.NEWBANK_KEYWORDS):
    return 'newbank'

# В get_parser():
parsers = {
    'monobank': MonobankParser,
    'privatbank': PrivatBankParser,
    'novapay': NovaPayParser,
    'newbank': NewBankParser,  # ← додати
    'unknown': GenericParser
}
```

### 4. Додати експорт в `parsers/__init__.py`:

```python
from .newbank_parser import NewBankParser
__all__ = [..., 'NewBankParser']
```

---

## Залежності

- **pdfplumber** - парсинг PDF та витягування таблиць
- **Python 3.7+** - dataclasses, type hints
