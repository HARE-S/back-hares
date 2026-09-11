import re

from app.analytics.evolution import calculate_individual_evolution
from app.extensions import db
from app.models.student import Student
from app.repositories.book_repository import BookRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.test_repository import TestRepository
from app.services.seed_service import SeedService

ACCENT_CHARS = "áéíóúüñÁÉÍÓÚÜÑ"


def _run_seed():
    service = SeedService(db.session)
    return service.seed()


def _snapshot_counts():
    student_repo = StudentRepository(db.session)
    test_repo = TestRepository(db.session)
    book_repo = BookRepository(db.session)
    result_repo = ResultRepository(db.session)
    return {
        "students": student_repo.count_students(),
        "tests": len(test_repo.get_all()),
        "books": len(book_repo.get_all()),
        "results": result_repo.count(),
        "enrollments": student_repo.count_enrollments(),
    }


def test_scenario_1_initial_load_creates_masters_and_catalog(app):
    """Escenario 1: Carga inicial.

    Dado una base de datos migrada y vacía
    Cuando se ejecuta el comando de carga de datos de prueba
    Entonces se crean los 28 alumnos de import_data.csv
    Y se crean las 34 pruebas de tests.csv
    Y se crea un catálogo mínimo de libros
    """
    with app.app_context():
        summary = _run_seed()

        assert summary["students"]["total"] == 28
        assert summary["students"]["students_created"] == 28
        assert summary["tests"]["total"] == 34
        assert summary["tests"]["created"] == 34
        assert summary["books"]["total"] == 5
        assert summary["books"]["created"] == 5
        assert summary["results"]["created"] == 28 * 3

        student_repo = StudentRepository(db.session)
        assert student_repo.count_students() == 28
        assert student_repo.count_centers() == 2
        assert student_repo.count_sections() == 5

        first = student_repo.get_student_by_external_id("STU01")
        assert first is not None
        assert first.name == "student 1"

        last = student_repo.get_student_by_external_id("STU28")
        assert last is not None
        assert last.name == "student 28"

        assert TestRepository(db.session).get_by_code("0IF") is not None
        assert TestRepository(db.session).get_by_code("3CL") is not None
        assert len(BookRepository(db.session).get_all()) == 5


def test_scenario_1_multi_section_student_gets_multiple_enrollments(app):
    """Escenario 1: El campo sections multivalor genera varias matrículas.

    Dado un alumno con sections = "1A,1B"
    Cuando se ejecuta la carga
    Entonces el alumno tiene dos matrículas
    """
    with app.app_context():
        _run_seed()

        student_repo = StudentRepository(db.session)
        stu03 = student_repo.get_student_by_external_id("STU03")
        assert stu03 is not None
        assert len(stu03.student_sections) == 2
        section_names = {ss.section.name for ss in stu03.student_sections}
        assert section_names == {"1A", "1B"}


def test_scenario_2_synthetic_results_allow_evolution(app):
    """Escenario 2: Resultados sintéticos con evolución.

    Dado los alumnos cargados
    Cuando termina la carga
    Entonces cada alumno tiene al menos tres resultados
    Y esos resultados están en fechas distintas
    Y permiten calcular una evolución
    """
    with app.app_context():
        _run_seed()

        student_repo = StudentRepository(db.session)
        result_repo = ResultRepository(db.session)
        students = student_repo.get_all_students()
        assert len(students) == 28

        for student in students:
            results = result_repo.get_by_student(student.id)
            assert len(results) >= 3
            assert len({r.test_date for r in results}) == len(results)

            evolution_data = [
                {
                    "test_date": r.test_date,
                    "word_count": r.test.words,
                    "time": r.time,
                    "successes": r.successes,
                    "mistakes": r.mistakes,
                }
                for r in results
            ]
            evolution = calculate_individual_evolution(evolution_data)
            assert evolution["has_insufficient_data"] is False
            assert evolution["total_tests"] >= 2


def test_scenario_3_command_is_idempotent(app):
    """Escenario 3: Idempotencia del comando.

    Dado que el comando ya se ha ejecutado una vez
    Cuando se ejecuta de nuevo
    Entonces no se duplica ningún registro
    Y el recuento de filas permanece igual
    """
    with app.app_context():
        first_summary = _run_seed()
        counts_after_first = _snapshot_counts()

        second_summary = _run_seed()
        counts_after_second = _snapshot_counts()

        assert counts_after_first == counts_after_second
        assert second_summary["students"]["students_created"] == 0
        assert second_summary["tests"]["created"] == 0
        assert second_summary["books"]["created"] == 0
        assert second_summary["results"]["created"] == 0
        assert counts_after_second["results"] == first_summary["results"]["created"]


def test_scenario_4_anonymous_names_without_personal_data(app):
    """Escenario 4: Ausencia de datos reales.

    Dado el conjunto de datos cargado
    Cuando se inspeccionan los nombres de alumnado
    Entonces son identificadores anónimos del tipo "student N"
    Y no contienen ningún dato personal real
    """
    with app.app_context():
        _run_seed()

        students = db.session.query(Student).all()
        assert len(students) == 28
        for student in students:
            assert re.fullmatch(r"student \d+", student.name)
            assert not any(ch in ACCENT_CHARS for ch in student.name)