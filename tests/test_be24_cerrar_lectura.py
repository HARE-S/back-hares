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
    """Fixture para crear datos base de prueba para BE-24."""
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

    book1 = Book(book="Don Quijote de la Mancha", level="I")
    book2 = Book(book="El Lazarillo de Tormes", level="0")
    session.add_all([book1, book2])
    session.flush()

    # Lectura en curso para student1 con book1 (iniciada el 12/09/2026)
    reading1 = ReadBook(
        student_id=s1.id,
        book_id=book1.id,
        start_date=datetime.date(2026, 9, 12),
        end_date=None,
    )
    session.add(reading1)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": s1,
        "student2": s2,
        "book1": book1,
        "book2": book2,
        "reading1": reading1,
    }


def test_scenario_1_close_reading_success(client, setup_data, session):
    """
    Escenario 1: Cierre correcto
    Dado una lectura en curso con fecha de inicio 12/09/2026
    Cuando se envía PATCH con end_date 03/10/2026
    Entonces la lectura queda registrada como finalizada
    Y devuelve 200 OK
    """
    clear_audit_logs()
    r1 = setup_data["reading1"]
    sec1 = setup_data["section1"]

    # Autenticar como tutor de la sección 1
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {"end_date": "2026-10-03"}
    resp = client.patch(f"/api/readings/{r1.id}", json=payload)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["id"] == str(r1.id)
    assert data["end_date"] == "2026-10-03"
    assert data["status"] == "finalizada"
    assert data["start_date"] == "2026-09-12"

    # Verificar en base de datos
    session.expire_all()
    updated_reading = session.get(ReadBook, r1.id)
    assert updated_reading.end_date == datetime.date(2026, 10, 3)

    # Verificar auditoría
    logs = [log for log in get_audit_logs() if log.get("resource_id") == str(r1.id)]
    assert len(logs) >= 1
    assert logs[-1]["action"] in ("CLOSE_READING", "UPDATE_READING")


def test_scenario_1_nested_alias_patch_success(client, setup_data, session):
    """
    Verifica que la ruta anidada /api/students/{student_id}/books/{reading_id}
    también funciona correctamente como alias.
    """
    r1 = setup_data["reading1"]
    sec1 = setup_data["section1"]
    s1 = setup_data["student1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    payload = {"end_date": "2026-10-05"}
    resp = client.patch(f"/api/students/{s1.id}/books/{r1.id}", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["end_date"] == "2026-10-05"


def test_scenario_2_end_date_before_start_date_fails(client, setup_data, session):
    """
    Escenario 2: Fecha de fin anterior al inicio
    Dado una lectura con inicio 12/09/2026
    Cuando se envía PATCH con end_date 01/09/2026
    Entonces el sistema rechaza la modificación
    Y devuelve 422 Unprocessable Entity
    """
    r1 = setup_data["reading1"]
    sec1 = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    # Fecha anterior al 12/09/2026
    payload = {"end_date": "2026-09-01"}
    resp = client.patch(f"/api/readings/{r1.id}", json=payload)
    assert resp.status_code == 422

    data = resp.get_json()
    assert "error" in data or "message" in data

    # Asegurar que en BD sigue intacta sin fecha de fin
    session.expire_all()
    reading_db = session.get(ReadBook, r1.id)
    assert reading_db.end_date is None


def test_scenario_3_distinction_of_states(client, setup_data, session):
    """
    Escenario 3: Distinción de estados
    Dado un alumno con una lectura cerrada y otra en curso
    Cuando se consulta su listado de lecturas
    Entonces cada una indica claramente su estado
    Y las finalizadas muestran su fecha de fin
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]
    book2 = setup_data["book2"]
    r1 = setup_data["reading1"]

    # r1 se cierra el 2026-10-03
    r1.end_date = datetime.date(2026, 10, 3)
    session.commit()

    # Se añade una segunda lectura en curso para student1
    r2 = ReadBook(
        student_id=s1.id,
        book_id=book2.id,
        start_date=datetime.date(2026, 10, 10),
        end_date=None,
    )
    session.add(r2)
    session.commit()

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    resp = client.get(f"/api/students/{s1.id}/books")
    assert resp.status_code == 200

    items = resp.get_json()
    assert isinstance(items, list)
    assert len(items) == 2

    # Encontrar la lectura finalizada y la en curso
    finished = next(item for item in items if item["id"] == str(r1.id))
    in_progress = next(item for item in items if item["id"] == str(r2.id))

    assert finished["status"] == "finalizada"
    assert finished["end_date"] == "2026-10-03"
    assert finished["title"] == "Don Quijote de la Mancha"

    assert in_progress["status"] == "en curso"
    assert in_progress["end_date"] is None
    assert in_progress["title"] == "El Lazarillo de Tormes"


def test_scenario_4_reopen_reading(client, setup_data, session):
    """
    Escenario 4: Reapertura
    Dado una lectura ya cerrada por error
    Cuando se envía PATCH poniendo end_date a nulo
    Entonces la lectura vuelve a considerarse en curso
    """
    clear_audit_logs()
    r1 = setup_data["reading1"]
    sec1 = setup_data["section1"]

    # Primero la cerramos
    r1.end_date = datetime.date(2026, 10, 3)
    session.commit()

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    # Ahora reabrimos enviando end_date: null
    payload = {"end_date": None}
    resp = client.patch(f"/api/readings/{r1.id}", json=payload)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["id"] == str(r1.id)
    assert data["end_date"] is None
    assert data["status"] == "en curso"
    assert data["start_date"] == "2026-09-12"  # Se conserva la fecha de inicio original

    # Verificar en base de datos
    session.expire_all()
    reading_db = session.get(ReadBook, r1.id)
    assert reading_db.end_date is None

    # Verificar auditoría
    logs = [log for log in get_audit_logs() if log.get("resource_id") == str(r1.id)]
    assert len(logs) >= 1
    assert logs[-1]["action"] in ("REOPEN_READING", "UPDATE_READING")


def test_scenario_5_reading_not_found(client, setup_data):
    """
    Escenario 5: Lectura inexistente
    Dado un identificador de lectura que no existe
    Cuando se envía PATCH
    Entonces el sistema devuelve 404 Not Found
    """
    sec1 = setup_data["section1"]
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    non_existent_id = uuid.uuid4()
    resp = client.patch(f"/api/readings/{non_existent_id}", json={"end_date": "2026-10-03"})
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "NOT_FOUND"


def test_forbidden_for_unauthorized_tutor_or_pending_role(client, setup_data):
    """
    Control de acceso:
    - Tutor de otra sección no puede modificar la lectura -> 403 Forbidden
    - Usuario con rol pendiente -> 403 Forbidden
    """
    r1 = setup_data["reading1"]
    sec2 = setup_data["section2"]

    # Tutor asignado solo a sección 2 (el alumno pertenece a sección 1)
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec2.id)]},
    )
    resp = client.patch(f"/api/readings/{r1.id}", json={"end_date": "2026-10-03"})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # Usuario con rol pendiente
    client.post(
        "/api/dev/session",
        json={"role": "pendiente", "sections": []},
    )
    resp = client.patch(f"/api/readings/{r1.id}", json={"end_date": "2026-10-03"})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_unauthenticated_request_fails(setup_data):
    """Sin autenticación devuelve 401 Unauthorized."""
    r1 = setup_data["reading1"]
    app = create_app(NoBypassConfig)
    with app.test_client() as unauth_client:
        resp = unauth_client.patch(f"/api/readings/{r1.id}", json={"end_date": "2026-10-03"})
        assert resp.status_code == 401


def test_invalid_json_body_bad_request(client, setup_data):
    """Cuerpo no JSON o formato inválido devuelve 400 Bad Request."""
    r1 = setup_data["reading1"]
    sec1 = setup_data["section1"]
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    # No JSON
    resp = client.patch(
        f"/api/readings/{r1.id}",
        data="not-a-json",
        content_type="text/plain",
    )
    assert resp.status_code == 400

    # Fecha inválida sintácticamente
    resp = client.patch(
        f"/api/readings/{r1.id}",
        json={"end_date": "fecha-invalida"},
    )
    assert resp.status_code == 400
