import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.models.book import Book, ReadBook
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Result, Test


class NoBypassConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-28."""
    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    # Sección histórica (curso 2024-2025) y actual (curso 2025-2026)
    section_past = Section(
        name="1º ESO A",
        center_id=center.id,
        academic_year="2024-2025",
    )
    section_current = Section(
        name="2º ESO A",
        center_id=center.id,
        academic_year="2025-2026",
    )
    section_other = Section(
        name="1º ESO B",
        center_id=center.id,
        academic_year="2025-2026",
    )
    session.add_all([section_past, section_current, section_other])
    session.flush()

    # Alumno 1: con historial completo
    s1 = Student(
        name="Aitor Ortiz",
        external_id="AIT-001",
        birth_date=datetime.date(2012, 5, 15),
        gender="M",
        academic_status="Ordinario",
        sector="Sector 1",
    )
    # Alumno 2: recién importado sin datos
    s2_empty = Student(
        name="Leire Blanco",
        external_id="LEI-002",
        birth_date=datetime.date(2013, 3, 20),
        gender="F",
        academic_status="ACNEAE",
        sector="Sector 2",
    )
    session.add_all([s1, s2_empty])
    session.flush()

    # Matrículas de s1: pasada y actual
    ss_past = StudentSection(
        student_id=s1.id,
        section_id=section_past.id,
        created_on=datetime.date(2024, 9, 10),
    )
    ss_current = StudentSection(
        student_id=s1.id,
        section_id=section_current.id,
        created_on=datetime.date(2025, 9, 10),
    )
    # Matrícula de s2
    ss_s2 = StudentSection(
        student_id=s2_empty.id,
        section_id=section_current.id,
        created_on=datetime.date(2025, 9, 10),
    )
    session.add_all([ss_past, ss_current, ss_s2])
    session.flush()

    # Prueba y resultado para s1
    test1 = Test(code="TEST-01", name="Comprensión Inicial", words=120, course=1, test_letter="I", type="Lectura")
    session.add(test1)
    session.flush()

    res1 = Result(
        student_id=s1.id,
        section_id=section_current.id,
        test_id=test1.id,
        test_date=datetime.date(2025, 10, 15),
        time=60,
        successes=110,
        mistakes=10,
    )
    session.add(res1)

    # Libro y lectura para s1
    book1 = Book(book="El Lazarillo de Tormes", level="0")
    session.add(book1)
    session.flush()

    reading1 = ReadBook(
        student_id=s1.id,
        book_id=book1.id,
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2025, 10, 20),
    )
    session.add(reading1)
    session.commit()

    return {
        "center": center,
        "section_past": section_past,
        "section_current": section_current,
        "section_other": section_other,
        "student1": s1,
        "student_empty": s2_empty,
        "test1": test1,
        "result1": res1,
        "book1": book1,
        "reading1": reading1,
    }


def test_scenario_1_and_2_complete_student_card(client, setup_data):
    """
    Escenarios 1 y 2: Ficha completa en una sola llamada
    Dado un alumno con resultados y lecturas registrados
    Cuando se consulta GET /api/students/{id}
    Entonces la respuesta incluye sus datos personales,
    secciones actuales e históricas, resultados con PPM y aciertos,
    y sus lecturas con su estado, todo en una sola petición.
    """
    s1 = setup_data["student1"]
    sec_curr = setup_data["section_current"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_curr.id)]},
    )

    resp = client.get(f"/api/students/{s1.id}")
    assert resp.status_code == 200

    data = resp.get_json()

    # 1. Datos personales
    assert data["id"] == str(s1.id)
    assert data["name"] == "Aitor Ortiz"
    assert data["birth_date"] == "2012-05-15"
    assert data["gender"] == "M"
    assert data["academic_status"] == "Ordinario"
    assert data["sector"] == "Sector 1"
    assert "age" in data

    # 2. Secciones actuales e históricas
    assert "sections" in data or "current_sections" in data
    current_secs = data.get("current_sections") or data["sections"].get("current", [])
    hist_secs = data.get("historical_sections") or data["sections"].get("historical", [])

    assert len(current_secs) >= 1
    assert any(s["name"] == "2º ESO A" for s in current_secs)
    assert len(hist_secs) >= 1
    assert any(s["name"] == "1º ESO A" for s in hist_secs)

    # 3. Resultados con métricas
    assert "results" in data
    assert len(data["results"]) == 1
    r = data["results"][0]
    assert r["test_name"] == "Comprensión Inicial"
    assert r["ppm"] == 120.0  # (120 words / 60 sec) * 60
    assert "accuracy" in r

    # 4. Lecturas con estado
    assert "readings" in data
    assert len(data["readings"]) == 1
    read = data["readings"][0]
    assert read["title"] == "El Lazarillo de Tormes"
    assert read["status"] == "finalizada"
    assert read["end_date"] == "2025-10-20"


def test_scenario_3_distinction_of_historical_sections(client, setup_data):
    """
    Escenario 3: Secciones históricas
    Dado un alumno que cambió de sección entre cursos
    Cuando se consulta su ficha
    Entonces se distinguen sus secciones actuales de las anteriores.
    """
    s1 = setup_data["student1"]
    sec_curr = setup_data["section_current"]

    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    resp = client.get(f"/api/students/{s1.id}")
    assert resp.status_code == 200

    data = resp.get_json()
    current_secs = data.get("current_sections") or data["sections"]["current"]
    hist_secs = data.get("historical_sections") or data["sections"]["historical"]

    current_names = [s["name"] for s in current_secs]
    hist_names = [s["name"] for s in hist_secs]

    assert "2º ESO A" in current_names
    assert "1º ESO A" not in current_names
    assert "1º ESO A" in hist_names
    assert "2º ESO A" not in hist_names


def test_scenario_4_student_without_data(client, setup_data):
    """
    Escenario 4: Alumno sin datos
    Dado un alumno recién importado sin resultados ni lecturas
    Cuando se consulta su ficha
    Entonces se devuelven sus datos con listas vacías y 200 OK.
    """
    s2 = setup_data["student_empty"]
    sec_curr = setup_data["section_current"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_curr.id)]},
    )

    resp = client.get(f"/api/students/{s2.id}")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["id"] == str(s2.id)
    assert data["name"] == "Leire Blanco"
    assert data["results"] == []
    assert data["readings"] == []


def test_scenario_5_student_not_found(client, setup_data):
    """
    Escenario 5a: Alumno inexistente devuelve 404 Not Found.
    """
    sec_curr = setup_data["section_current"]
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_curr.id)]},
    )

    non_existent_id = uuid.uuid4()
    resp = client.get(f"/api/students/{non_existent_id}")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "NOT_FOUND"


def test_scenario_5_tutor_without_permission_forbidden(client, setup_data):
    """
    Escenario 5b: Tutor sin sección del alumno devuelve 403 Forbidden.
    """
    s1 = setup_data["student1"]
    sec_other = setup_data["section_other"]

    # Tutor asignado solo a 1º ESO B (el alumno está en 2º ESO A y 1º ESO A)
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_other.id)]},
    )

    resp = client.get(f"/api/students/{s1.id}")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_access_control_unauthenticated_and_pending_role(client, setup_data):
    """
    Control de acceso: 401 sin sesión y 403 con rol pendiente.
    """
    s1_id = str(setup_data["student1"].id)

    app = create_app(NoBypassConfig)
    with app.test_client() as unauth_client:
        # 401 sin sesión
        assert unauth_client.get(f"/api/students/{s1_id}").status_code == 401

    # 403 con rol pendiente
    client.post("/api/dev/session", json={"role": "pendiente", "sections": []})
    assert client.get(f"/api/students/{s1_id}").status_code == 403


def test_versioned_endpoint_v1_alias(client, setup_data):
    """
    Verifica que GET /api/v1/students/{id} funciona igual que GET /api/students/{id}.
    """
    s1 = setup_data["student1"]
    sec_curr = setup_data["section_current"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_curr.id)]},
    )

    resp = client.get(f"/api/v1/students/{s1.id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == str(s1.id)
