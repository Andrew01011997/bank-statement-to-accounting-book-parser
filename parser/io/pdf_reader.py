# -*- coding: utf-8 -*-
"""
PDF file wrapper.
"""

from contextlib import contextmanager
import pdfplumber


class PDFReader:
    """PDF file wrapper."""

    @staticmethod
    @contextmanager
    def open(pdf_path: str):
        """
        Opens a PDF file as a context manager.

        Args:
            pdf_path: Path to the PDF file

        Yields:
            pdfplumber PDF object

        Raises:
            Exception: If the file cannot be opened
        """
        try:
            pdf = pdfplumber.open(pdf_path)
        except Exception as e:
            raise Exception(f"Cannot open PDF file {pdf_path}: {e}") from e

        try:
            yield pdf
        finally:
            pdf.close()
