import datetime
import uuid
import pytest
from app import create_app
from app.config import TestingConfig
from app.core.audit import clear_audit_logs, get_audit_logs
from app.models.center import Center, Section
from app.models.student import Student
from app.models.test import Result, Test


class NoBypassConfig(TestingConfig):
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba."""
    center = Center(name="Centro Vitoria")
    session.add(center)
    session.flush()

    section1 = Section(name="1º ESO A", center_id=center.id)
    section2 = Section(name="1º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    student = Student(name="Aitor Ortiz")
    session.add(student)
    session.flush()

    # Prueba con 100 palabras
    test_model = Test(code="1AF", name="El halcón peregrino", words=100)
    session.add(test_model)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student": student,
        "test": test_model,
    }


def test_scenario_1_register_result_success(client, setup_data):
    """
    Escenario 1: Registro correcto (POST /api/v1/students/{student_id}/results)
    Dado un tutor con sesión activa y la sección del alumno asignada
    Cuando envía test_id, section_id, test_date, time, successes y mistakes
    Entonces el sistema crea el resultado asociado al alumno
    Y guarda la sección como foto del momento
    Y devuelve 201 Created con el recurso completo
    Y el recurso incluye el PPM calculado
    """
    student = setup_data["student"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    # Asignar la sección 1 al tutor activo en sesión
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-10",
        "time": 60,  # 60 segundos con 100 palabras -> PPM = 100.0
        "successes": 18,
        "mistakes": 2,
    }

    # Probar endpoint directo /api/v1/students/<id>/results
    resp = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()

    assert data["student_id"] == str(student.id)
    assert data["section_id"] == str(section.id)
    assert data["test_id"] == str(test_obj.id)
    assert data["test_date"] == "2026-03-10"
    assert data["time"] == 60
    assert data["successes"] == 18
    assert data["mistakes"] == 2
    # Verificación de PPM: 100 palabras en 1 min = 100.0
    assert data["ppm"] == 100.0
    assert "id" in data

    # Probar también el endpoint canónico /api/v1/students/<id>/results con tiempo diferente
    payload_v1 = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-15",
        "time": 120,  # 120 seg = 2 min -> PPM = 100 / 2 = 50.0
        "successes": 15,
        "mistakes": 3,
    }
    resp_v1 = client.post(f"/api/v1/students/{student.id}/results", json=payload_v1)
    assert resp_v1.status_code == 201
    assert resp_v1.get_json()["ppm"] == 50.0


def test_scenario_2_invalid_numeric_values(client, setup_data):
    """
    Escenario 2: Valores numéricos inválidos
    Dado un tutor con sesión activa
    Cuando envía un tiempo, aciertos o errores negativos
    Entonces el sistema rechaza la petición
    Y devuelve 400 Bad Request indicando el campo inválido
    Y no se crea ningún registro
    """
    student = setup_data["student"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    base_payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 2,
    }

    # 1. Tiempo negativo
    neg_time = dict(base_payload, time=-15)
    r1 = client.post(f"/api/v1/students/{student.id}/results", json=neg_time)
    assert r1.status_code == 400
    assert r1.get_json()["field"] == "time"

    # 2. Tiempo cero
    zero_time = dict(base_payload, time=0)
    r2 = client.post(f"/api/v1/students/{student.id}/results", json=zero_time)
    assert r2.status_code == 400
    assert r2.get_json()["field"] == "time"

    # 3. Aciertos negativos
    neg_succ = dict(base_payload, successes=-1)
    r3 = client.post(f"/api/v1/students/{student.id}/results", json=neg_succ)
    assert r3.status_code == 400
    assert r3.get_json()["field"] == "successes"

    # 4. Errores negativos
    neg_mist = dict(base_payload, mistakes=-5)
    r4 = client.post(f"/api/v1/students/{student.id}/results", json=neg_mist)
    assert r4.status_code == 400
    assert r4.get_json()["field"] == "mistakes"


def test_scenario_3_nonexistent_reference(client, setup_data):
    """
    Escenario 3: Referencia inexistente
    Dado un tutor con sesión activa
    Cuando envía un test_id o un section_id que no existe
    Entonces el sistema devuelve 400 Bad Request
    """
    student = setup_data["student"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    random_id = str(uuid.uuid4())

    # 1. test_id no existe
    r_test = client.post(
        f"/api/v1/students/{student.id}/results",
        json={
            "test_id": random_id,
            "section_id": str(section.id),
            "test_date": "2026-03-10",
            "time": 60,
            "successes": 15,
            "mistakes": 2,
        },
    )
    assert r_test.status_code == 400
    assert "prueba" in r_test.get_json()["error"].lower()

    # 2. section_id no existe
    r_sec = client.post(
        f"/api/v1/students/{student.id}/results",
        json={
            "test_id": str(test_obj.id),
            "section_id": random_id,
            "test_date": "2026-03-10",
            "time": 60,
            "successes": 15,
            "mistakes": 2,
        },
    )
    assert r_sec.status_code == 400
    assert "sección" in r_sec.get_json()["error"].lower()

    # 3. student_id no existe
    r_stu = client.post(
        f"/api/v1/students/{random_id}/results",
        json={
            "test_id": str(test_obj.id),
            "section_id": str(section.id),
            "test_date": "2026-03-10",
            "time": 60,
            "successes": 15,
            "mistakes": 2,
        },
    )
    assert r_stu.status_code == 400
    assert "alumno" in r_stu.get_json()["error"].lower()


def test_scenario_4_exact_duplicate_rejected(client, setup_data):
    """
    Escenario 4: Duplicado exacto
    Dado un alumno con un resultado de la prueba 1AF con fecha 10/03/2026
    Cuando se envía otro resultado de la prueba 1AF con esa misma fecha
    Entonces el sistema devuelve 409 Conflict
    """
    student = setup_data["student"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 2,
    }

    # Primer registro
    r1 = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert r1.status_code == 201

    # Segundo registro idéntico en fecha y prueba
    r2 = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert r2.status_code == 409
    assert r2.get_json()["error"] == "CONFLICT"

    # En una fecha distinta SÍ debe permitirse (BE-19 / reintento)
    payload_other_date = dict(payload, test_date="2026-03-11")
    r3 = client.post(f"/api/v1/students/{student.id}/results", json=payload_other_date)
    assert r3.status_code == 201


def test_scenario_5_request_without_session():
    """
    Escenario 5: Petición sin sesión
    Dado una petición sin cookie de sesión válida
    Cuando se llama al endpoint
    Entonces el sistema devuelve 401 Unauthorized
    Y no devuelve ninguna redirección
    """
    app_no_bypass = create_app(NoBypassConfig)
    client_no_auth = app_no_bypass.test_client()

    fake_id = uuid.uuid4()
    resp = client_no_auth.post(
        f"/api/v1/students/{fake_id}/results",
        json={
            "test_id": str(uuid.uuid4()),
            "section_id": str(uuid.uuid4()),
            "test_date": "2026-03-10",
            "time": 60,
            "successes": 15,
            "mistakes": 2,
        },
    )

    assert resp.status_code == 401
    assert resp.get_json()["error"] == "UNAUTHORIZED"
    # Sin redirección (código 3xx ni cabecera Location)
    assert "Location" not in resp.headers


def test_scenario_6_tutor_without_permission_on_section(client, setup_data):
    """
    Escenario 6: Tutor sin permiso sobre la sección
    Dado un tutor con sesión activa
    Y que la sección indicada no está entre las que tiene asignadas
    Cuando envía el resultado
    Entonces el sistema devuelve 403 Forbidden
    Y no se crea ningún registro
    """
    student = setup_data["student"]
    section1 = setup_data["section1"]
    section2 = setup_data["section2"]
    test_obj = setup_data["test"]

    # El tutor solo tiene asignada section1
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section1.id)]},
    )

    # Intenta registrar sobre section2
    payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section2.id),  # Sección no asignada
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 2,
    }

    resp = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # En cambio, un coordinador puede registrar en cualquier sección
    client.post("/api/dev/session", json={"role": "coordinator"})
    resp_coord = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp_coord.status_code == 201


def test_scenario_7_pending_role_user_rejected(client, setup_data):
    """
    Escenario 7: Usuario con rol pendiente
    Dado un usuario recién autenticado con rol "pendiente"
    Cuando intenta registrar un resultado
    Entonces el sistema devuelve 403 Forbidden
    """
    student = setup_data["student"]
    section1 = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post("/api/dev/session", json={"role": "pendiente"})

    payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section1.id),
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 2,
    }

    resp = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_scenario_8_audit_logged_on_success(client, setup_data):
    """
    Escenario 8: Registro en auditoría
    Dado un registro de resultado completado con éxito
    Cuando termina la operación
    Entonces queda una entrada de auditoría con usuario, fecha y recurso afectado
    """
    clear_audit_logs()

    student = setup_data["student"]
    section1 = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "email": "tutor.aitor@penascal.org", "sections": [str(section1.id)]},
    )

    payload = {
        "test_id": str(test_obj.id),
        "section_id": str(section1.id),
        "test_date": "2026-03-10",
        "time": 50,
        "successes": 20,
        "mistakes": 0,
    }

    resp = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp.status_code == 201
    created_id = resp.get_json()["id"]

    logs = get_audit_logs(resource_type="results", resource_id=created_id)
    assert len(logs) == 1
    audit_entry = logs[0]
    assert audit_entry["user"] == "tutor.aitor@penascal.org"
    assert audit_entry["action"] == "CREATE_RESULT"
    assert audit_entry["resource_type"] == "results"
    assert audit_entry["resource_id"] == str(created_id)
    assert audit_entry["date"] == datetime.date.today().isoformat()
