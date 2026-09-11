import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.core.audit import clear_audit_logs, get_audit_logs
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
    """Fixture para crear datos base de prueba para BE-51."""
    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    section_a = Section(name="1º ESO A", center_id=center.id)
    section_b = Section(name="1º ESO B", center_id=center.id)
    section_empty = Section(name="1º ESO C", center_id=center.id)
    session.add_all([section_a, section_b, section_empty])
    session.flush()

    s1 = Student(name="Aitor Ortiz")
    s2 = Student(name="Leire Blanco")
    s3 = Student(name="Mikel Gómez")
    session.add_all([s1, s2, s3])
    session.flush()

    # Inicialmente s1 y s2 en sección A, s3 en sección B
    ss1 = StudentSection(student_id=s1.id, section_id=section_a.id)
    ss2 = StudentSection(student_id=s2.id, section_id=section_a.id)
    ss3 = StudentSection(student_id=s3.id, section_id=section_b.id)
    session.add_all([ss1, ss2, ss3])
    session.flush()

    # Dos pruebas en catálogo
    test_1af = Test(code="1AF", name="El halcón peregrino", words=120)
    test_1bf = Test(code="1BF", name="El fondo marino", words=150)
    session.add_all([test_1af, test_1bf])
    session.flush()

    # Resultados para sección A:
    # r1: s1 hace 1AF el 2026-01-15 (time=60s -> PPM=120.0, comprehension=85%)
    r1 = Result(
        student_id=s1.id,
        section_id=section_a.id,
        test_id=test_1af.id,
        test_date=datetime.date(2026, 1, 15),
        time=60,
        successes=18,
        mistakes=2,
    )
    # r2: s2 hace 1AF el 2026-03-20 (time=90s -> PPM=80.0, comprehension=62.5%)
    r2 = Result(
        student_id=s2.id,
        section_id=section_a.id,
        test_id=test_1af.id,
        test_date=datetime.date(2026, 3, 20),
        time=90,
        successes=15,
        mistakes=5,
    )
    # r3: s1 hace 1BF el 2026-05-10 (time=100s -> PPM=90.0, acc=80%)
    r3 = Result(
        student_id=s1.id,
        section_id=section_a.id,
        test_id=test_1bf.id,
        test_date=datetime.date(2026, 5, 10),
        time=100,
        successes=16,
        mistakes=4,
    )

    session.add_all([r1, r2, r3])
    session.commit()

    return {
        "center": center,
        "section_a": section_a,
        "section_b": section_b,
        "section_empty": section_empty,
        "students": [s1, s2, s3],
        "student_sections": [ss1, ss2, ss3],
        "tests": [test_1af, test_1bf],
        "results": [r1, r2, r3],
    }


def test_scenario_1_section_history_returns_all_results_with_student_and_test_metadata(client, setup_data):
    """
    Escenario 1: Histórico del grupo
    Dado una sección con alumnado y resultados registrados
    Cuando se consulta su historial de pruebas
    Entonces se devuelven los resultados de todos sus alumnos
    Y cada uno indica a qué alumno y a qué prueba corresponde con métricas
    Y devuelve 200 OK
    """
    sec_a = setup_data["section_a"]
    s1, s2, _ = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_a.id)]},
    )

    resp = client.get(f"/api/v1/sections/{sec_a.id}/results")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Comprobar orden cronológico y metadatos de alumno y prueba
    first = data[0]
    assert first["student_id"] == str(s1.id)
    assert first["student_name"] == "Aitor Ortiz"
    assert first["test_code"] == "1AF"
    assert first["test_name"] == "El halcón peregrino"
    assert first["test_date"] == "2026-01-15"
    assert first["ppm"] == 120.0
    assert first["comprehension"] == 85.0

    second = data[1]
    assert second["student_id"] == str(s2.id)
    assert second["student_name"] == "Leire Blanco"
    assert second["test_date"] == "2026-03-20"
    assert second["ppm"] == 80.0
    assert second["comprehension"] == 62.5

    # Comprobar ruta directa sin prefijo v1
    resp_direct = client.get(f"/api/sections/{sec_a.id}/results")
    assert resp_direct.status_code == 200
    assert len(resp_direct.get_json()) == 3


def test_scenario_2_group_by_test(client, setup_data):
    """
    Escenario 2: Agrupación por prueba
    Dado una sección donde se ha aplicado la misma prueba a alumnos del grupo
    Cuando se consulta el historial agrupado por prueba (?group_by=test)
    Entonces se ven juntos los resultados de esa aplicación
    Y se puede comparar a los alumnos entre sí
    """
    sec_a = setup_data["section_a"]
    test_1af, test_1bf = setup_data["tests"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_a.id)]},
    )

    resp = client.get(f"/api/v1/sections/{sec_a.id}/results?group_by=test")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2  # Dos pruebas distintas aplicadas en section_a: 1AF y 1BF

    # Encontrar grupo de 1AF
    group_1af = next((g for g in data if g["test_id"] == str(test_1af.id)), None)
    assert group_1af is not None
    assert group_1af["test_code"] == "1AF"
    assert group_1af["test_name"] == "El halcón peregrino"
    assert group_1af["results_count"] == 2
    assert len(group_1af["results"]) == 2

    student_ids_1af = {r["student_name"] for r in group_1af["results"]}
    assert student_ids_1af == {"Aitor Ortiz", "Leire Blanco"}

    # Encontrar grupo de 1BF
    group_1bf = next((g for g in data if g["test_id"] == str(test_1bf.id)), None)
    assert group_1bf is not None
    assert group_1bf["test_code"] == "1BF"
    assert group_1bf["results_count"] == 1
    assert group_1bf["results"][0]["student_name"] == "Aitor Ortiz"


def test_scenario_3_date_range_filtering(client, setup_data):
    """
    Escenario 3: Acotación por fechas
    Dado una sección con resultados de todo el curso
    Cuando se consulta acotando a un rango de fechas
    Entonces solo se devuelven los resultados de ese periodo
    """
    sec_a = setup_data["section_a"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_a.id)]},
    )

    # 1. Rango que solo incluye el resultado del 2026-03-20
    resp1 = client.get(f"/api/v1/sections/{sec_a.id}/results?start_date=2026-02-01&end_date=2026-04-01")
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert len(data1) == 1
    assert data1[0]["test_date"] == "2026-03-20"

    # 2. Prueba con alias from_date y to_date
    resp2 = client.get(f"/api/v1/sections/{sec_a.id}/results?from_date=2026-05-01&to_date=2026-05-31")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2) == 1
    assert data2[0]["test_date"] == "2026-05-10"

    # 3. Formato de fecha inválido devuelve 400 Bad Request
    resp_err1 = client.get(f"/api/v1/sections/{sec_a.id}/results?start_date=2026/02/01")
    assert resp_err1.status_code == 400
    assert "start_date" in resp_err1.get_json().get("error", "").lower()

    # 4. start_date > end_date devuelve 400 Bad Request
    resp_err2 = client.get(f"/api/v1/sections/{sec_a.id}/results?start_date=2026-06-01&end_date=2026-01-01")
    assert resp_err2.status_code == 400


def test_scenario_4_student_changed_section_remains_in_original_section_history(client, setup_data, session):
    """
    Escenario 4: Resultados de alumnos que cambiaron de grupo
    Dado un alumno que hizo una prueba estando en la sección A
    Y que después pasó a la sección B
    Cuando se consulta el historial de la sección A
    Entonces ese resultado sigue apareciendo en la sección A
    Y no se traslada a la B
    """
    sec_a = setup_data["section_a"]
    sec_b = setup_data["section_b"]
    s1 = setup_data["students"][0]

    # Modificar matrícula actual de s1 para trasladarlo a sec_b
    ss1 = setup_data["student_sections"][0]
    ss1.section_id = sec_b.id
    session.commit()

    # Coordinador pedagógico consulta sección A
    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    # Consulta Sección A: los resultados de s1 siguen apareciendo fielmente en Sección A
    resp_a = client.get(f"/api/v1/sections/{sec_a.id}/results")
    assert resp_a.status_code == 200
    data_a = resp_a.get_json()
    assert len(data_a) == 3
    s1_results_in_a = [r for r in data_a if r["student_id"] == str(s1.id)]
    assert len(s1_results_in_a) == 2  # Los 2 resultados originales realizados en A

    # Consulta Sección B: no contiene los resultados previos de s1 en A
    resp_b = client.get(f"/api/v1/sections/{sec_b.id}/results")
    assert resp_b.status_code == 200
    data_b = resp_b.get_json()
    s1_results_in_b = [r for r in data_b if r["student_id"] == str(s1.id)]
    assert len(s1_results_in_b) == 0  # No se trasladaron a la sección B


def test_scenario_5_empty_section_returns_empty_list_and_nonexistent_returns_404(client, setup_data):
    """
    Escenario 5: Sección sin resultados y sección inexistente
    Dado una sección sin ninguna prueba registrada
    Cuando se consulta su historial
    Entonces se devuelve una lista vacía con 200 OK.
    Y si no existe la sección, devuelve 404 Not Found.
    """
    sec_empty = setup_data["section_empty"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_empty.id)]},
    )

    # 1. Sección vacía devuelve [] con 200 OK
    resp_empty = client.get(f"/api/v1/sections/{sec_empty.id}/results")
    assert resp_empty.status_code == 200
    assert resp_empty.get_json() == []

    # 2. Con group_by=test en sección vacía devuelve []
    resp_empty_grouped = client.get(f"/api/v1/sections/{sec_empty.id}/results?group_by=test")
    assert resp_empty_grouped.status_code == 200
    assert resp_empty_grouped.get_json() == []

    # 3. Sección inexistente devuelve 404 Not Found
    random_uuid = uuid.uuid4()
    # Permitir como coordinator para saltar chequeo de permiso de sección
    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )
    resp_not_found = client.get(f"/api/v1/sections/{random_uuid}/results")
    assert resp_not_found.status_code == 404
    assert resp_not_found.get_json()["error"] == "NOT_FOUND"

    # 4. ID malformado devuelve 400 Bad Request
    resp_invalid_id = client.get("/api/v1/sections/id-no-valido/results")
    assert resp_invalid_id.status_code == 400


def test_scenario_6_tutor_without_assigned_section_returns_403(client, setup_data):
    """
    Escenario 6: Tutor sin la sección asignada
    Dado un tutor cuyas secciones no incluyen la consultada
    Cuando pide su historial
    Entonces el sistema devuelve 403 Forbidden
    """
    sec_a = setup_data["section_a"]
    sec_b = setup_data["section_b"]

    # Tutor asignado únicamente a sec_b
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec_b.id)]},
    )

    # Intenta consultar sec_a
    resp = client.get(f"/api/v1/sections/{sec_a.id}/results")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_pending_role_returns_403(client, setup_data):
    """
    Usuario con rol 'pendiente' debe recibir 403 Forbidden al consultar sección.
    """
    sec_a = setup_data["section_a"]

    client.post(
        "/api/dev/session",
        json={"role": "pendiente", "sections": [str(sec_a.id)]},
    )

    resp = client.get(f"/api/v1/sections/{sec_a.id}/results")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_unauthenticated_returns_401(setup_data):
    """
    Petición sin autenticación debe retornar 401 Unauthorized.
    """
    app = create_app(NoBypassConfig)
    unauth_client = app.test_client()

    sec_a = setup_data["section_a"]
    resp = unauth_client.get(f"/api/v1/sections/{sec_a.id}/results")
    assert resp.status_code == 401


def test_audit_logged_on_section_view(client, setup_data):
    """
    Verifica que la consulta del historial de sección queda registrada en auditoría
    por contener datos agregados de múltiples menores (Escenario 6 y notas de BE-51).
    """
    clear_audit_logs()
    sec_a = setup_data["section_a"]

    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    resp = client.get(f"/api/v1/sections/{sec_a.id}/results?group_by=test")
    assert resp.status_code == 200

    audit_logs = get_audit_logs()
    section_logs = [l for l in audit_logs if l["action"] == "VIEW_SECTION_RESULTS"]
    assert len(section_logs) == 1

    entry = section_logs[0]
    assert entry["resource_type"] == "sections"
    assert entry["resource_id"] == str(sec_a.id)
    assert entry["details"]["results_count"] == 3
    assert entry["details"]["group_by"] == "test"
