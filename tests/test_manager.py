# -*- coding: utf-8 -*-
"""StatementParserManager tests."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from parser.manager import StatementParserManager


def run_quietly(manager):
    """Runs the manager, returning (result, stdout)."""
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(io.StringIO()):
        result = manager.run()
    return result, out.getvalue()


class InputFolderTest(unittest.TestCase):
    """docs/KNOWN_ISSUES.md #13: *.PDF found on every OS, same order on every OS, no crashes."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.input_dir = self.tmp / 'input'
        self.addCleanup(self._tmp.cleanup)

    def manager(self):
        return StatementParserManager(self.input_dir, self.tmp / 'output')

    def test_finds_pdfs_case_insensitively_in_name_order(self):
        self.input_dir.mkdir()
        for name in ('c.pdf', 'B.pdf', 'a.PDF', 'notes.txt'):
            (self.input_dir / name).touch()
        (self.input_dir / 'nested.pdf').mkdir()

        manager = self.manager()
        with mock.patch.object(manager, 'process_file', return_value=True) as process_file:
            result, _ = run_quietly(manager)

        self.assertTrue(result)
        self.assertEqual([c.args[0].name for c in process_file.call_args_list], ['a.PDF', 'B.pdf', 'c.pdf'])

    def test_same_csv_name_is_not_overwritten(self):
        # Both names can coexist only on a case-sensitive file system, so the listing is mocked
        self.input_dir.mkdir()
        files = [self.input_dir / 'statement.pdf', self.input_dir / 'Statement.PDF']

        manager = self.manager()
        with mock.patch.object(Path, 'iterdir', return_value=iter(files)), \
                mock.patch.object(Path, 'is_file', return_value=True), \
                mock.patch.object(manager, 'process_file', return_value=True) as process_file:
            result, out = run_quietly(manager)

        self.assertFalse(result)
        self.assertEqual(process_file.call_count, 1)
        self.assertIn('would overwrite', out)

    def test_missing_input_folder(self):
        result, out = run_quietly(self.manager())
        self.assertFalse(result)
        self.assertIn('does not exist', out)

    def test_input_path_is_a_file(self):
        self.input_dir.touch()
        result, out = run_quietly(self.manager())
        self.assertFalse(result)
        self.assertIn('is not a folder', out)

    def test_unreadable_input_folder(self):
        self.input_dir.mkdir()
        manager = self.manager()
        with mock.patch.object(Path, 'iterdir', side_effect=PermissionError('denied')):
            result, out = run_quietly(manager)

        self.assertFalse(result)
        self.assertIn('Cannot read folder', out)

    def test_empty_input_folder_is_not_an_error(self):
        self.input_dir.mkdir()
        result, out = run_quietly(self.manager())
        self.assertTrue(result)
        self.assertIn('nothing to do', out)


class ResultTest(unittest.TestCase):
    def test_broken_pdfs_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp, 'input')
            input_dir.mkdir()
            Path(input_dir, 'a.pdf').write_bytes(b'not a pdf')

            result, out = run_quietly(StatementParserManager(input_dir, Path(tmp, 'output')))

        self.assertFalse(result)
        self.assertIn('1 of 1 file(s) failed', out)

    def test_no_transactions_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = StatementParserManager(Path(tmp, 'input'), Path(tmp, 'output'))
            with redirect_stdout(io.StringIO()):
                self.assertFalse(manager._write_csv(Path('a.pdf'), []))


if __name__ == '__main__':
    unittest.main()
