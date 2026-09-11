"""Cargador idempotente de alumnado (BE-05 / BE-07 embryonic).

Highlights created and updated entities without duplicating any record.
Identity is always resolved by `external_id`, never by name.
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.importer.parser import parse_students_csv
from app.repositories.student_repository import StudentRepository


class StudentImporter:
    """Loads students, centers, sections and enrollments idempotently."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = StudentRepository(session)

    def import_students(
        self,
        rows: List[Dict[str, Any]],
        commit: bool = True,
    ) -> Dict[str, int]:
        """
        Imports the parsed rows creating missing masters and enrollments.

        Returns a summary with counters: total, students_created,
        students_updated, students_omitted, centers_created,
        sections_created, enrollments_created and errors (BE-06).
        """
        summary = {
            "total": len(rows),
            "students_created": 0,
            "students_updated": 0,
            "students_omitted": 0,
            "centers_created": 0,
            "sections_created": 0,
            "enrollments_created": 0,
            "errors": 0,
        }

        for row in rows:
            center, center_created = self.repo.get_or_create_center(row["center"])
            if center_created:
                summary["centers_created"] += 1

            student, student_created, student_changed = self.repo.upsert_student(
                external_id=row["student_id"],
                name=row["student_name"],
            )
            if student_created:
                summary["students_created"] += 1
            elif student_changed:
                summary["students_updated"] += 1
            else:
                summary["students_omitted"] += 1

            for section_name in row["sections"]:
                section, section_created = self.repo.get_or_create_section(center, section_name)
                if section_created:
                    summary["sections_created"] += 1

                enrollment = self.repo.add_enrollment(student, section)
                if enrollment is not None:
                    summary["enrollments_created"] += 1

        if commit:
            self.session.commit()

        return summary

    def import_from_csv(
        self,
        content: str,
        commit: bool = True,
    ) -> Dict[str, int]:
        """Parses CSV content and imports it (see import_students)."""
        rows = parse_students_csv(content)
        return self.import_students(rows, commit=commit)