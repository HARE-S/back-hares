import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.core.audit import clear_audit_logs, get_audit_logs
from app.models.book import Book, ReadBook
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


class NoBypassConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-23."""
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

    # Libro disponible
    book1 = Book(book="Don Quijote de la Mancha", level="I")
    # Libro deshabilitado (baja lógica)
    book_disabled = Book(
        book="Libro Retirado",
        level="0",
        disabled_at=datetime.date(2026, 1, 1),
    )
    session.add_all([book1, book_disabled])
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": s1,
        "student2": s2,
        "book1": book1,
        "book_disabled": book_disabled,
    }


def test_scenario_1_assign_book_success(client, setup_data, session):
    """
    Escenario 1: Asignación correcta
    Dado un tutor con la sección del alumno asignada
    Cuando envía POST /api/students/{id}/books con book_id y start_date
    Entonces se registra la lectura
    Y devuelve 201 Created
    """
    clear_audit_logs()
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(book1.id),
        "start_date": "2026-09-12",
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["student_id"] == str(s1.id)
    assert data["book_id"] == str(book1.id)
    assert data["book_title"] == "Don Quijote de la Mancha"
    assert data["book_level"] == "I"
    assert data["start_date"] == "2026-09-12"
    assert data["end_date"] is None
    assert data["status"] == "en curso"

    # Verificar en base de datos
    session.expire_all()
    reading = session.query(ReadBook).filter_by(student_id=s1.id, book_id=book1.id).first()
    assert reading is not None
    assert reading.start_date == datetime.date(2026, 9, 12)
    assert reading.end_date is None

    # Probar también con prefijo canónico /api/v1/students/{id}/books
    payload_v1 = {
        "book_id": str(book1.id),
        "start_date": "2026-10-01",  # Diferente start_date
    }
    resp_v1 = client.post(f"/api/v1/students/{s1.id}/books", json=payload_v1)
    assert resp_v1.status_code == 201


def test_scenario_2_assign_book_without_end_date(client, setup_data, session):
    """
    Escenario 2: Lectura sin fecha de fin
    Dado una asignación sin end_date
    Cuando se procesa
    Entonces la lectura queda registrada como en curso
    Y no se considera un error
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(book1.id),
        "start_date": "2026-09-15",
        "end_date": None,
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["status"] == "en curso"
    assert data["end_date"] is None


def test_scenario_3_nonexistent_book_returns_400(client, setup_data):
    """
    Escenario 3: Libro inexistente
    Dado un book_id que no existe en el catálogo
    Cuando se intenta asignar
    Entonces el sistema devuelve 400 Bad Request
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    fake_book_id = uuid.uuid4()

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(fake_book_id),
        "start_date": "2026-09-12",
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 400
    assert "libro" in resp.get_json().get("error", "").lower()


def test_scenario_4_disabled_book_returns_400_with_explanation(client, setup_data):
    """
    Escenario 4: Libro deshabilitado
    Dado un libro con disabled_at relleno
    Cuando se intenta asignar a un alumno
    Entonces el sistema devuelve 400 Bad Request
    Y explica que el libro ya no está disponible
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book_disabled = setup_data["book_disabled"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(book_disabled.id),
        "start_date": "2026-09-12",
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 400
    err_msg = resp.get_json().get("error", "").lower()
    assert "disponible" in err_msg or "activo" in err_msg


def test_scenario_5_tutor_without_permission_returns_403(client, setup_data):
    """
    Escenario 5: Tutor sin permiso
    Dado un tutor cuyas secciones no incluyen a ese alumno
    Cuando intenta asignarle un libro
    Entonces el sistema devuelve 403 Forbidden
    """
    s1 = setup_data["student1"]
    sec2 = setup_data["section2"]  # Tutor solo tiene sec2, s1 está en sec1
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec2.id)]},
    )

    payload = {
        "book_id": str(book1.id),
        "start_date": "2026-09-12",
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_pending_role_returns_403(client, setup_data):
    """
    Usuario con rol 'pendiente' debe recibir 403 Forbidden.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "pendiente", "sections": [str(sec1.id)]},
    )

    resp = client.post(f"/api/students/{s1.id}/books", json={"book_id": str(book1.id), "start_date": "2026-09-12"})
    assert resp.status_code == 403


def test_unauthenticated_returns_401(setup_data):
    """
    Petición sin autenticación debe retornar 401 Unauthorized.
    """
    app = create_app(NoBypassConfig)
    unauth_client = app.test_client()

    s1 = setup_data["student1"]
    book1 = setup_data["book1"]

    resp = unauth_client.post(f"/api/students/{s1.id}/books", json={"book_id": str(book1.id), "start_date": "2026-09-12"})
    assert resp.status_code == 401


def test_duplicate_assignment_same_start_date_returns_409(client, setup_data):
    """
    Duplicado exacto para el mismo alumno, libro y fecha de inicio devuelve 409 Conflict.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(book1.id),
        "start_date": "2026-09-20",
    }

    # Primera asignación OK
    r1 = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert r1.status_code == 201

    # Segunda asignación idéntica rechazada con 409
    r2 = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert r2.status_code == 409
    assert r2.get_json()["error"] == "CONFLICT"


def test_end_date_before_start_date_returns_422(client, setup_data):
    """
    Fecha de fin anterior a la de inicio devuelve 422 Unprocessable Entity.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {
        "book_id": str(book1.id),
        "start_date": "2026-09-20",
        "end_date": "2026-09-10",  # Anterior
    }

    resp = client.post(f"/api/students/{s1.id}/books", json=payload)
    assert resp.status_code == 422
    assert resp.get_json()["error"] == "UNPROCESSABLE_ENTITY"


def test_nonexistent_student_returns_404(client, setup_data):
    """
    Identificador de alumno que no existe devuelve 404 Not Found.
    """
    book1 = setup_data["book1"]
    fake_student_id = uuid.uuid4()

    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    resp = client.post(
        f"/api/students/{fake_student_id}/books",
        json={"book_id": str(book1.id), "start_date": "2026-09-20"},
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "NOT_FOUND"


def test_audit_logged_on_assignment(client, setup_data):
    """
    Verifica que la asignación de libro genera un evento en auditoría ASSIGN_BOOK.
    """
    clear_audit_logs()
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book1 = setup_data["book1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    resp = client.post(
        f"/api/students/{s1.id}/books",
        json={"book_id": str(book1.id), "start_date": "2026-09-25"},
    )
    assert resp.status_code == 201

    logs = get_audit_logs()
    assign_logs = [l for l in logs if l["action"] == "ASSIGN_BOOK"]
    assert len(assign_logs) == 1
    assert assign_logs[0]["resource_type"] == "read_books"
    assert assign_logs[0]["details"]["student_id"] == str(s1.id)
    assert assign_logs[0]["details"]["book_id"] == str(book1.id)
