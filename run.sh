#!/usr/bin/env bash
# Launcher for macOS/Linux: installs dependencies if needed and runs the parser.
set -euo pipefail

# Run from the script's folder so input/ and output/ resolve correctly
cd "$(dirname "$0")"

echo "=== Bank statement parser ==="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Install Python 3.10+ and try again."
    exit 1
fi

# Install into the same interpreter that runs main.py
if ! python3 -c "import pdfplumber" &> /dev/null; then
    echo "Installing dependencies..."
    python3 -m pip install -r requirements.txt
    echo ""
fi

python3 main.py

echo ""
read -r -p "Press Enter to exit..."
