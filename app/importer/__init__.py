"""Importador de datos maestros (Bloque A).

Punto de entrada del módulo de importación. Reutiliza `services` y
`repositories` del backend: parser + loader idempotente de alumnado.
"""
from app.importer.loader import StudentImporter
from app.importer.parser import parse_students_csv

__all__ = ["StudentImporter", "parse_students_csv"]