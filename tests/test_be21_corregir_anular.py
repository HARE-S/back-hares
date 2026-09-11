import datetime
import uuid
import pytest
from app import create_app
from app.config import TestingConfig
from app.core.audit import clear_audit_logs, get_audit_logs
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Result, Test


class NoBypassConfig(TestingConfig):
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-21."""
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

    # student1 en section1, student2 en section2
    ss1 = StudentSection(student_id=student1.id, section_id=section1.id)
    ss2 = StudentSection(student_id=student2.id, section_id=section2.id)
    session.add_all([ss1, ss2])
    session.flush()

    # Prueba con 120 palabras
    test_1af = Test(code="1AF", name="El halcón peregrino", words=120)
    session.add(test_1af)
    session.flush()

    # Resultado inicial para student1: 90 segundos, 15 aciertos, 5 errores (PPM = (120/90)*60 = 80.0)
    result = Result(
        student_id=student1.id,
        section_id=section1.id,
        test_id=test_1af.id,
        test_date=datetime.date(2026, 3, 10),
        time=90,
        successes=15,
        mistakes=5,
    )
    session.add(result)
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": student1,
        "student2": student2,
        "test": test_1af,
        "result": result,
    }


def test_scenario_1_partial_update_recalculates_ppm(client, setup_data, session):
    """
    Escenario 1: Corrección parcial
    Dado un resultado registrado con un tiempo erróneo (90s, PPM=80.0)
    Cuando se envía PATCH modificando solo el tiempo a 60s
    Entonces el resultado se actualiza
    Y su PPM se recalcula en la respuesta (120 palabras en 60s = 120.0 PPM)
    Y devuelve 200 OK
    """
    res = setup_data["result"]
    sec = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # Modificar únicamente el tiempo a 60 segundos
    payload = {"time": 60}
    resp = client.patch(f"/api/v1/results/{res.id}", json=payload)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["id"] == str(res.id)
    assert data["time"] == 60
    assert data["ppm"] == 120.0
    assert data["successes"] == 15  # Se conserva el valor previo no modificado
    assert data["mistakes"] == 5

    # Verificar en base de datos
    session.expire_all()
    reloaded = session.get(Result, res.id)
    assert reloaded.time == 60

    # Probar también el endpoint canónico con prefijo /api/v1/results/<id>
    resp_v1 = client.patch(f"/api/v1/results/{res.id}", json={"time": 40})
    assert resp_v1.status_code == 200
    assert resp_v1.get_json()["time"] == 40
    assert resp_v1.get_json()["ppm"] == 180.0  # (120 / 40) * 60 = 180.0


def test_scenario_2_invalid_data_returns_422(client, setup_data, session):
    """
    Escenario 2: Datos inválidos
    Dado un resultado existente
    Cuando se envía PATCH con aciertos negativos
    Entonces el sistema devuelve 422 Unprocessable Entity
    Y el resultado no se modifica
    """
    res = setup_data["result"]
    sec = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # 1. Aciertos negativos
    r1 = client.patch(f"/api/v1/results/{res.id}", json={"successes": -3})
    assert r1.status_code == 422
    assert r1.get_json()["error"] == "UNPROCESSABLE_ENTITY"

    # 2. Tiempo cero o negativo
    r2 = client.patch(f"/api/v1/results/{res.id}", json={"time": 0})
    assert r2.status_code == 422
    assert r2.get_json()["error"] == "UNPROCESSABLE_ENTITY"

    # 3. Errores negativos
    r3 = client.patch(f"/api/v1/results/{res.id}", json={"mistakes": -1})
    assert r3.status_code == 422
    assert r3.get_json()["error"] == "UNPROCESSABLE_ENTITY"

    # Verificar que el resultado en base de datos NO se modificó
    session.expire_all()
    reloaded = session.get(Result, res.id)
    assert reloaded.time == 90
    assert reloaded.successes == 15
    assert reloaded.mistakes == 5


def test_scenario_3_deletion_returns_204_and_removes_physically(client, setup_data, session):
    """
    Escenario 3: Anulación (borrado físico)
    Dado un resultado registrado por error
    Cuando se envía DELETE sobre él
    Entonces el resultado se elimina físicamente
    Y devuelve 204 No Content
    """
    res = setup_data["result"]
    sec = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    resp = client.delete(f"/api/v1/results/{res.id}")
    assert resp.status_code == 204
    assert resp.data == b""

    # Verificar que ya no existe físicamente en base de datos
    session.expire_all()
    deleted = session.get(Result, res.id)
    assert deleted is None


def test_scenario_4_nonexistent_result_returns_404(client):
    """
    Escenario 4: Resultado inexistente
    Dado un identificador de resultado que no existe
    Cuando se envía PATCH o DELETE
    Entonces el sistema devuelve 404 Not Found
    """
    client.post("/api/dev/session", json={"role": "coordinator"})

    fake_id = uuid.uuid4()

    # PATCH sobre id inexistente
    r_patch = client.patch(f"/api/v1/results/{fake_id}", json={"time": 50})
    assert r_patch.status_code == 404
    assert r_patch.get_json()["error"] == "NOT_FOUND"

    # DELETE sobre id inexistente
    r_del = client.delete(f"/api/v1/results/{fake_id}")
    assert r_del.status_code == 404
    assert r_del.get_json()["error"] == "NOT_FOUND"


def test_scenario_5_tutor_without_permission_returns_403(client, setup_data, session):
    """
    Escenario 5: Tutor sin permiso
    Dado un tutor cuyas secciones no incluyen al alumno del resultado
    Cuando intenta modificarlo o eliminarlo
    Entonces el sistema devuelve 403 Forbidden
    """
    res = setup_data["result"]
    sec2 = setup_data["section2"]

    # Tutor solo asignado a section2 (el resultado pertenece a alumno de section1)
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec2.id)]},
    )

    # Intento de PATCH -> 403
    r_patch = client.patch(f"/api/v1/results/{res.id}", json={"time": 50})
    assert r_patch.status_code == 403
    assert r_patch.get_json()["error"] == "FORBIDDEN"

    # Intento de DELETE -> 403
    r_del = client.delete(f"/api/v1/results/{res.id}")
    assert r_del.status_code == 403
    assert r_del.get_json()["error"] == "FORBIDDEN"

    # El registro no fue modificado ni eliminado
    session.expire_all()
    intact = session.get(Result, res.id)
    assert intact is not None
    assert intact.time == 90


def test_scenario_6_audit_logged_with_previous_values(client, setup_data):
    """
    Escenario 6: Traza de la modificación y anulación con valores anteriores
    Dado una corrección o anulación completada
    Cuando termina la operación
    Entonces queda registrada en auditoría con el usuario y el valor anterior
    """
    clear_audit_logs()

    res = setup_data["result"]
    sec1 = setup_data["section1"]

    # 1. Traza de modificación (PATCH)
    client.post(
        "/api/dev/session",
        json={
            "role": "tutor",
            "email": "tutor.carlos@penascal.org",
            "sections": [str(sec1.id)],
        },
    )

    resp_patch = client.patch(
        f"/api/v1/results/{res.id}",
        json={"time": 55, "successes": 19},
    )
    assert resp_patch.status_code == 200

    logs_patch = get_audit_logs(resource_type="results", resource_id=str(res.id))
    assert len(logs_patch) == 1
    audit_patch = logs_patch[0]
    assert audit_patch["user"] == "tutor.carlos@penascal.org"
    assert audit_patch["action"] == "UPDATE_RESULT"
    # Valores anteriores
    assert audit_patch["details"]["previous_values"]["time"] == 90
    assert audit_patch["details"]["previous_values"]["successes"] == 15
    # Nuevos valores
    assert audit_patch["details"]["new_values"]["time"] == 55
    assert audit_patch["details"]["new_values"]["successes"] == 19

    # 2. Traza de anulación (DELETE)
    resp_del = client.delete(f"/api/v1/results/{res.id}")
    assert resp_del.status_code == 204

    logs_all = get_audit_logs(resource_type="results", resource_id=str(res.id))
    assert len(logs_all) == 2
    audit_del = logs_all[1]
    assert audit_del["user"] == "tutor.carlos@penascal.org"
    assert audit_del["action"] == "DELETE_RESULT"
    assert audit_del["details"]["previous_values"]["time"] == 55
    assert audit_del["details"]["previous_values"]["successes"] == 19
    assert audit_del["details"]["previous_values"]["mistakes"] == 5


def test_alias_routes_under_student_prefix(client, setup_data, session):
    """
    Verifica que las rutas alias /api/v1/students/<student_id>/results/<result_id>
    también funcionan correctamente para PATCH y DELETE.
    """
    student = setup_data["student1"]
    res = setup_data["result"]
    sec = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # PATCH vía /api/v1/students/<student_id>/results/<result_id>
    resp_patch = client.patch(
        f"/api/v1/students/{student.id}/results/{res.id}",
        json={"time": 45},
    )
    assert resp_patch.status_code == 200
    assert resp_patch.get_json()["time"] == 45

    # DELETE vía /api/v1/students/<student_id>/results/<result_id>
    resp_del = client.delete(f"/api/v1/students/{student.id}/results/{res.id}")
    assert resp_del.status_code == 204

    session.expire_all()
    assert session.get(Result, res.id) is None


def test_collision_on_patch_date_returns_409(client, setup_data, session):
    """
    Verifica que si un PATCH cambia la fecha del resultado a una fecha
    en la que el alumno ya tiene un resultado para esa prueba, devuelve 409 Conflict.
    """
    student = setup_data["student1"]
    sec = setup_data["section1"]
    test_obj = setup_data["test"]
    res1 = setup_data["result"]  # fecha: 2026-03-10

    # Crear un segundo resultado el 2026-03-24
    res2 = Result(
        student_id=student.id,
        section_id=sec.id,
        test_id=test_obj.id,
        test_date=datetime.date(2026, 3, 24),
        time=60,
        successes=18,
        mistakes=2,
    )
    session.add(res2)
    session.commit()

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec.id)]},
    )

    # Intentar cambiar la fecha de res2 a la fecha de res1 (2026-03-10) -> Colisión
    resp = client.patch(f"/api/v1/results/{res2.id}", json={"test_date": "2026-03-10"})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "CONFLICT"
