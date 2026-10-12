#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bank statement parser that builds the FOP income ledger ("Книга обліку доходів").

Usage:
    python3 main.py

    or via the launcher scripts:
    ./run.sh (Linux/macOS)
    run.bat (Windows)
"""

import sys

from parser import StatementParserManager


def configure_console() -> None:
    """
    Switches stdout/stderr to UTF-8.

    Without this, output redirected to a file, a pipe or a scheduler on Windows
    is encoded as cp1251/cp1252, and printing ✓/⚠️/ℹ️/❌ raises UnicodeEncodeError,
    aborting the file before its CSV is written.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            # Stream replaced or closed (e.g. an IDE, pythonw) - leave it as is
            pass


def main() -> int:
    """Entry point. Returns the process exit code: 0 on success, 1 if anything failed."""
    configure_console()
    manager = StatementParserManager()
    return 1 if manager.run() else 0


if __name__ == '__main__':
    sys.exit(main())
