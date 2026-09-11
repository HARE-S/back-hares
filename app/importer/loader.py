"""Cargador idempotente de alumnado (BE-05 / BE-06 / BE-07).

Creates and updates entities without duplicating any record. Identity is
always resolved by `external_id`, never by name.

BE-07 adds row-level tolerance: an invalid row is rejected and recorded in
the error details while the rest of the file keeps processing.
"""
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.importer.parser import parse_students_csv_collect
from app.repositories.student_repository import StudentRepository


def _empty_summary() -> Dict[str, Any]:
    return {
        "total": 0,
        "students_created": 0,
        "students_updated": 0,
        "students_omitted": 0,
        "centers_created": 0,
        "sections_created": 0,
        "enrollments_created": 0,
        "errors": 0,
        "error_details": [],
    }


class StudentImporter:
    """Loads students, centers, sections and enrollments idempotently."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = StudentRepository(session)

    def _merge(self, summary: Dict[str, Any], deltas: Dict[str, int]) -> None:
        for key, value in deltas.items():
            summary[key] += value

    def _import_row(self, row: Dict[str, Any]) -> Dict[str, int]:
        """Imports a single row inside a savepoint (BE-07 T-4).

        Each row runs in its own nested transaction so a failure in one row
        does not abort the rest of the file nor leave partial data behind.

        Returns the outcome deltas:
        {"students_created", "students_updated", "students_omitted",
         "centers_created", "sections_created", "enrollments_created"}
        """
        with self.session.begin_nested():
            center, center_created = self.repo.get_or_create_center(row["center"])
            student, student_created, student_changed = self.repo.upsert_student(
                external_id=row["student_id"],
                name=row["student_name"],
            )

            section_deltas = {"centers_created": 0, "sections_created": 0, "enrollments_created": 0}
            if center_created:
                section_deltas["centers_created"] += 1

            for section_name in row["sections"]:
                section, section_created = self.repo.get_or_create_section(center, section_name)
                if section_created:
                    section_deltas["sections_created"] += 1
                enrollment = self.repo.add_enrollment(student, section)
                if enrollment is not None:
                    section_deltas["enrollments_created"] += 1

            deltas = {
                "students_created": 1 if student_created else 0,
                "students_updated": 1 if (not student_created and student_changed) else 0,
                "students_omitted": 1 if (not student_created and not student_changed) else 0,
            }
            deltas.update(section_deltas)
            return deltas

    def import_students(
        self,
        rows: List[Dict[str, Any]],
        commit: bool = True,
        collect_errors: bool = True,
    ) -> Dict[str, Any]:
        """
        Imports the parsed rows creating missing masters and enrollments.

        Returns a summary with counters (BE-06) and, when collect_errors is
        True, the list of rejected rows with line, column and reason
        (BE-07 / BE-08 structure).
        """
        summary = _empty_summary()
        summary["total"] = len(rows)

        for row in rows:
            try:
                deltas = self._import_row(row)
            except Exception as exc:  # noqa: BLE001 - row must not kill the rest
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

    def import_from_csv(
        self,
        content: str,
        commit: bool = True,
        collect_errors: bool = True,
    ) -> Dict[str, Any]:
        """Parses CSV content and imports it (see import_students)."""
        rows, parse_errors = parse_students_csv_collect(content)
        summary = self.import_students(rows, commit=commit, collect_errors=collect_errors)

        for error in parse_errors:
            summary["errors"] += 1
            summary["total"] += 1
            if collect_errors:
                summary["error_details"].append(error)

        return summary