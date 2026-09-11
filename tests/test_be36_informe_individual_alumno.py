import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.core.audit import clear_audit_logs, get_audit_logs
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
    """Fixture para crear datos base de prueba para BE-36."""
    clear_audit_logs()

    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    sec1 = Section(name="1º ESO A", center_id=center.id, academic_year="2025-2026")
    sec2 = Section(name="1º ESO B", center_id=center.id, academic_year="2025-2026")
    session.add_all([sec1, sec2])
    session.flush()

    # Alumno 1: con 2 pruebas y 1 lectura (datos suficientes para evolución)
    s1 = Student(
        name="Aitor Ortiz",
        external_id="AIT-001",
        birth_date=datetime.date(2012, 5, 15),
        gender="M",
        academic_status="Ordinario",
        sector="Sector 1",
    )
    # Alumno 2: con 1 sola prueba (datos insuficientes para evolución)
    s2_single = Student(
        name="Leire Blanco",
        external_id="LEI-002",
        birth_date=datetime.date(2013, 3, 20),
        gender="F",
        academic_status="ACNEAE",
        sector="Sector 2",
    )
    # Alumno 3: en Sección 2
    s3_other = Student(
        name="Lucía Morales",
        external_id="LUC-003",
        birth_date=datetime.date(2012, 8, 20),
        gender="F",
    )
    session.add_all([s1, s2_single, s3_other])
    session.flush()

    # Matrículas
    ss1 = StudentSection(student_id=s1.id, section_id=sec1.id, created_on=datetime.date(2025, 9, 10))
    ss2 = StudentSection(student_id=s2_single.id, section_id=sec1.id, created_on=datetime.date(2025, 9, 10))
    ss3 = StudentSection(student_id=s3_other.id, section_id=sec2.id, created_on=datetime.date(2025, 9, 10))
    session.add_all([ss1, ss2, ss3])
    session.flush()

    # Pruebas
    t1 = Test(code="TEST-01", name="Prueba Inicial", words=120, course=1, test_letter="I", type="Lectura")
    t2 = Test(code="TEST-02", name="Prueba Trimestral", words=150, course=1, test_letter="M", type="Lectura")
    session.add_all([t1, t2])
    session.flush()

    # Resultados para s1 (2 pruebas en fechas distintas)
    res_s1_1 = Result(
        student_id=s1.id,
        section_id=sec1.id,
        test_id=t1.id,
        test_date=datetime.date(2025, 10, 15),
        time=60,
        successes=14,
        mistakes=2,
    )
    res_s1_2 = Result(
        student_id=s1.id,
        section_id=sec1.id,
        test_id=t2.id,
        test_date=datetime.date(2025, 11, 20),
        time=60,
        successes=18,
        mistakes=1,
    )
    # Resultado para s2 (1 sola prueba)
    res_s2_1 = Result(
        student_id=s2_single.id,
        section_id=sec1.id,
        test_id=t1.id,
        test_date=datetime.date(2025, 10, 15),
        time=70,
        successes=10,
        mistakes=5,
    )
    session.add_all([res_s1_1, res_s1_2, res_s2_1])

    # Libro y lectura para s1
    b1 = Book(book="El Lazarillo de Tormes", level="0")
    session.add(b1)
    session.flush()

    reading_s1 = ReadBook(
        student_id=s1.id,
        book_id=b1.id,
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2025, 10, 25),
    )
    session.add(reading_s1)
    session.commit()

    return {
        "center": center,
        "section1": sec1,
        "section2": sec2,
        "student1": s1,
        "student_single": s2_single,
        "student_other": s3_other,
        "test1": t1,
        "test2": t2,
        "reading1": reading_s1,
    }


def test_scenario_1_and_2_complete_report_and_generation_date(client, setup_data):
    """
    Escenarios 1 y 2: Contenido del informe y fecha de generación
    Dado un alumno con histórico registrado
    Cuando se solicitan los datos de su informe
    Entonces la respuesta incluye sus datos identificativos, histórico de pruebas,
    lecturas, serie de evolución temporal y fecha/hora de generación.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]

    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    resp = client.get(f"/api/v1/students/{s1.id}/report")
    assert resp.status_code == 200

    data = resp.get_json()

    # 1. Datos identificativos del alumno
    student_info = data.get("student") or data
    assert student_info["id"] == str(s1.id)
    assert student_info["name"] == "Aitor Ortiz"
    assert student_info["birth_date"] == "2012-05-15"
    assert "age" in student_info

    # 2. Histórico de pruebas con métricas
    assert "results" in data
    assert len(data["results"]) == 2
    for r in data["results"]:
        assert "ppm" in r
        assert "comprehension" in r or "accuracy" in r

    # 3. Lecturas
    assert "readings" in data
    assert len(data["readings"]) == 1
    assert data["readings"][0]["title"] == "El Lazarillo de Tormes"

    # 4. Serie de evolución temporal
    assert "evolution" in data
    evo = data["evolution"]
    assert evo["has_insufficient_data"] is False
    assert len(evo["time_series"]) == 2
    assert "variations" in evo
    assert "ppm" in evo["variations"]
    assert "accuracy" in evo["variations"]

    # 5. Escenario 2: Fecha y hora de generación
    assert "generated_at" in data
    gen_at = datetime.datetime.fromisoformat(data["generated_at"])
    assert isinstance(gen_at, datetime.datetime)


def test_scenario_3_student_with_insufficient_data(client, setup_data):
    """
    Escenario 3: Alumno sin datos suficientes
    Dado un alumno con una sola prueba
    Cuando se solicitan los datos de su informe
    Entonces se devuelven sus datos con el indicador de evolución insuficiente
    Y no se incluye ninguna proyección.
    """
    s2 = setup_data["student_single"]
    sec1 = setup_data["section1"]

    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    resp = client.get(f"/api/v1/students/{s2.id}/report")
    assert resp.status_code == 200

    data = resp.get_json()
    assert "evolution" in data
    evo = data["evolution"]

    # Indicador de datos insuficientes
    assert evo["has_insufficient_data"] is True or data.get("has_insufficient_data") is True
    # No se incluye proyección
    assert data.get("projection") is None


def test_scenario_4_tutor_without_permission_forbidden(client, setup_data):
    """
    Escenario 4: Permiso sobre el alumno
    Dado un tutor sin la sección de ese alumno
    Cuando solicita su informe
    Entonces el sistema devuelve 403 Forbidden.
    """
    s3 = setup_data["student_other"]
    sec1 = setup_data["section1"]

    # Tutor asignado solo a Sección 1 (el alumno s3 está en Sección 2)
    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    resp = client.get(f"/api/v1/students/{s3.id}/report")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_scenario_5_audit_logging_on_report_generation(client, setup_data):
    """
    Escenario 5: Registro de la generación en auditoría
    Dado un informe generado
    Cuando termina la operación
    Entonces queda registrada en auditoría.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]

    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    clear_audit_logs()

    resp = client.get(f"/api/v1/students/{s1.id}/report")
    assert resp.status_code == 200

    logs = get_audit_logs(resource_type="students")
    report_logs = [log for log in logs if log["action"] == "GENERATE_STUDENT_REPORT"]
    assert len(report_logs) >= 1

    entry = report_logs[0]
    assert entry["resource_id"] == str(s1.id)


def test_access_control_unauthenticated_pending_and_not_found(client, setup_data):
    """
    Control de acceso: 401 sin sesión, 403 rol pendiente, 404 alumno inexistente.
    """
    s1_id = str(setup_data["student1"].id)

    # 1. 401 sin sesión
    app = create_app(NoBypassConfig)
    with app.test_client() as unauth_client:
        assert unauth_client.get(f"/api/v1/students/{s1_id}/report").status_code == 401

    # 2. 403 rol pendiente
    client.post("/api/dev/session", json={"role": "pendiente", "sections": []})
    assert client.get(f"/api/v1/students/{s1_id}/report").status_code == 403

    # 3. 404 alumno no encontrado
    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})
    non_existent = uuid.uuid4()
    resp = client.get(f"/api/v1/students/{non_existent}/report")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "NOT_FOUND"


def test_versioned_endpoint_v1_and_direct_alias(client, setup_data):
    """
    Verifica que GET /api/v1/students/{id}/report y GET /api/students/{id}/report funcionan idénticamente.
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]

    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    resp_v1 = client.get(f"/api/v1/students/{s1.id}/report")
    assert resp_v1.status_code == 200

    resp_direct = client.get(f"/api/students/{s1.id}/report")
    assert resp_direct.status_code == 200
    assert resp_v1.get_json()["id"] == resp_direct.get_json()["id"]
