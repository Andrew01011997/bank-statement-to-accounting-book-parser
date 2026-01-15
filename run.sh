#!/bin/bash
# Скрипт запуску парсера для macOS/Linux

echo "=== Парсер банківських виписок ==="
echo ""

# Перевірка наявності Python
if ! command -v python3 &> /dev/null; then
    echo "Помилка: Python 3 не встановлено!"
    echo "Встановіть Python 3 перед використанням."
    exit 1
fi

# Перевірка наявності залежностей
if ! python3 -c "import pdfplumber" &> /dev/null; then
    echo "Встановлення залежностей..."
    pip3 install -r requirements.txt
    echo ""
fi

# Запуск парсера
python3 main.py

echo ""
echo "Натисніть Enter для виходу..."
read
