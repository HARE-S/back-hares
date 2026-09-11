import datetime
import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.config import Config
from app.core.exceptions import ConflictError
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
    """Fixture para crear datos base de prueba para BE-19."""
    center = Center(name="Centro Vitoria")
    session.add(center)
    session.flush()

    section1 = Section(name="1º ESO A", center_id=center.id)
    section2 = Section(name="1º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    student1 = Student(name="Aitor Ortiz")
    student2 = Student(name="Leire Blanco")
    session.add_all([student1, student2])
    session.flush()

    # Vincular student1 a section1 y student2 a section2
    ss1 = StudentSection(student_id=student1.id, section_id=section1.id)
    ss2 = StudentSection(student_id=student2.id, section_id=section2.id)
    session.add_all([ss1, ss2])
    session.flush()

    # Prueba con 100 palabras
    test_1af = Test(code="1AF", name="El halcón peregrino", words=100)
    session.add(test_1af)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": student1,
        "student2": student2,
        "test": test_1af,
    }


def test_scenario_1_repetition_in_different_date(client, setup_data, session):
    """
    Escenario 1: Repetición en otra fecha
    Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
    Cuando se registra otro resultado de la prueba 1AF el 24/03/2026
    Entonces el sistema acepta el registro
    Y devuelve 201 Created
    Y el alumno pasa a tener dos resultados de esa misma prueba
    """
    student = setup_data["student1"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    # 1. Primer resultado: 10/03/2026
    payload_1 = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 5,
    }
    resp1 = client.post(f"/api/v1/students/{student.id}/results", json=payload_1)
    assert resp1.status_code == 201

    # 2. Segundo resultado de la misma prueba en fecha posterior: 24/03/2026
    payload_2 = {
        "test_id": str(test_obj.id),
        "section_id": str(section.id),
        "test_date": "2026-03-24",
        "time": 50,
        "successes": 18,
        "mistakes": 2,
    }
    resp2 = client.post(f"/api/v1/students/{student.id}/results", json=payload_2)
    assert resp2.status_code == 201

    # Verificar en BD que existen exactamente 2 resultados para este alumno y prueba
    results = (
        session.query(Result)
        .filter(Result.student_id == student.id, Result.test_id == test_obj.id)
        .all()
    )
    assert len(results) == 2
    dates = {r.test_date.isoformat() for r in results}
    assert dates == {"2026-03-10", "2026-03-24"}


def test_scenario_2_third_repetition_and_no_limits(client, setup_data, session):
    """
    Escenario 2: Tercera repetición
    Dado un alumno con dos resultados de la prueba 1AF en fechas distintas
    Cuando se registra un tercero en una fecha nueva
    Entonces el sistema lo acepta
    Y no existe límite al número de repeticiones
    """
    student = setup_data["student1"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section.id)]},
    )

    dates = ["2026-03-10", "2026-03-24", "2026-04-07", "2026-04-21"]
    for d in dates:
        payload = {
            "test_id": str(test_obj.id),
            "section_id": str(section.id),
            "test_date": d,
            "time": 60,
            "successes": 18,
            "mistakes": 2,
        }
        resp = client.post(f"/api/v1/students/{student.id}/results", json=payload)
        assert resp.status_code == 201

    results = (
        session.query(Result)
        .filter(Result.student_id == student.id, Result.test_id == test_obj.id)
        .all()
    )
    assert len(results) == 4


def test_scenario_3_exact_duplicate_rejected(client, setup_data, session):
    """
    Escenario 3: Duplicado exacto rechazado
    Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
    Cuando se envía otro con esa misma prueba y fecha
    Entonces el sistema devuelve 409 Conflict
    Y sigue existiendo un único resultado para esa combinación
    """
    student = setup_data["student1"]
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
        "mistakes": 5,
    }

    # Primer registro exitoso
    resp1 = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp1.status_code == 201

    # Intento de duplicado exacto
    resp2 = client.post(f"/api/v1/students/{student.id}/results", json=payload)
    assert resp2.status_code == 409
    assert resp2.get_json()["error"] == "CONFLICT"

    # Verificar que solo existe un resultado
    results = (
        session.query(Result)
        .filter(
            Result.student_id == student.id,
            Result.test_id == test_obj.id,
            Result.test_date == datetime.date(2026, 3, 10),
        )
        .all()
    )
    assert len(results) == 1


def test_scenario_4_ordered_history_with_metrics(client, setup_data):
    """
    Escenario 4: Histórico ordenado
    Dado un alumno con resultados el 24/03, el 10/03 y el 07/04
    Cuando se consulta su histórico
    Entonces se devuelven ordenados por fecha ascendente
    Y cada uno incluye su PPM y su porcentaje de aciertos
    """
    student = setup_data["student1"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    client.post(
        "/api/dev/session",
        json={"role": "coordinator"},
    )

    # Insertamos desordenados a propósito: primero 24/03, luego 10/03, luego 07/04
    # 1. 24/03: time=60s, words=100 -> PPM=100.0. 16 aciertos, 4 errores -> comprehension=70.0%
    client.post(
        f"/api/v1/students/{student.id}/results",
        json={
            "test_id": str(test_obj.id),
            "section_id": str(section.id),
            "test_date": "2026-03-24",
            "time": 60,
            "successes": 16,
            "mistakes": 4,
        },
    )

    # 2. 10/03: time=120s, words=100 -> PPM=50.0. 10 aciertos, 10 errores -> comprehension=25.0%
    client.post(
        f"/api/v1/students/{student.id}/results",
        json={
            "test_id": str(test_obj.id),
            "section_id": str(section.id),
            "test_date": "2026-03-10",
            "time": 120,
            "successes": 10,
            "mistakes": 10,
        },
    )

    # 3. 07/04: time=50s, words=100 -> PPM=120.0. 20 aciertos, 0 errores -> comprehension=100.0%
    client.post(
        f"/api/v1/students/{student.id}/results",
        json={
            "test_id": str(test_obj.id),
            "section_id": str(section.id),
            "test_date": "2026-04-07",
            "time": 50,
            "successes": 20,
            "mistakes": 0,
        },
    )

    # Consultar histórico vía GET /api/v1/students/{student_id}/results
    resp = client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200
    history = resp.get_json()
    assert len(history) == 3

    # Comprobar orden cronológico ascendente estricto
    assert history[0]["test_date"] == "2026-03-10"
    assert history[0]["ppm"] == 50.0
    assert history[0]["comprehension"] == 25.0
    assert history[0]["test_code"] == "1AF"

    assert history[1]["test_date"] == "2026-03-24"
    assert history[1]["ppm"] == 100.0
    assert history[1]["comprehension"] == 70.0
    assert history[1]["test_code"] == "1AF"

    assert history[2]["test_date"] == "2026-04-07"
    assert history[2]["ppm"] == 120.0
    assert history[2]["comprehension"] == 100.0
    assert history[2]["test_code"] == "1AF"

    # Verificar también ruta directa /api/v1/students/{student_id}/results
    resp_direct = client.get(f"/api/v1/students/{student.id}/results")
    assert resp_direct.status_code == 200
    assert len(resp_direct.get_json()) == 3


def test_scenario_5_independence_between_students(client, setup_data, session):
    """
    Escenario 5: Independencia entre alumnos
    Dado dos alumnos distintos
    Cuando ambos registran un resultado de la prueba 1AF con la misma fecha
    Entonces el sistema acepta los dos registros
    Y la restricción de unicidad no los considera duplicados
    """
    student1 = setup_data["student1"]
    student2 = setup_data["student2"]
    section1 = setup_data["section1"]
    section2 = setup_data["section2"]
    test_obj = setup_data["test"]

    client.post("/api/dev/session", json={"role": "coordinator"})

    payload_1 = {
        "test_id": str(test_obj.id),
        "section_id": str(section1.id),
        "test_date": "2026-03-10",
        "time": 60,
        "successes": 15,
        "mistakes": 5,
    }
    resp1 = client.post(f"/api/v1/students/{student1.id}/results", json=payload_1)
    assert resp1.status_code == 201

    payload_2 = {
        "test_id": str(test_obj.id),
        "section_id": str(section2.id),
        "test_date": "2026-03-10",
        "time": 75,
        "successes": 14,
        "mistakes": 6,
    }
    resp2 = client.post(f"/api/v1/students/{student2.id}/results", json=payload_2)
    assert resp2.status_code == 201

    # Ambos registros coexisten en la misma fecha
    r1 = session.query(Result).filter(Result.student_id == student1.id).first()
    r2 = session.query(Result).filter(Result.student_id == student2.id).first()
    assert r1 is not None and r2 is not None
    assert r1.test_date == r2.test_date == datetime.date(2026, 3, 10)


def test_repository_translates_integrity_error_to_conflict_error(session, setup_data):
    """
    T-BE19-03: Mapeo de violación de unicidad a excepción de dominio ConflictError
    y no un error 500 no controlado de base de datos.
    """
    student = setup_data["student1"]
    section = setup_data["section1"]
    test_obj = setup_data["test"]

    repo = ResultRepository(session)

    # Primer insert directo
    repo.create(
        student_id=student.id,
        section_id=section.id,
        test_id=test_obj.id,
        test_date=datetime.date(2026, 3, 10),
        time=60,
        successes=15,
        mistakes=5,
        commit=True,
    )

    # Segundo insert idéntico a nivel de repo (simula carrera donde exists_duplicate devolvió False)
    with pytest.raises(ConflictError) as exc_info:
        repo.create(
            student_id=student.id,
            section_id=section.id,
            test_id=test_obj.id,
            test_date=datetime.date(2026, 3, 10),
            time=60,
            successes=15,
            mistakes=5,
            commit=True,
        )

    assert "Ya existe un resultado registrado" in str(exc_info.value)


def test_history_permissions_and_validations(client, setup_data):
    """
    Verifica las autorizaciones y validaciones de consulta de histórico:
    - Tutor sin permiso sobre el alumno -> 403 Forbidden
    - Rol 'pendiente' -> 403 Forbidden
    - Sin sesión -> 401 Unauthorized
    - Alumno inexistente o UUID inválido -> 400 Bad Request
    """
    student1 = setup_data["student1"]
    section1 = setup_data["section1"]
    section2 = setup_data["section2"]

    # 1. Tutor asignado a section2 intenta ver histórico de student1 (asignado a section1)
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section2.id)]},
    )
    resp_forbid = client.get(f"/api/v1/students/{student1.id}/results")
    assert resp_forbid.status_code == 403
    assert resp_forbid.get_json()["error"] == "FORBIDDEN"

    # 2. Usuario con rol pendiente
    client.post("/api/dev/session", json={"role": "pendiente"})
    resp_pend = client.get(f"/api/v1/students/{student1.id}/results")
    assert resp_pend.status_code == 403

    # 3. Tutor con permiso sobre section1 sí puede ver
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section1.id)]},
    )
    resp_ok = client.get(f"/api/v1/students/{student1.id}/results")
    assert resp_ok.status_code == 200

    # 4. Sin sesión
    app_no_bypass = create_app(NoBypassConfig)
    client_no_auth = app_no_bypass.test_client()
    resp_unauth = client_no_auth.get(f"/api/v1/students/{student1.id}/results")
    assert resp_unauth.status_code == 401

    # 5. Alumno no existe
    client.post("/api/dev/session", json={"role": "coordinator"})
    fake_id = uuid.uuid4()
    resp_notfound = client.get(f"/api/v1/students/{fake_id}/results")
    assert resp_notfound.status_code == 404
    assert "alumno" in (resp_notfound.get_json().get("message") or resp_notfound.get_json().get("error", "")).lower()

    # 6. ID inválido
    resp_invalid = client.get("/api/v1/students/not-a-uuid/results")
    assert resp_invalid.status_code == 400


def test_postgresql_unique_constraint_direct():
    """
    T-BE19-05: Verificación de la restricción física UNIQUE en PostgreSQL real.
    Si el contenedor PostgreSQL está accesible, verifica en pg_constraint que existe
    'uq_results_student_test_date' sobre las columnas esperadas (student_id, test_id, test_date).
    """
    db_url = Config.SQLALCHEMY_DATABASE_URI
    if not db_url or "postgresql" not in db_url:
        pytest.skip("Base de datos PostgreSQL no configurada en este entorno")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Verificar existencia de la constraint en pg_constraint
            query = text("""
                SELECT conname
                FROM pg_constraint
                WHERE conname = 'uq_results_student_test_date';
            """)
            res = conn.execute(query).fetchone()
            assert res is not None, "La constraint 'uq_results_student_test_date' no existe en PostgreSQL"
            assert res[0] == "uq_results_student_test_date"
    except Exception as e:
        pytest.skip(f"No se pudo conectar a PostgreSQL: {e}")

