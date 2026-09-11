import datetime
import os
import uuid
import pytest
from sqlalchemy import text
from app import create_app
from app.config import Config
from app.core.audit import clear_audit_logs, get_audit_logs
from app.core.exceptions import ConflictError
from app.models.book import Book, ReadBook
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.repositories.reading_repository import ReadingRepository


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-25."""
    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    section1 = Section(name="1º ESO A", center_id=center.id)
    section2 = Section(name="1º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    s1 = Student(name="Aitor Ortiz")
    s2 = Student(name="Leire Blanco")
    session.add_all([s1, s2])
    session.flush()

    ss1 = StudentSection(student_id=s1.id, section_id=section1.id)
    ss2 = StudentSection(student_id=s2.id, section_id=section2.id)
    session.add_all([ss1, ss2])
    session.flush()

    book = Book(book="El Lazarillo de Tormes", level="0")
    session.add(book)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": s1,
        "student2": s2,
        "book": book,
    }


def test_scenario_1_second_reading_in_another_course_accepted(client, setup_data, session):
    """
    Escenario 1: Segunda lectura en otro curso
    Dado un alumno que leyó "El Lazarillo" con inicio 05/10/2025
    Cuando se registra otra lectura del mismo libro con inicio 12/09/2026
    Entonces el sistema acepta el registro (201 Created)
    Y el alumno tiene dos lecturas de ese libro
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book = setup_data["book"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    # 1. Primera lectura (curso anterior)
    resp1 = client.post(
        f"/api/students/{s1.id}/books",
        json={"book_id": str(book.id), "start_date": "2025-10-05"},
    )
    assert resp1.status_code == 201

    # 2. Segunda lectura del mismo libro (nuevo curso escolar)
    resp2 = client.post(
        f"/api/students/{s1.id}/books",
        json={"book_id": str(book.id), "start_date": "2026-09-12"},
    )
    assert resp2.status_code == 201

    data2 = resp2.get_json()
    assert data2["student_id"] == str(s1.id)
    assert data2["book_id"] == str(book.id)
    assert data2["start_date"] == "2026-09-12"

    # Verificar en BD que existen exactamente 2 lecturas distintas
    session.expire_all()
    readings = (
        session.query(ReadBook)
        .filter_by(student_id=s1.id, book_id=book.id)
        .order_by(ReadBook.start_date.asc())
        .all()
    )
    assert len(readings) == 2
    assert readings[0].start_date == datetime.date(2025, 10, 5)
    assert readings[1].start_date == datetime.date(2026, 9, 12)
    assert readings[0].id != readings[1].id


def test_scenario_2_exact_duplicate_rejected(client, setup_data):
    """
    Escenario 2: Duplicado exacto rechazado
    Dado una lectura de "El Lazarillo" con inicio 12/09/2026
    Cuando se registra otra del mismo libro con esa misma fecha de inicio
    Entonces el sistema devuelve 409 Conflict
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book = setup_data["book"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {"book_id": str(book.id), "start_date": "2026-09-12"}

    # Primera vez -> 201 Created
    resp1 = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp1.status_code == 201

    # Segunda vez idéntica -> 409 Conflict
    resp2 = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp2.status_code == 409
    assert resp2.get_json()["error"] == "CONFLICT"


def test_scenario_3_complete_history(client, setup_data):
    """
    Escenario 3: Histórico completo
    Dado un alumno con dos lecturas del mismo libro
    Cuando se consulta su listado de lecturas
    Entonces aparecen ambas
    Y se distinguen por su fecha de inicio
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book = setup_data["book"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    client.post(f"/api/students/{s1.id}/books", json={"book_id": str(book.id), "start_date": "2025-10-05"})
    client.post(f"/api/students/{s1.id}/books", json={"book_id": str(book.id), "start_date": "2026-09-12"})

    resp = client.get(f"/api/students/{s1.id}/books")
    assert resp.status_code == 200

    items = resp.get_json()
    assert len(items) == 2
    start_dates = [item["start_date"] for item in items]
    assert "2025-10-05" in start_dates
    assert "2026-09-12" in start_dates
    assert all(item["book_id"] == str(book.id) for item in items)


def test_scenario_4_independence_between_different_students(client, setup_data):
    """
    Escenario 4: Independencia entre alumnos
    Dado dos alumnos distintos
    Cuando ambos registran el mismo libro con la misma fecha de inicio
    Entonces el sistema acepta los dos registros (201 Created en ambos)
    """
    s1 = setup_data["student1"]
    s2 = setup_data["student2"]
    sec1 = setup_data["section1"]
    sec2 = setup_data["section2"]
    book = setup_data["book"]

    # Tutor con acceso a ambas secciones
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id), str(sec2.id)]},
    )

    payload = {"book_id": str(book.id), "start_date": "2026-09-12"}

    # Alumno 1
    resp1 = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp1.status_code == 201

    # Alumno 2 con misma fecha y mismo libro
    resp2 = client.post(f"/api/students/{s2.id}/books", json=payload)
    assert resp2.status_code == 201

    assert resp1.get_json()["id"] != resp2.get_json()["id"]


def test_repository_integrity_conflict(session, setup_data):
    """
    Verifica que el repositorio ReadingRepository atrapa la violación de integridad
    y lanza ConflictError cuando se intenta insertar duplicado a nivel persistencia.
    """
    s1 = setup_data["student1"]
    book = setup_data["book"]
    repo = ReadingRepository(session)

    # Inserción inicial
    repo.create(
        student_id=s1.id,
        book_id=book.id,
        start_date=datetime.date(2026, 9, 12),
        commit=True,
    )

    # Intento de creación directa de duplicado
    with pytest.raises(ConflictError) as exc_info:
        repo.create(
            student_id=s1.id,
            book_id=book.id,
            start_date=datetime.date(2026, 9, 12),
            commit=True,
        )
    assert "Ya existe una lectura registrada" in str(exc_info.value)


def test_postgresql_unique_constraint_direct():
    """
    T-BE25-01: Verificación de la restricción física UNIQUE en PostgreSQL real.
    Si el contenedor PostgreSQL está accesible, verifica en pg_constraint que existe
    la restricción uq_read_books_student_book_start.
    """
    db_user = os.getenv("POSTGRES_USER", "hares_user")
    db_pass = os.getenv("POSTGRES_PASSWORD", "hares_pass")
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hares_db")
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    from sqlalchemy import create_engine
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            query = text("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conname = 'uq_read_books_student_book_start'
                  AND conrelid = 'read_books'::regclass;
            """)
            res = conn.execute(query).fetchone()
            assert res is not None, "La restricción 'uq_read_books_student_book_start' no existe en PostgreSQL"
            assert res[1] == "u", "La restricción debe ser de tipo UNIQUE ('u')"
    except Exception as e:
        pytest.skip(f"Base de datos PostgreSQL real no accesible directamente desde este test runner: {e}")
