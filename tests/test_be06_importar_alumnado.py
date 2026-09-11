"""BE-06: Importar alumnado desde el volcado de Alexia — escenarios 1 a 5.

Cubrimos la lectura y el alta inicial de centros, secciones, alumnos y
matrículas reutilizando el importador idempotente (BE-05 / BE-07).
El informe de errores por fila pertenece a BE-08 y queda fuera de alcance.
"""
from pathlib import Path

import pytest

from app.core.exceptions import ValidationError
from app.extensions import db
from app.importer import StudentImporter, parse_students_csv
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.repositories.student_repository import StudentRepository

FIXTURES = Path(__file__).parent / "fixtures"
VALID_CSV = FIXTURES / "import_data_valid.csv"
BAD_SEPARATOR_CSV = FIXTURES / "import_data_bad_separator.csv"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _import_file(session, csv_path: Path):
    service = StudentImporter(session)
    return service.import_from_csv(_read(csv_path))


def test_scenario_1_import_creates_masters_and_enrollments_with_summary(app):
    """Escenario 1: un fichero correcto crea todo y el resumen es completo.

    Dado un CSV con separador ';' y UTF-8 con las columnas esperadas
    Cuando se ejecuta la importación
    Entonces se crean los centros, secciones, alumnos y matrículas
    Y el resumen indica creados, actualizados, omitidos y errores
    """
    with app.app_context():
        summary = _import_file(db.session, VALID_CSV)

        assert summary["total"] == 6
        assert summary["students_created"] == 6
        assert summary["students_updated"] == 0
        assert summary["students_omitted"] == 0
        assert summary["centers_created"] == 2
        assert summary["sections_created"] == 7
        assert summary["enrollments_created"] == 9
        assert summary["errors"] == 0

        repo = StudentRepository(db.session)
        assert repo.count_students() == 6
        assert repo.count_centers() == 2
        assert repo.count_sections() == 7
        assert repo.count_enrollments() == 9


def test_scenario_2_multi_value_sections_create_distinct_enrollments(app):
    """Escenario 2 (obligatorio): sections multivalor genera una matrícula por sección.

    Dado una fila con sections = "1CARMED2,JB25480021,ITININSMAD"
    Cuando se procesa la fila
    Entonces se generan tres matrículas para el alumno
    Y cada una apunta a una sección distinta
    """
    with app.app_context():
        rows = parse_students_csv(
            "student_id;student_name;sections;center\n"
            "ALX003;Carla Díaz Ortiz;1CARMED2,JB25480021,ITININSMAD;Boluetaberri\n"
        )
        assert rows[0]["sections"] == ["1CARMED2", "JB25480021", "ITININSMAD"]

        summary = _import_file(db.session, VALID_CSV)
        assert summary["enrollments_created"] == 9

        student = StudentRepository(db.session).get_student_by_external_id("ALX003")
        assert student is not None
        enrollments = db.session.query(StudentSection).filter(
            StudentSection.student_id == student.id
        ).all()
        section_names = {enrollment.section.name for enrollment in enrollments}
        assert section_names == {"1CARMED2", "JB25480021", "ITININSMAD"}

        section_names_all = {row[0] for row in db.session.query(Section.name).all()}
        assert {"1CARMED2", "JB25480021", "ITININSMAD"}.issubset(section_names_all)


def test_scenario_3_unknown_center_is_created(app):
    """Escenario 3: un centro no existente se crea.

    Dado una fila con el centro "Boluetaberri" sin registrar
    Cuando se procesa
    Entonces se crea el centro
    Y el alumno queda asociado a él a través de sus secciones
    """
    with app.app_context():
        _import_file(db.session, VALID_CSV)

        center = db.session.query(Center).filter(Center.name == "Boluetaberri").first()
        assert center is not None

        student = StudentRepository(db.session).get_student_by_external_id("ALX003")
        assert student is not None
        section_centers = {ss.section.center.name for ss in student.student_sections}
        assert section_centers == {"Boluetaberri"}


def test_scenario_4_unknown_section_is_created_under_its_center(app):
    """Escenario 4: una sección no registrada se crea bajo el centro de la fila.

    Dado una fila con una sección nueva ("3ESO") para el centro "Peñascal"
    Cuando se procesa
    Entonces se crea la sección asociada al centro de la fila
    """
    with app.app_context():
        _import_file(db.session, VALID_CSV)

        section = (
            db.session.query(Section)
            .join(Center, Section.center_id == Center.id)
            .filter(Section.name == "3ESO", Center.name == "Peñascal")
            .first()
        )
        assert section is not None
        assert section.center.name == "Peñascal"


def test_scenario_5_wrong_separator_aborts_without_partial_rows(app):
    """Escenario 5: separador incorrecto detiene el proceso sin registros parciales.

    Dado un fichero que no usa ';' como separador
    Cuando se intenta importar
    Entonces se lanza ValidationError
    Y no se ha creado ningún registro (atómico)
    """
    with app.app_context():
        content = _read(BAD_SEPARATOR_CSV)

        with pytest.raises(ValidationError):
            parse_students_csv(content)

        before = {
            "students": StudentRepository(db.session).count_students(),
            "centers": StudentRepository(db.session).count_centers(),
        }
        assert before["students"] == 0
        assert before["centers"] == 0

        with pytest.raises(ValidationError):
            StudentImporter(db.session).import_from_csv(content)
        db.session.rollback()

        assert StudentRepository(db.session).count_students() == before["students"]
        assert StudentRepository(db.session).count_centers() == before["centers"]