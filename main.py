#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер банківських виписок для створення Книги обліку доходів

Використання:
    python3 main.py

    або через скрипти:
    ./run.sh (Linux/Mac)
    run.bat (Windows)
"""

from parser import StatementParserManager


def main():
    """Головна функція."""
    manager = StatementParserManager()
    manager.run()


if __name__ == '__main__':
    main()
