# -*- coding: utf-8 -*-
"""Tests for the main.py entry point."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'


class ConsoleEncodingTest(unittest.TestCase):
    """docs/KNOWN_ISSUES.md #1: non-UTF-8 console output must not break the program."""

    def test_non_utf8_redirected_output_does_not_crash(self):
        env = dict(os.environ, PYTHONIOENCODING='cp1251', PYTHONUTF8='0')
        with tempfile.TemporaryDirectory() as cwd:
            # No input folder -> prints "❌ Folder input does not exist!",
            # and ❌ cannot be encoded in cp1251
            result = subprocess.run(
                [sys.executable, str(MAIN_PY)],
                cwd=cwd, env=env, capture_output=True,
            )

        # Missing input folder is reported with exit code 1, not a crash
        self.assertEqual(result.returncode, 1, result.stderr.decode('utf-8', 'replace'))
        self.assertNotIn(b'Traceback', result.stderr)
        self.assertNotIn(b'UnicodeEncodeError', result.stderr)
        self.assertIn('❌'.encode('utf-8'), result.stdout)


if __name__ == '__main__':
    unittest.main()
