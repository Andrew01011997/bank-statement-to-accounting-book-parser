# -*- coding: utf-8 -*-
"""
Обгортка для роботи з PDF файлами
"""

from contextlib import contextmanager
import pdfplumber


class PDFReader:
    """Обгортка для роботи з PDF файлами."""

    @staticmethod
    @contextmanager
    def open(pdf_path: str):
        """
        Безпечне відкриття PDF файлу з контекстним менеджером.

        Args:
            pdf_path: Шлях до PDF файлу

        Yields:
            PDF об'єкт

        Raises:
            Exception: Якщо помилка при відкритті файлу
        """
        pdf = None
        try:
            pdf = pdfplumber.open(pdf_path)
            yield pdf
        except Exception as e:
            raise Exception(f"Помилка відкриття PDF файлу {pdf_path}: {e}")
        finally:
            if pdf:
                pdf.close()
