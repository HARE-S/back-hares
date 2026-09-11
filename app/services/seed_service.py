"""Servicio de carga de datos de prueba anónimos (BE-05).

Orquesta el poblamiento de la base de datos migrada y vacía con:
- 28 alumnos anónimos desde `import_data.csv` (via app.importer).
- Las 34 pruebas de `tests.csv` (reutilizando CatalogService, BE-12).
- Un catálogo mínimo de libros.
- Resultados sintéticos: al menos 3 por alumno, en fechas distintas y con
  tendencia variada para permitir calcular evolución.

El comando es idempotente: comprueba existencia antes de crear, de forma que
ejecutarlo dos veces no duplica ningún registro.
"""
import datetime
import random
from pathlib import Path
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from app.importer import StudentImporter
from app.importer.parser import parse_students_csv
from app.repositories.book_repository import BookRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.test_repository import TestRepository
from app.services.catalog_service import CatalogService


class SeedService:
    """Loads anonymous test data into the database (BE-05)."""

    MIN_RESULTS_PER_STUDENT = 3
    RESULTS_BASE_DATE = datetime.date(2026, 9, 1)
    RESULTS_DAY_SPACING = 14
    DEFAULT_STUDENTS_CSV = "data/seeds/import_data.csv"
    DEFAULT_TESTS_CSV = "data/seeds/tests.csv"

    MINIMAL_BOOKS: Tuple[Tuple[str, str], ...] = (
        ("El pirata valiente", "0"),
        ("Aventuras en el mar", "0-I"),
        ("Misterios de invierno", "I"),
        ("Historias del bosque", "I/II"),
        ("El viaje de las estrellas", "II"),
    )

    def __init__(self, session: Session):
        self.session = session
        self.catalog = CatalogService(session)
        self.importer = StudentImporter(session)
        self.student_repo = StudentRepository(session)
        self.test_repo = TestRepository(session)
        self.book_repo = BookRepository(session)
        self.result_repo = ResultRepository(session)

    def seed(
        self,
        students_csv_path: str = DEFAULT_STUDENTS_CSV,
        tests_csv_path: str = DEFAULT_TESTS_CSV,
    ) -> Dict[str, Any]:
        """Runs the full anonymous data load (BE-05 scenarios 1 and 2)."""
        students_content = Path(students_csv_path).read_text(encoding="utf-8")
        rows = parse_students_csv(students_content)

        summary: Dict[str, Any] = {}
        summary["tests"] = self.catalog.import_tests_from_csv(tests_csv_path)
        summary["students"] = self.importer.import_students(rows, commit=False)
        summary["books"] = self._seed_books()
        summary["results"] = self._seed_results()
        self.session.commit()
        return summary

    def _seed_books(self) -> Dict[str, int]:
        """Creates the minimal book catalog if the titles do not exist yet."""
        created = 0
        existing = 0
        for title, level in self.MINIMAL_BOOKS:
            if self.book_repo.exists_by_title(title):
                existing += 1
            else:
                self.book_repo.create(book=title, level=level)
                created += 1
        return {"total": len(self.MINIMAL_BOOKS), "created": created, "existing": existing}

    def _seed_results(self) -> Dict[str, Any]:
        """
        Generates at least three synthetic results per student.

        The pseudo-random generator is deterministic per student and attempt,
        so re-running the command yields the same candidates and skips those
        that already exist (idempotency, T-BE05-04).
        """
        tests = self.test_repo.get_all()
        students = self.student_repo.get_all_students()

        created = 0
        skipped = 0
        reported_students = 0

        for student in students:
            section_id = self._first_section_id(student)
            if section_id is None:
                continue
            for attempt in range(self.MIN_RESULTS_PER_STUDENT):
                rng = random.Random(f"{student.external_id or student.id}:{attempt}")
                test = rng.choice(tests)
                test_date = self.RESULTS_BASE_DATE + datetime.timedelta(
                    days=attempt * self.RESULTS_DAY_SPACING
                )
                time_seconds = self._compute_time(test.words, attempt, rng)
                successes, mistakes = self._compute_score(attempt, rng)

                if self.result_repo.exists(student.id, test.id, test_date):
                    skipped += 1
                    continue

                self.result_repo.create(
                    student_id=student.id,
                    section_id=section_id,
                    test_id=test.id,
                    test_date=test_date,
                    time=time_seconds,
                    successes=successes,
                    mistakes=mistakes,
                )
                created += 1
            reported_students += 1

        return {
            "total_students": reported_students,
            "min_results_per_student": self.MIN_RESULTS_PER_STUDENT,
            "created": created,
            "skipped": skipped,
        }

    def _first_section_id(self, student) -> Any:
        """Returns the student's first enrolled section id or None."""
        for enrollment in student.student_sections:
            return enrollment.section_id
        return None

    @staticmethod
    def _compute_time(word_count: int, attempt: int, rng: random.Random) -> int:
        """Computes a plausible reading time with a growing speed trend."""
        target_ppm = 90 + attempt * 25 + rng.randint(-8, 8)
        time_seconds = round(word_count / (max(target_ppm, 1) / 60.0))
        return max(1, time_seconds)

    @staticmethod
    def _compute_score(attempt: int, rng: random.Random) -> Tuple[int, int]:
        """Computes deterministic successes and mistakes per attempt."""
        successes = min(18, 10 + attempt * 2 + rng.randint(0, 2))
        mistakes = max(0, rng.randint(0, 5 - attempt))
        return successes, mistakes