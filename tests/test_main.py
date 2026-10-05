# -*- coding: utf-8 -*-
"""Тести точки входу main.py."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'


class ConsoleEncodingTest(unittest.TestCase):
    """BUGS.md P1 #1: вивід не в UTF-8 консоль не повинен ламати програму."""

    def test_non_utf8_redirected_output_does_not_crash(self):
        env = dict(os.environ, PYTHONIOENCODING='cp1251', PYTHONUTF8='0')
        with tempfile.TemporaryDirectory() as cwd:
            # Папки input немає -> друкується "❌ Папка input не існує!",
            # символ ❌ не кодується в cp1251
            result = subprocess.run(
                [sys.executable, str(MAIN_PY)],
                cwd=cwd, env=env, capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))
        self.assertNotIn(b'UnicodeEncodeError', result.stderr)
        self.assertIn('❌'.encode('utf-8'), result.stdout)


if __name__ == '__main__':
    unittest.main()
