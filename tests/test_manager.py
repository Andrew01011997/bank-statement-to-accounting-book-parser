# -*- coding: utf-8 -*-
"""StatementParserManager tests."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from parser.manager import StatementParserManager


class FileDiscoveryTest(unittest.TestCase):
    """docs/KNOWN_ISSUES.md #13: *.PDF found on every OS, same processing order on every OS."""

    def test_finds_pdfs_case_insensitively_in_name_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp, 'input')
            input_dir.mkdir()
            for name in ('c.pdf', 'B.pdf', 'a.PDF', 'notes.txt'):
                Path(input_dir, name).touch()
            Path(input_dir, 'nested.pdf').mkdir()

            manager = StatementParserManager(input_dir, Path(tmp, 'output'))
            with mock.patch.object(manager, 'process_file') as process_file, \
                    redirect_stdout(io.StringIO()):
                manager.run()

        self.assertEqual([c.args[0].name for c in process_file.call_args_list], ['a.PDF', 'B.pdf', 'c.pdf'])


    def test_input_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'input').touch()
            manager = StatementParserManager(Path(tmp, 'input'), Path(tmp, 'output'))
            out = io.StringIO()
            with redirect_stdout(out):
                manager.run()

        self.assertIn('is not a folder', out.getvalue())


    def test_unreadable_input_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'input').mkdir()
            manager = StatementParserManager(Path(tmp, 'input'), Path(tmp, 'output'))
            out = io.StringIO()
            with mock.patch.object(Path, 'iterdir', side_effect=PermissionError('denied')), \
                    redirect_stdout(out):
                failures = manager.run()

        self.assertEqual(failures, 1)
        self.assertIn('Cannot read folder', out.getvalue())


class FailureCountTest(unittest.TestCase):
    def test_failed_files_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp, 'input')
            input_dir.mkdir()
            for name in ('a.pdf', 'b.pdf'):
                Path(input_dir, name).write_bytes(b'not a pdf')

            manager = StatementParserManager(input_dir, Path(tmp, 'output'))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                failures = manager.run()

        self.assertEqual(failures, 2)


if __name__ == '__main__':
    unittest.main()
