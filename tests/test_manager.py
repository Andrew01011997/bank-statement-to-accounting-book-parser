# -*- coding: utf-8 -*-
"""StatementParserManager tests."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from parser.manager import StatementParserManager


class FileDiscoveryTest(unittest.TestCase):
    """docs/KNOWN_ISSUES.md #13: *.PDF found on every OS, stable processing order."""

    def test_finds_pdfs_case_insensitively_in_sorted_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp, 'input')
            input_dir.mkdir()
            for name in ('b.pdf', 'a.PDF', 'notes.txt'):
                Path(input_dir, name).touch()
            Path(input_dir, 'nested.pdf').mkdir()

            manager = StatementParserManager(input_dir, Path(tmp, 'output'))
            with mock.patch.object(manager, 'process_file') as process_file, \
                    redirect_stdout(io.StringIO()):
                manager.run()

        self.assertEqual([c.args[0].name for c in process_file.call_args_list], ['a.PDF', 'b.pdf'])


if __name__ == '__main__':
    unittest.main()
