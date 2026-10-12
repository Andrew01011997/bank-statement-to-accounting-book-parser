@echo off
REM Launcher for Windows: installs dependencies if needed and runs the parser.
REM Pass --no-pause for unattended runs (Task Scheduler, scripts) so it never waits for a key.

REM Run from the script folder so input\ and output\ resolve correctly
cd /d "%~dp0"

set "PAUSE_AT_END=1"
if /i "%~1"=="--no-pause" set "PAUSE_AT_END="

echo === Bank statement parser ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Download Python 3.10+ from https://www.python.org/downloads/
    if defined PAUSE_AT_END pause
    exit /b 1
)

REM Install into the same interpreter that runs main.py
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: failed to install dependencies.
        if defined PAUSE_AT_END pause
        exit /b 1
    )
    echo.
)

python main.py
set "STATUS=%ERRORLEVEL%"

echo.
if defined PAUSE_AT_END pause
exit /b %STATUS%
