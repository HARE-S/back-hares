"""BE-07: Importación idempotente — escenarios 1 a 5.

Cubre la identificación por `external_id` (nunca por nombre), la
actualización de datos cambiantes, la sincronización de matrículas y la
tolerancia a filas inválidas que no abortan el resto del fichero.
"""
from pathlib import Path

from app.extensions import db
from app.importer import StudentImporter, parse_students_csv_collect
from app.models.student import Student, StudentSection
from app.repositories.student_repository import StudentRepository

FIXTURES = Path(__file__).parent / "fixtures"
EMPTY_EXTERNAL_ID_CSV = FIXTURES / "import_data_empty_external_id.csv"
VALID_CSV = FIXTURES / "import_data_valid.csv"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _import_file(session, csv_path: Path):
    service = StudentImporter(session)
    return service.import_from_csv(_read(csv_path))


def _counts(session):
    repo = StudentRepository(session)
    return {
        "students": repo.count_students(),
        "centers": repo.count_centers(),
        "sections": repo.count_sections(),
        "enrollments": repo.count_enrollments(),
    }


def test_scenario_1_reimport_produces_identical_counts(app):
    """Escenario 1: reimportar el mismo fichero mantiene los recuentos.

    Dado un fichero de alumnado ya importado
    Cuando se vuelve a importar exactamente el mismo fichero
    Entonces los recuentos de alumnos, matrículas, centros y secciones
    son idénticos a la primera importación
    Y el resumen indica omitidos en lugar de creados
    """
    with app.app_context():
        first = _import_file(db.session, VALID_CSV)
        first_counts = _counts(db.session)

        second = _import_file(db.session, VALID_CSV)
        second_counts = _counts(db.session)

        assert first_counts == second_counts
        assert second["students_created"] == 0
        assert second["students_omitted"] == first["students_created"]
        assert second["students_omitted"] == 6
        assert second["enrollments_created"] == 0
        assert second["errors"] == 0


def test_scenario_2_name_change_updates_in_place(app):
    """Escenario 2: un cambio de nombre actualiza, no crea un alumno nuevo.

    Dado un alumno existente con un nombre antiguo y resultados asociados
    Cuando se importa un fichero con su external_id y un nombre nuevo
    Entonces se actualiza el nombre del mismo alumno
    Y no se crea ningún alumno nuevo
    Y sus resultados y matrículas siguen asociados al mismo registro
    """
    with app.app_context():
        _import_file(db.session, VALID_CSV)
        repo = StudentRepository(db.session)
        student = repo.get_student_by_external_id("ALX003")
        student_id = student.id
        previous_name = student.name

        new_name = "Carla Díaz Ortíz (actualizada)"
        content = _read(VALID_CSV).replace("Carla Díaz Ortiz", new_name)
        rename_summary = StudentImporter(db.session).import_from_csv(content)
        db.session.flush()

        assert rename_summary["students_created"] == 0
        assert rename_summary["students_updated"] == 1

        repo = StudentRepository(db.session)
        renamed = repo.get_student_by_external_id("ALX003")
        assert renamed.id == student_id
        assert renamed.name == new_name
        assert repo.get_student_by_external_id("ALX003").name != previous_name
        assert repo.count_students() == 6

        enrollments = db.session.query(StudentSection).filter(
            StudentSection.student_id == student_id
        ).all()
        assert len(enrollments) == 3


def test_scenario_3_additional_enrollment_is_added(app):
    """Escenario 3: una matrícula nueva se añade conservando las existentes.

    Dado un alumno con matrículas en 1CARMED2, JB25480021 e ITININSMAD
    Cuando se importa el mismo external_id con una sección extra "3ESO"
    Entonces se crea la nueva matrícula
    Y las tres anteriores siguen existiendo
    """
    with app.app_context():
        _import_file(db.session, VALID_CSV)
        repo = StudentRepository(db.session)
        student = repo.get_student_by_external_id("ALX003")
        student_id = student.id

        before = db.session.query(StudentSection).filter(
            StudentSection.student_id == student_id
        ).count()
        assert before == 3

        content = _read(VALID_CSV).replace(
            "JB25480021,ITININSMAD",
            "JB25480021,ITININSMAD,3ESO",
        )
        summary = StudentImporter(db.session).import_from_csv(content)

        assert summary["sections_created"] == 1
        assert summary["enrollments_created"] == 1

        names = {
            ss.section.name
            for ss in db.session.query(StudentSection)
            .filter(StudentSection.student_id == student_id)
            .all()
        }
        assert names == {"1CARMED2", "JB25480021", "ITININSMAD", "3ESO"}


def test_scenario_4_same_name_resolved_by_external_id(app):
    """Escenario 4: dos alumnos con el mismo nombre se distinguen por external_id.

    Dado dos filas con el mismo student_name pero distinto external_id
    Cuando se importan
    Entonces se crean dos alumnos distintos
    Y cada uno queda ligado a su propio external_id
    """
    with app.app_context():
        content = (
            "student_id;student_name;sections;center\n"
            "X1;Nombre Común;1A;Centro A\n"
            "X2;Nombre Común;1B;Centro B\n"
        )
        summary = StudentImporter(db.session).import_from_csv(content)

        assert summary["students_created"] == 2
        repo = StudentRepository(db.session)
        x1 = repo.get_student_by_external_id("X1")
        x2 = repo.get_student_by_external_id("X2")
        assert x1 is not None and x2 is not None
        assert x1.id != x2.id
        assert x1.name == x2.name == "Nombre Común"


def test_scenario_5_row_without_external_id_rejected_and_rest_continues(app):
    """Escenario 5: una fila sin external_id se rechaza y el resto continúa.

    Dado un fichero cuya segunda fila carece de student_id
    Cuando se importa
    Entonces esa fila se rechaza y queda registrada en el informe de errores
    Y las filas válidas se importan (el proceso no se aborta)
    """
    with app.app_context():
        summary = _import_file(db.session, EMPTY_EXTERNAL_ID_CSV)

        assert summary["errors"] == 1
        assert summary["students_created"] == 2

        error = summary["error_details"][0]
        assert error["line"] == 3
        assert error["column"] == "student_id"
        assert "no puede estar vacío" in error["reason"]

        repo = StudentRepository(db.session)
        assert repo.get_student_by_external_id("ALX001") is not None
        assert repo.get_student_by_external_id("ALX002") is not None
        assert repo.count_students() == 2


def test_tolerant_parser_reports_row_errors_without_aborting(app):
    """El parser tolerante devuelve (rows, errors) sin lanzar excepción."""
    rows, errors = parse_students_csv_collect(_read(EMPTY_EXTERNAL_ID_CSV))
    assert len(rows) == 2
    assert len(errors) == 1
    assert isinstance(rows[0], dict)
    assert isinstance(errors[0], dict)