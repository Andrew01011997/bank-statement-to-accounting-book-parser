@echo off
REM Скрипт запуску парсера для Windows

echo === Парсер банківських виписок ===
echo.

REM Перевірка наявності Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Помилка: Python не встановлено!
    echo Завантажте Python з https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Перевірка наявності залежностей
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Встановлення залежностей...
    pip install -r requirements.txt
    echo.
)

REM Запуск парсера
python main.py

echo.
pause
