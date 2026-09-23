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
    """Fixture para crear datos de prueba representativos para BE-34."""
    clear_audit_logs()

    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    sec1 = Section(name="1º ESO A", center_id=center.id, academic_year="2025-2026")
    sec2 = Section(name="1º ESO B", center_id=center.id, academic_year="2025-2026")
    session.add_all([sec1, sec2])
    session.flush()

    # Alumno 1 (sec1): Tendencia NEGATIVA (180 -> 150 -> 120 PPM)
    s_negative = Student(
        name="Carlos Empeora",
        external_id="CAR-001",
    )
    # Alumno 2 (sec1): Tendencia PLANA (130 -> 130 -> 130 PPM)
    s_flat = Student(
        name="Paula Plana",
        external_id="PAU-002",
    )
    # Alumno 3 (sec1): Tendencia POSITIVA (100 -> 140 -> 180 PPM)
    s_improving = Student(
        name="Iker Mejora",
        external_id="IKE-003",
    )
    # Alumno 4 (sec1): Datos INSUFICIENTES (1 sola prueba registrada)
    s_single = Student(
        name="Sofia UnaPrueba",
        external_id="SOF-004",
    )
    # Alumno 5 (sec2): Alumno en otra sección (tendencia negativa)
    s_sec2_negative = Student(
        name="Marcos OtraSeccion",
        external_id="MAR-005",
    )

    session.add_all([s_negative, s_flat, s_improving, s_single, s_sec2_negative])
    session.flush()

    session.add_all([
        StudentSection(student_id=s_negative.id, section_id=sec1.id),
        StudentSection(student_id=s_flat.id, section_id=sec1.id),
        StudentSection(student_id=s_improving.id, section_id=sec1.id),
        StudentSection(student_id=s_single.id, section_id=sec1.id),
        StudentSection(student_id=s_sec2_negative.id, section_id=sec2.id),
    ])

    test1 = Test(code="1CL", name="Prueba 1", words=300)
    test2 = Test(code="2CL", name="Prueba 2", words=300)
    test3 = Test(code="3CL", name="Prueba 3", words=300)
    session.add_all([test1, test2, test3])
    session.flush()

    d1 = datetime.date(2025, 10, 1)
    d2 = datetime.date(2025, 11, 15)
    d3 = datetime.date(2025, 12, 20)

    # 1. Alumno negativo: time=100 (180 PPM) -> time=120 (150 PPM) -> time=150 (120 PPM)
    res_neg = [
        Result(student_id=s_negative.id, section_id=sec1.id, test_id=test1.id, test_date=d1, time=100, successes=15, mistakes=3),
        Result(student_id=s_negative.id, section_id=sec1.id, test_id=test2.id, test_date=d2, time=120, successes=15, mistakes=3),
        Result(student_id=s_negative.id, section_id=sec1.id, test_id=test3.id, test_date=d3, time=150, successes=15, mistakes=3),
    ]

    # 2. Alumno plano: time=138.46 (~130 PPM en todas) -> use words=260, time=120 -> 130 PPM
    # Con words=300: time=138 -> 130.43 PPM
    res_flat = [
        Result(student_id=s_flat.id, section_id=sec1.id, test_id=test1.id, test_date=d1, time=138, successes=15, mistakes=3),
        Result(student_id=s_flat.id, section_id=sec1.id, test_id=test2.id, test_date=d2, time=138, successes=15, mistakes=3),
        Result(student_id=s_flat.id, section_id=sec1.id, test_id=test3.id, test_date=d3, time=138, successes=15, mistakes=3),
    ]

    # 3. Alumno en progreso: time=180 (100 PPM) -> time=128 (140.6 PPM) -> time=100 (180 PPM)
    res_imp = [
        Result(student_id=s_improving.id, section_id=sec1.id, test_id=test1.id, test_date=d1, time=180, successes=15, mistakes=3),
        Result(student_id=s_improving.id, section_id=sec1.id, test_id=test2.id, test_date=d2, time=128, successes=15, mistakes=3),
        Result(student_id=s_improving.id, section_id=sec1.id, test_id=test3.id, test_date=d3, time=100, successes=15, mistakes=3),
    ]

    # 4. Alumno con 1 sola prueba
    res_single = [
        Result(student_id=s_single.id, section_id=sec1.id, test_id=test1.id, test_date=d1, time=120, successes=15, mistakes=3),
    ]

    # 5. Alumno en sec2 (negativo)
    res_sec2 = [
        Result(student_id=s_sec2_negative.id, section_id=sec2.id, test_id=test1.id, test_date=d1, time=100, successes=15, mistakes=3),
        Result(student_id=s_sec2_negative.id, section_id=sec2.id, test_id=test2.id, test_date=d2, time=120, successes=15, mistakes=3),
        Result(student_id=s_sec2_negative.id, section_id=sec2.id, test_id=test3.id, test_date=d3, time=150, successes=15, mistakes=3),
    ]

    session.add_all(res_neg + res_flat + res_imp + res_single + res_sec2)
    session.commit()

    return {
        "sec1": sec1,
        "sec2": sec2,
        "s_negative": s_negative,
        "s_flat": s_flat,
        "s_improving": s_improving,
        "s_single": s_single,
        "s_sec2_negative": s_sec2_negative,
    }


def test_scenario_1_negative_trend_detection(client, setup_data):
    """
    Escenario 1: Detección de tendencia negativa.
    Dado alumnos cuyos resultados empeoran en las últimas pruebas,
    aparecen en la lista de alumnos sin progreso.
    """
    s_negative = setup_data["s_negative"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get("/api/v1/students/no-progress")
    assert resp.status_code == 200

    data = resp.get_json()
    no_progress = data["no_progress"]
    no_prog_ids = [item["student_id"] for item in no_progress]

    assert str(s_negative.id) in no_prog_ids

    neg_entry = next(item for item in no_progress if item["student_id"] == str(s_negative.id))
    assert neg_entry["trend_type"] == "negative"
    assert neg_entry["slope"] < 0
    assert neg_entry["variation"] < 0
    assert neg_entry["classification"] == "no_progress"


def test_scenario_2_flat_trend_detection(client, setup_data):
    """
    Escenario 2: Tendencia plana.
    Dado un alumno cuyos resultados no mejoran ni empeoran,
    cuando se aplica el umbral, se incluye en la lista si su variación está por debajo.
    """
    s_flat = setup_data["s_flat"]
    s_improving = setup_data["s_improving"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get("/api/v1/students/no-progress?threshold=0.0")
    assert resp.status_code == 200

    data = resp.get_json()
    no_progress = data["no_progress"]
    no_prog_ids = [item["student_id"] for item in no_progress]

    # El plano aparece en no_progress
    assert str(s_flat.id) in no_prog_ids
    flat_entry = next(item for item in no_progress if item["student_id"] == str(s_flat.id))
    assert flat_entry["trend_type"] == "flat"
    assert flat_entry["classification"] == "no_progress"

    # El que mejora NO aparece en no_progress
    assert str(s_improving.id) not in no_prog_ids
    improving_ids = [item["student_id"] for item in data["improving"]]
    assert str(s_improving.id) in improving_ids


def test_scenario_3_insufficient_data_distinction(client, setup_data):
    """
    Escenario 3: Distinción de datos insuficientes (CRÍTICO).
    Dado un alumno con una sola prueba, aparece clasificado como
    "sin datos suficientes" y NO como "sin progreso".
    """
    s_single = setup_data["s_single"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get("/api/v1/students/no-progress")
    assert resp.status_code == 200

    data = resp.get_json()

    # 1. Aparece en insufficient_data
    insufficient = data["insufficient_data"]
    insufficient_ids = [item["student_id"] for item in insufficient]
    assert str(s_single.id) in insufficient_ids

    entry = next(item for item in insufficient if item["student_id"] == str(s_single.id))
    assert entry["classification"] == "insufficient_data"
    assert entry["has_sufficient_data"] is False
    assert entry["total_tests"] == 1
    assert entry["reason"] is not None

    # 2. NO aparece en no_progress
    no_prog_ids = [item["student_id"] for item in data["no_progress"]]
    assert str(s_single.id) not in no_prog_ids


def test_scenario_4_configurable_parameters(client, setup_data):
    """
    Escenario 4: Parámetros configurables.
    Cuando se consulta indicando otro umbral y otro número de pruebas,
    el cálculo usa esos parámetros.
    """
    s_single = setup_data["s_single"]
    s_improving = setup_data["s_improving"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    # Si n_tests=2, s_single sigue siendo insuficiente (tiene 1 prueba)
    resp_n2 = client.get("/api/v1/students/no-progress?n_tests=2")
    assert resp_n2.status_code == 200
    data_n2 = resp_n2.get_json()
    assert data_n2["parameters"]["n_tests"] == 2

    # Si ponemos umbral muy alto (threshold=100.0), incluso s_improving (que ganó 80 PPM)
    # queda por debajo del umbral y se considera sin progreso suficiente
    resp_thresh = client.get("/api/v1/students/no-progress?threshold=100.0")
    assert resp_thresh.status_code == 200
    data_thresh = resp_thresh.get_json()
    assert data_thresh["parameters"]["threshold"] == 100.0

    no_prog_ids = [item["student_id"] for item in data_thresh["no_progress"]]
    assert str(s_improving.id) in no_prog_ids


def test_scenario_5_tutor_role_scoping(client, setup_data):
    """
    Escenario 5: Alcance por rol.
    Dado un tutor con una sección asignada (sec1),
    solo aparecen alumnos de su sección.
    """
    sec1 = setup_data["sec1"]
    sec2 = setup_data["sec2"]
    s_sec2_negative = setup_data["s_sec2_negative"]

    # Iniciar sesión como tutor de sec1 únicamente
    client.post("/api/dev/session", json={"role": "tutor", "sections": [str(sec1.id)]})

    resp = client.get("/api/v1/students/no-progress")
    assert resp.status_code == 200

    data = resp.get_json()
    all_returned_ids = [item["student_id"] for item in data["no_progress"]] + [
        item["student_id"] for item in data["insufficient_data"]
    ] + [item["student_id"] for item in data["improving"]]

    # El alumno de sec2 NO debe aparecer
    assert str(s_sec2_negative.id) not in all_returned_ids

    # Si el tutor intenta filtrar por la sección 2 (no asignada) -> 403 Forbidden
    resp_unauthorized = client.get(f"/api/v1/students/no-progress?section_id={sec2.id}")
    assert resp_unauthorized.status_code == 403
    assert resp_unauthorized.get_json()["error"] == "FORBIDDEN"


def test_access_control_and_audit(client, setup_data):
    """
    Verifica 401 sin sesión, 403 para rol pendiente, y registro en auditoría.
    """
    # 1. 401 sin sesión
    no_bypass_app = create_app(NoBypassConfig)
    with no_bypass_app.test_client() as unauth_client:
        assert unauth_client.get("/api/v1/students/no-progress").status_code == 401

    # 2. 403 para rol 'pendiente'
    client.post("/api/dev/session", json={"role": "pendiente", "sections": []})
    assert client.get("/api/v1/students/no-progress").status_code == 403

    # 3. 400 Bad Request por parámetros inválidos
    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})
    assert client.get("/api/v1/students/no-progress?n_tests=invalido").status_code == 400
    assert client.get("/api/v1/students/no-progress?threshold=invalido").status_code == 400
    assert client.get("/api/v1/students/no-progress?section_id=no-es-uuid").status_code == 400

    # 4. Auditoría
    clear_audit_logs()
    resp = client.get("/api/v1/students/no-progress")
    assert resp.status_code == 200

    logs = get_audit_logs(resource_type="students")
    actions = [l["action"] for l in logs]
    assert "DETECT_NO_PROGRESS_STUDENTS" in actions
