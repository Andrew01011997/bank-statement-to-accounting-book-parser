@echo off
REM Launcher for Windows: installs dependencies if needed and runs the parser.

REM Run from the script folder so input\ and output\ resolve correctly
cd /d "%~dp0"

echo === Bank statement parser ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Download Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install into the same interpreter that runs main.py
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    echo.
)

python main.py

echo.
pause
