import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.core.audit import clear_audit_logs, get_audit_logs
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Result, Test
from app.repositories.result_repository import ResultRepository


class NoBypassConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-20."""
    center = Center(name="Centro Vitoria")
    session.add(center)
    session.flush()

    section1 = Section(name="1º ESO A", center_id=center.id)
    section2 = Section(name="1º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    student_with_results = Student(name="Aitor Ortiz")
    student_without_results = Student(name="Miren Goikoetxea")
    student_other_section = Student(name="Jon Zabaleta")
    session.add_all([student_with_results, student_without_results, student_other_section])
    session.flush()

    # Vincular a secciones
    session.add_all([
        StudentSection(student_id=student_with_results.id, section_id=section1.id),
        StudentSection(student_id=student_without_results.id, section_id=section1.id),
        StudentSection(student_id=student_other_section.id, section_id=section2.id),
    ])
    session.flush()

    # Pruebas con palabras conocidas
    test_1af = Test(code="1AF", name="El halcón peregrino", words=120)
    test_2bf = Test(code="2BF", name="La tortuga marina", words=150)
    session.add_all([test_1af, test_2bf])
    session.flush()

    # Resultados para student_with_results: fechas desordenadas a propósito
    # R1: 2026-03-24, test_1af, time=60s, 18 aciertos, 2 errores -> PPM=120.0, comprehension=85.0%
    r1 = Result(
        student_id=student_with_results.id,
        section_id=section1.id,
        test_id=test_1af.id,
        test_date=datetime.date(2026, 3, 24),
        time=60,
        successes=18,
        mistakes=2,
    )
    # R2: 2026-03-10, test_1af, time=72s, 15 aciertos, 5 errores -> PPM=100.0, comprehension=62.5%
    r2 = Result(
        student_id=student_with_results.id,
        section_id=section1.id,
        test_id=test_1af.id,
        test_date=datetime.date(2026, 3, 10),
        time=72,
        successes=15,
        mistakes=5,
    )
    # R3: 2026-04-05, test_2bf, time=90s, 19 aciertos, 1 error -> PPM=100.0, comprehension=92.5%
    r3 = Result(
        student_id=student_with_results.id,
        section_id=section1.id,
        test_id=test_2bf.id,
        test_date=datetime.date(2026, 4, 5),
        time=90,
        successes=19,
        mistakes=1,
    )
    session.add_all([r1, r2, r3])
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student_with_results": student_with_results,
        "student_without_results": student_without_results,
        "student_other_section": student_other_section,
        "test_1af": test_1af,
        "test_2bf": test_2bf,
    }


def test_scenario_1_full_ordered_history(client, setup_data):
    """
    Escenario 1: Histórico completo
    Dado un alumno con varios resultados registrados
    Cuando se consulta GET /api/v1/students/{id}/results
    Entonces se devuelven todos sus resultados ordenados por fecha
    Y devuelve 200 OK
    """
    student = setup_data["student_with_results"]

    client.post("/api/dev/session", json={"role": "coordinator"})

    # Probar endpoint directo /api/v1/students/{id}/results
    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200
    results = resp.get_json()
    assert len(results) == 3

    # Comprobar orden cronológico por fecha ascendente
    assert results[0]["test_date"] == "2026-03-10"
    assert results[1]["test_date"] == "2026-03-24"
    assert results[2]["test_date"] == "2026-04-05"

    # Probar también endpoint canónico /api/v1/students/{id}/results
    resp_v1 = client.get(f"/api/v1/students/{student.id}/results")
    assert resp_v1.status_code == 200
    assert len(resp_v1.get_json()) == 3


def test_scenario_2_test_metadata_included(client, setup_data):
    """
    Escenario 2: Datos de la prueba incluidos
    Dado un resultado de la prueba 1AF
    Cuando se consulta el histórico
    Entonces cada resultado incluye el nombre y el número de palabras de la prueba
    Y no hace falta una segunda llamada para obtenerlos
    """
    student = setup_data["student_with_results"]

    client.post("/api/dev/session", json={"role": "coordinator"})

    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200
    results = resp.get_json()

    # Primer resultado (2026-03-10, test_1af: 'El halcón peregrino', 120 palabras)
    r1 = results[0]
    assert r1["test_code"] == "1AF"
    assert r1["test_name"] == "El halcón peregrino"
    assert r1["test_words"] == 120
    assert r1["words"] == 120

    # Tercer resultado (2026-04-05, test_2bf: 'La tortuga marina', 150 palabras)
    r3 = results[2]
    assert r3["test_code"] == "2BF"
    assert r3["test_name"] == "La tortuga marina"
    assert r3["test_words"] == 150
    assert r3["words"] == 150


def test_scenario_3_calculated_metrics(client, setup_data):
    """
    Escenario 3: Métricas calculadas
    Dado un resultado con tiempo, aciertos y errores
    Cuando se consulta el histórico
    Entonces cada resultado incluye su PPM y su porcentaje de aciertos
    """
    student = setup_data["student_with_results"]

    client.post("/api/dev/session", json={"role": "coordinator"})

    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200
    results = resp.get_json()

    # 1. Fecha 2026-03-10: 120 palabras en 72s -> PPM = (120/72)*60 = 100.0. Aciertos 15/20 = 75.0%
    assert results[0]["ppm"] == 100.0
    assert results[0]["comprehension"] == 62.5

    # 2. Fecha 2026-03-24: 120 palabras en 60s -> PPM = 120.0. Aciertos 18/20 = 90.0%
    assert results[1]["ppm"] == 120.0
    assert results[1]["comprehension"] == 85.0

    # 3. Fecha 2026-04-05: 150 palabras en 90s -> PPM = (150/90)*60 = 100.0. Aciertos 19/20 = 95.0%
    assert results[2]["ppm"] == 100.0
    assert results[2]["comprehension"] == 92.5


def test_scenario_4_student_without_results(client, setup_data):
    """
    Escenario 4: Alumno sin resultados
    Dado un alumno sin ninguna prueba registrada
    Cuando se consulta su histórico
    Entonces se devuelve una lista vacía
    Y devuelve 200 OK, no 404
    """
    student = setup_data["student_without_results"]

    client.post("/api/dev/session", json={"role": "coordinator"})

    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_scenario_5_nonexistent_student_returns_404(client):
    """
    Escenario 5: Alumno inexistente
    Dado un identificador de alumno que no existe
    Cuando se consulta su histórico
    Entonces el sistema devuelve 404 Not Found
    """
    client.post("/api/dev/session", json={"role": "coordinator"})

    nonexistent_id = uuid.uuid4()
    resp = client.get(f"/api/v1/students/{nonexistent_id}/results")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "NOT_FOUND"
    assert "alumno" in data["message"].lower()


def test_scenario_6_tutor_without_permission(client, setup_data):
    """
    Escenario 6: Tutor sin permiso
    Dado un tutor cuyas secciones no incluyen a ese alumno
    Cuando consulta su histórico
    Entonces el sistema devuelve 403 Forbidden
    """
    student_sec2 = setup_data["student_other_section"]
    section1 = setup_data["section1"]

    # El tutor solo tiene asignada la sección 1
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section1.id)]},
    )

    # Intenta consultar alumno de la sección 2
    resp = client.get(f"/api/v1/students/{student_sec2.id}/results")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # En cambio, para un alumno de su sección (sección 1) sí tiene permiso
    student_sec1 = setup_data["student_with_results"]
    resp_ok = client.get(f"/api/v1/students/{student_sec1.id}/results")
    assert resp_ok.status_code == 200


def test_audit_logged_on_history_view(client, setup_data):
    """
    Seguridad / Auditoría (BE-44 y notas de BE-20):
    La consulta del histórico queda registrada en la auditoría con el usuario y el alumno consultado.
    """
    clear_audit_logs()

    student = setup_data["student_with_results"]
    section1 = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={
            "role": "tutor",
            "email": "tutor.maria@penascal.org",
            "sections": [str(section1.id)],
        },
    )

    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200

    logs = get_audit_logs(resource_type="students", resource_id=str(student.id))
    assert len(logs) == 1
    entry = logs[0]
    assert entry["user"] == "tutor.maria@penascal.org"
    assert entry["action"] == "VIEW_STUDENT_RESULTS"
    assert entry["resource_type"] == "students"
    assert entry["resource_id"] == str(student.id)
    assert entry["details"]["results_count"] == 3


def test_repository_eager_loads_test_relationship(session, setup_data):
    """
    T-BE20-01: Verificación de que ResultRepository.get_by_student realiza
    la unión (joinedload) y tiene la relación test precargada.
    """
    student = setup_data["student_with_results"]
    repo = ResultRepository(session)

    results = repo.get_by_student(student.id, order_asc=True)
    assert len(results) == 3

    # Las entidades Test deben estar disponibles sin lanzar queries diferidas
    for r in results:
        assert r.test is not None
        assert r.test.words > 0
        assert r.test.name != ""
