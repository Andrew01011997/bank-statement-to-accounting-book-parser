#!/usr/bin/env bash
# Launcher for macOS/Linux: installs dependencies if needed and runs the parser.
set -uo pipefail

# Pause before exit only in an interactive terminal (not in cron/CI/pipes)
pause() {
    if [ -t 0 ]; then
        echo ""
        read -r -p "Press Enter to exit..." || true
    fi
}

# Run from the script's folder so input/ and output/ resolve correctly
cd "$(dirname "$0")" || exit 1

echo "=== Bank statement parser ==="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Install Python 3.10+ and try again."
    pause
    exit 1
fi

# Install into the same interpreter that runs main.py
if ! python3 -c "import pdfplumber" &> /dev/null; then
    echo "Installing dependencies..."
    if ! python3 -m pip install -r requirements.txt; then
        echo "Error: failed to install dependencies."
        pause
        exit 1
    fi
    echo ""
fi

python3 main.py
status=$?

pause
exit "$status"
