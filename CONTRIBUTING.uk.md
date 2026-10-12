# Як долучитися

🇬🇧 [English version](CONTRIBUTING.md)

Дякуємо за допомогу! Повідомлення про помилки, нові формати банків і виправлення — вітаються.

## Головне правило: жодних реальних даних

Ніколи не комітьте й не додавайте реальні виписки, CSV чи скриншоти з реальними даними. Описуйте макети з вигаданими значеннями. Див. [SECURITY.uk.md](SECURITY.uk.md).

## Налаштування

```bash
git clone https://github.com/Andrew01011997/bank-statement-to-accounting-book-parser.git
cd bank-statement-to-accounting-book-parser
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

## Перед pull request

```bash
python -m unittest discover -s tests -t .   # усі тести мають проходити
ruff check .                                # без помилок лінтера
```

Якщо змінювали парсер, також запустіть `python main.py` на реальній виписці **локально** і перевірте «Control sum matches». Не комітьте цю виписку.

## Домовленості

- **Мова:** код, коментарі, docstring, вивід у консоль і повідомлення комітів — англійською. Ключові слова й regex, що збігаються з текстом виписок, лишаються українськими, як і заголовки CSV (це назви колонок Книги обліку).
- **Конфігурація замість коду:** regex, ключові слова та межі — у `parser/utils/constants.py`.
- **Суми:** ніколи не робіть `float()` з комірки напряму; використовуйте `BaseParser._extract_amount`, який також відфільтровує витрати.
- **Тести:** кожна зміна — з тестом на синтетичних сторінках (`tests/fakes.py`). Відому, але не виправлену помилку можна зафіксувати через `@unittest.expectedFailure`.
- **Документація:** оновлюйте `CHANGELOG.md` і `CHANGELOG.uk.md`; виправляючи відому проблему — обидва файли `docs/KNOWN_ISSUES*.md`. Англійська та українська версії документа мають збігатися.
- **Коміти:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Як додати банк

Див. [docs/ARCHITECTURE.uk.md → Як додати банк](docs/ARCHITECTURE.uk.md#як-додати-банк).
