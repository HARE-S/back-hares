"""Importador de datos maestros (Bloque A).

Punto de entrada del módulo de importación. Reutiliza `services` y
`repositories` del backend: parser + loader idempotente de alumnado y el
cargador del catálogo inicial de libros.
"""
from app.importer.books_loader import BookImporter
from app.importer.books_parser import normalize_book_level, parse_books_xlsx
from app.importer.loader import StudentImporter
from app.importer.parser import parse_students_csv, parse_students_csv_collect

__all__ = [
    "StudentImporter",
    "parse_students_csv",
    "parse_students_csv_collect",
    "BookImporter",
    "parse_books_xlsx",
    "normalize_book_level",
]