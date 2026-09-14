"""Cargador idempotente del catálogo inicial de libros (BE-17).

Identidad por título (insensible a mayúsculas), como el resto del catálogo:
si el libro ya existe no se duplica ni se pisa; se cuenta como `existing`.

BE-17 añade tolerancia por fila: una fila que falla en base de datos se
registra en `error_details` y el resto del fichero continúa (savepoint por
fila, patrón BE-07 T-4).
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.importer.books_parser import parse_books_xlsx
from app.models.book import Book
from app.repositories.book_repository import BookRepository

REVIEW_CSV_SUFFIX = "_revision.csv"


def _empty_summary() -> Dict[str, Any]:
    return {
        "total": 0,
        "processed": 0,
        "books_created": 0,
        "books_existing": 0,
        "headers_skipped": 0,
        "separators_skipped": 0,
        "errors": 0,
        "error_details": [],
        "review": [],
    }


class BookImporter:
    """Carga libros del catálogo inicial de forma idempotente."""

    def __init__(self, session: Session):
        self.session = session
        self.book_repo = BookRepository(session)

    def _merge(self, summary: Dict[str, Any], deltas: Dict[str, int]) -> None:
        for key, value in deltas.items():
            summary[key] += value

    def _import_row(self, row: Dict[str, Any]) -> Dict[str, int]:
        """Crea un libro dentro de un savepoint (patrón BE-07 T-4).

        Si el título ya existe se cuenta como `existing` y no se modifica.
        """
        with self.session.begin_nested():
            if self.book_repo.exists_by_title(row["titulo"]):
                return {"books_created": 0, "books_existing": 1}

            book = Book(
                book=row["titulo"],
                level=row["nivel"],
                copies_note=row.get("copies_note"),
                sessions_note=row.get("sessions_note"),
            )
            self.session.add(book)
            self.session.flush()
            return {"books_created": 1, "books_existing": 0}

    def import_rows(
        self,
        rows: List[Dict[str, Any]],
        commit: bool = True,
        collect_errors: bool = True,
    ) -> Dict[str, Any]:
        """Importa las filas ya parseadas acumulando errores sin abortar."""
        summary = _empty_summary()
        summary["total"] = len(rows)

        for row in rows:
            try:
                deltas = self._import_row(row)
            except Exception as exc:  # noqa: BLE001 - la fila no debe tumbar el resto
                summary["errors"] += 1
                if collect_errors:
                    summary["error_details"].append({
                        "line": row.get("line"),
                        "column": None,
                        "reason": str(exc),
                    })
                continue
            self._merge(summary, deltas)

        if commit:
            self.session.commit()

        return summary

    def import_from_xlsx(
        self,
        path,
        commit: bool = True,
        collect_errors: bool = True,
    ) -> Dict[str, Any]:
        """Parsea el Excel y carga las filas válidas en una sola transacción.

        Devuelve el resumen con los contadores y el listado de revisión
        manual (filas no interpretables) en `summary["review"]`.
        """
        parsed = parse_books_xlsx(path)
        summary = self.import_rows(
            parsed["rows"],
            commit=False,
            collect_errors=collect_errors,
        )
        summary["headers_skipped"] = parsed["headers_skipped"]
        summary["separators_skipped"] = parsed["separators_skipped"]
        summary["review"] = parsed["review"]
        summary["processed"] = summary["total"] - summary["errors"]

        if commit:
            self.session.commit()

        return summary