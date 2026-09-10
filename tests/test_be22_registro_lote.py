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
    """Fixture para crear datos base de prueba para BE-22."""
    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    section1 = Section(name="2º ESO A", center_id=center.id)
    section2 = Section(name="2º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    s1 = Student(name="Aitor Ortiz")
    s2 = Student(name="Leire Blanco")
    s3 = Student(name="Mikel Gómez")
    s4 = Student(name="Nerea Ruiz")
    s5 = Student(name="Jon Etxebarria")
    session.add_all([s1, s2, s3, s4, s5])
    session.flush()

    for st in [s1, s2, s3, s4, s5]:
        ss = StudentSection(student_id=st.id, section_id=section1.id)
        session.add(ss)
    session.flush()

    # Prueba con 120 palabras
    test_1af = Test(code="1AF", name="El halcón peregrino", words=120)
    session.add(test_1af)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "students": [s1, s2, s3, s4, s5],
        "test": test_1af,
    }


def test_scenario_1_valid_batch_creates_all_results_with_ppm(client, setup_data, session):
    """
    Escenario 1: Lote correcto
    Dado un tutor con la sección asignada
    Cuando envía una prueba, una fecha y una lista de resultados por alumno
    Entonces se registran todos los resultados en una sola transacción
    Y devuelve 201 Created con el resumen de lo registrado (y PPM calculado)
    """
    clear_audit_logs()
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    # Autenticar como tutor de la sección 1
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-15",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 18,
                "mistakes": 2,
            },
            {
                "student_id": str(students[1].id),
                "time": 80,
                "successes": 15,
                "mistakes": 5,
            },
            {
                "student_id": str(students[2].id),
                "time": 100,
                "successes": 12,
                "mistakes": 8,
            },
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["registered_count"] == 3
    assert data["absent_count"] == 0
    assert data["test_id"] == str(test.id)
    assert data["section_id"] == str(sec.id)
    assert data["test_date"] == "2026-03-15"
    assert len(data["results"]) == 3

    # Verificar cálculo de PPM en cada resultado (120 words / time * 60)
    # student 0: (120/60)*60 = 120.0 PPM
    assert data["results"][0]["student_id"] == str(students[0].id)
    assert data["results"][0]["ppm"] == 120.0
    # student 1: (120/80)*60 = 90.0 PPM
    assert data["results"][1]["student_id"] == str(students[1].id)
    assert data["results"][1]["ppm"] == 90.0
    # student 2: (120/100)*60 = 72.0 PPM
    assert data["results"][2]["student_id"] == str(students[2].id)
    assert data["results"][2]["ppm"] == 72.0

    # Verificar persistencia en base de datos
    session.expire_all()
    db_results = session.query(Result).filter_by(test_id=test.id, section_id=sec.id).all()
    assert len(db_results) == 3

    # Verificar auditoría
    audit_logs = get_audit_logs()
    batch_logs = [l for l in audit_logs if l["action"] == "BATCH_REGISTER_RESULTS"]
    assert len(batch_logs) == 1
    assert batch_logs[0]["details"]["registered_count"] == 3


def test_scenario_2_absent_students_omitted_without_zeros(client, setup_data, session):
    """
    Escenario 2: Alumnos ausentes omitidos
    Dado un lote donde alumnos vienen sin datos o marcados ausentes
    Cuando se procesa
    Entonces esos alumnos no generan ningún resultado
    Y no se registran con valores a cero
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # Enviamos 4 alumnos: 2 con datos, 1 marcado ausente, 1 sin datos (None / vacíos)
    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-16",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 20,
                "mistakes": 0,
            },
            {
                "student_id": str(students[1].id),
                "absent": True,  # Ausente explícito
            },
            {
                "student_id": str(students[2].id),
                "time": None,  # Dejado en blanco
                "successes": None,
                "mistakes": None,
            },
            {
                "student_id": str(students[3].id),
                "time": 75,
                "successes": 19,
                "mistakes": 1,
            },
        ],
    }

    resp = client.post("/api/results/batch", json=batch_payload)
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["registered_count"] == 2
    assert data["absent_count"] == 2
    assert len(data["results"]) == 2

    # Verificar que en base de datos NO existen resultados para student 1 y student 2
    session.expire_all()
    s1_res = session.query(Result).filter_by(student_id=students[1].id, test_date=datetime.date(2026, 3, 16)).first()
    s2_res = session.query(Result).filter_by(student_id=students[2].id, test_date=datetime.date(2026, 3, 16)).first()
    assert s1_res is None
    assert s2_res is None

    # Comprobar que solo los presentes están guardados
    saved_student_ids = {str(r.student_id) for r in session.query(Result).filter_by(test_date=datetime.date(2026, 3, 16)).all()}
    assert saved_student_ids == {str(students[0].id), str(students[3].id)}


def test_scenario_3_invalid_row_identifies_affected_row(client, setup_data, session):
    """
    Escenario 3: Una fila inválida
    Dado un lote donde una fila tiene un tiempo negativo o aciertos negativos
    Cuando se procesa
    Entonces el sistema indica qué fila ha fallado y por qué (index, student_id, field, error)
    Y la respuesta permite a la interfaz señalar esa fila concreta
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-17",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            },
            {
                "student_id": str(students[1].id),
                "time": -45,  # Inválido: tiempo negativo
                "successes": 10,
                "mistakes": 3,
            },
            {
                "student_id": str(students[2].id),
                "time": 70,
                "successes": -5,  # Inválido: aciertos negativos
                "mistakes": 1,
            },
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["error"] == "BATCH_VALIDATION_ERROR"
    assert "errors" in data
    assert len(data["errors"]) >= 2

    # Verificar que se reporta la fila 1 (students[1])
    row1_error = next((e for e in data["errors"] if e["index"] == 1), None)
    assert row1_error is not None
    assert row1_error["student_id"] == str(students[1].id)
    assert row1_error["field"] == "time"

    # Verificar que se reporta la fila 2 (students[2])
    row2_error = next((e for e in data["errors"] if e["index"] == 2), None)
    assert row2_error is not None
    assert row2_error["student_id"] == str(students[2].id)
    assert row2_error["field"] == "successes"


def test_scenario_4_atomicity_on_failure_no_partial_records(client, setup_data, session):
    """
    Escenario 4: Atomicidad
    Dado un lote que falla a mitad de proceso (por ejemplo fila inválida o alumno no existente)
    Cuando se produce el error
    Entonces no queda ningún resultado del lote registrado a medias
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-18",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            },
            {
                "student_id": str(students[1].id),
                "time": 80,
                "successes": 12,
                "mistakes": 4,
            },
            {
                "student_id": str(students[2].id),
                "time": 0,  # Inválido: tiempo debe ser > 0
                "successes": 10,
                "mistakes": 1,
            },
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 400

    # Comprobar que en base de datos NO se guardó ningún resultado para esa fecha
    session.expire_all()
    count = session.query(Result).filter_by(test_date=datetime.date(2026, 3, 18)).count()
    assert count == 0


def test_scenario_5_duplicate_in_batch_or_db(client, setup_data, session):
    """
    Escenario 5: Duplicado dentro del lote y contra BD
    Dado un alumno que ya tiene resultado en esa fecha o aparece dos veces en el lote
    Cuando se procesa
    Entonces esa fila se rechaza indicando el conflicto con el estudiante
    Y no se persiste nada (política de atomicidad)
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # 1. Caso Duplicado dentro del mismo lote
    payload_internal_dup = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-19",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            },
            {
                "student_id": str(students[0].id),  # Mismo alumno repetido en el lote
                "time": 65,
                "successes": 14,
                "mistakes": 3,
            },
        ],
    }
    r1 = client.post("/api/v1/results/batch", json=payload_internal_dup)
    assert r1.status_code == 400
    errors1 = r1.get_json().get("errors", [])
    assert any(e["student_id"] == str(students[0].id) and "duplicado" in e["error"].lower() for e in errors1)

    # 2. Caso Duplicado contra resultado ya existente en BD
    existing_result = Result(
        student_id=students[1].id,
        section_id=sec.id,
        test_id=test.id,
        test_date=datetime.date(2026, 3, 20),
        time=70,
        successes=15,
        mistakes=2,
    )
    session.add(existing_result)
    session.commit()

    payload_db_dup = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-20",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            },
            {
                "student_id": str(students[1].id),  # Ya existe en BD para esta prueba y fecha
                "time": 75,
                "successes": 14,
                "mistakes": 3,
            },
        ],
    }
    r2 = client.post("/api/v1/results/batch", json=payload_db_dup)
    assert r2.status_code == 400
    errors2 = r2.get_json().get("errors", [])
    assert any(e["student_id"] == str(students[1].id) and e["field"] == "test_date" for e in errors2)

    # Verificar que student 0 no se persistió
    session.expire_all()
    s0_res = session.query(Result).filter_by(student_id=students[0].id, test_date=datetime.date(2026, 3, 20)).first()
    assert s0_res is None


def test_scenario_6_tutor_without_permission_returns_403(client, setup_data, session):
    """
    Escenario 6: Tutor sin permiso
    Dado un tutor sin la sección asignada
    Cuando envía el lote
    Entonces el sistema devuelve 403 Forbidden
    """
    sec1 = setup_data["section1"]
    sec2 = setup_data["section2"]
    test = setup_data["test"]
    students = setup_data["students"]

    # Autenticar como tutor asignado únicamente a sec2
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec2.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec1.id),  # Intenta registrar para sec1
        "test_date": "2026-03-21",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            }
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # Verificar que no se guardó nada
    session.expire_all()
    count = session.query(Result).filter_by(test_date=datetime.date(2026, 3, 21)).count()
    assert count == 0


def test_pending_role_returns_403(client, setup_data):
    """
    Usuario con rol 'pendiente' debe recibir 403 Forbidden.
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "pendiente", "sections": [str(sec.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-22",
        "results": [
            {
                "student_id": str(students[0].id),
                "time": 60,
                "successes": 15,
                "mistakes": 2,
            }
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 403


def test_unauthenticated_returns_401(setup_data):
    """
    Petición sin autenticar debe retornar 401 Unauthorized.
    """
    app = create_app(NoBypassConfig)
    unauth_client = app.test_client()

    sec = setup_data["section1"]
    test = setup_data["test"]

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-22",
        "results": [],
    }

    resp = unauth_client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 401


def test_all_absent_students_returns_201_zero_registered(client, setup_data, session):
    """
    Lote donde todos los alumnos están ausentes devuelve 201 y registered_count=0.
    """
    sec = setup_data["section1"]
    test = setup_data["test"]
    students = setup_data["students"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    batch_payload = {
        "test_id": str(test.id),
        "section_id": str(sec.id),
        "test_date": "2026-03-23",
        "results": [
            {"student_id": str(students[0].id), "absent": True},
            {"student_id": str(students[1].id), "time": None},
        ],
    }

    resp = client.post("/api/v1/results/batch", json=batch_payload)
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["registered_count"] == 0
    assert data["absent_count"] == 2
    assert data["results"] == []

    session.expire_all()
    count = session.query(Result).filter_by(test_date=datetime.date(2026, 3, 23)).count()
    assert count == 0
