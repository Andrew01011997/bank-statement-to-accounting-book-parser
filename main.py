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

import sys

from parser import StatementParserManager


def configure_console() -> None:
    """
    Перемикає stdout/stderr на UTF-8.

    Без цього вивід у файл, конвеєр чи планувальник на Windows кодується
    в cp1251/cp1252, і print з ✓/⚠️/ℹ️/❌ кидає UnicodeEncodeError —
    обробка файлу переривається до запису CSV.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            # Потік замінено чи закрито (напр. IDE, pythonw) — лишаємо як є
            pass


def main():
    """Головна функція."""
    configure_console()
    manager = StatementParserManager()
    manager.run()


if __name__ == '__main__':
    main()
