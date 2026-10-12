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



class ExitCodeTest(unittest.TestCase):
    def run_main(self, cwd):
        return subprocess.run([sys.executable, str(MAIN_PY)], cwd=cwd, capture_output=True,
                              env=dict(os.environ, PYTHONIOENCODING='utf-8'))

    def test_output_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as cwd:
            Path(cwd, 'output').touch()
            result = self.run_main(cwd)

        self.assertEqual(result.returncode, 1)
        self.assertNotIn(b'Traceback', result.stderr)
        self.assertIn('Cannot create the output folder'.encode(), result.stdout)

    def test_empty_input_folder_exits_0(self):
        with tempfile.TemporaryDirectory() as cwd:
            Path(cwd, 'input').mkdir()
            result = self.run_main(cwd)

        self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', 'replace'))


if __name__ == '__main__':
    unittest.main()
