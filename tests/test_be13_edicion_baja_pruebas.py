import datetime
import pytest
from app.models.center import Center, Section
from app.models.student import Student
from app.models.test import Result, Test



def test_scenario_1_full_replacement_put(client, session):
    """
    Escenario 1: Reemplazo completo (PUT)
    Dado una prueba existente
    Cuando se envía PUT con todos los campos
    Entonces el recurso se reemplaza por completo
    Y devuelve 200 OK
    """
    test = Test(code="0IF", name="Normativa piscinas", words=235, level="0", type="F")
    session.add(test)
    session.commit()

    payload = {
        "code": "0IF_MOD",
        "name": "Normativa piscinas actualizada",
        "words": 250,
        "level": "1",
        "type": "L",
    }
    headers = {"X-User-Role": "coordinator"}

    response = client.put(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert data["id"] == str(test.id)
    assert data["code"] == "0IF_MOD"
    assert data["name"] == "Normativa piscinas actualizada"
    assert data["words"] == 250
    assert data["level"] == "1"
    assert data["type"] == "L"


def test_scenario_1_put_requires_mandatory_fields(client, session):
    """
    PUT es un reemplazo completo: si falta un campo obligatorio (ej: words), devuelve 422.
    """
    test = Test(code="0IF", name="Normativa piscinas", words=235)
    session.add(test)
    session.commit()

    payload = {
        "code": "0IF",
        "name": "Normativa piscinas sin palabras",
        # 'words' ausente
    }
    headers = {"X-User-Role": "coordinator"}

    response = client.put(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 422
    assert "obligatorio" in response.get_json()["error"]


def test_scenario_2_partial_modification_patch(client, session):
    """
    Escenario 2: Modificación parcial (PATCH)
    Dado una prueba existente
    Cuando se envía PATCH con solo el campo name
    Entonces se modifica únicamente ese campo
    Y devuelve 200 OK
    """
    test = Test(code="0IL", name="Los cazadores de focas", words=258, level="0", type="L")
    session.add(test)
    session.commit()

    payload = {"name": "Los cazadores del Ártico"}
    headers = {"X-User-Role": "admin"}

    response = client.patch(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert data["name"] == "Los cazadores del Ártico"
    assert data["code"] == "0IL"
    assert data["words"] == 258
    assert data["level"] == "0"
    assert data["type"] == "L"


@pytest.mark.parametrize(
    "invalid_words",
    [0, -5, "noventa", False, None],
)
def test_scenario_3_invalid_data_in_patch_returns_422(client, session, invalid_words):
    """
    Escenario 3: Datos inválidos en PATCH
    Dado una prueba existente
    Cuando se envía PATCH con un valor de words no válido
    Entonces el sistema rechaza la petición
    Y devuelve 422 Unprocessable Entity
    """
    test = Test(code="0AF", name="La vaca", words=269)
    session.add(test)
    session.commit()

    payload = {"words": invalid_words}
    headers = {"X-User-Role": "coordinator"}

    response = client.patch(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 422

    data = response.get_json()
    assert "error" in data


def test_scenario_4_cannot_change_code_if_test_has_results(client, session):
    """
    Escenario 4: Intento de cambiar el código de una prueba con resultados
    Dado una prueba que ya tiene resultados de alumnos asociados
    Cuando se intenta modificar su campo code
    Entonces el sistema deniega la modificación
    Y devuelve 409 Conflict explicando el motivo
    """
    center = Center(name="Centro Bolueta")
    section = Section(name="1CARMED2", center=center)
    student = Student(name="Alumno con Resultados")
    test = Test(code="1AL", name="Los trabajos de Teseo", words=1032)
    session.add_all([center, section, student, test])
    session.commit()

    # Asociar resultado
    result = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test.id,
        test_date=datetime.date(2026, 1, 15),
        time=120,
        successes=8,
        mistakes=2,
    )
    session.add(result)
    session.commit()

    # Intentar cambiar code vía PATCH
    payload = {"code": "1AL_NUEVO"}
    headers = {"X-User-Role": "coordinator"}

    response = client.patch(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 409

    data = response.get_json()
    assert "error" in data
    assert "resultados" in data["error"].lower()

    # El código debe seguir intacto en base de datos
    session.refresh(test)
    assert test.code == "1AL"


def test_scenario_4_same_code_allowed_in_put_even_with_results(client, session):
    """
    Regla refinada de Escenario 4:
    Si la prueba tiene resultados pero en PUT se reenvía el MISMO código (code no cambia),
    la actualización se debe permitir con 200 OK.
    """
    center = Center(name="Centro Bolueta")
    section = Section(name="1CARMED2", center=center)
    student = Student(name="Alumno 2")
    test = Test(code="1BF", name="El laurel", words=767)
    session.add_all([center, section, student, test])
    session.commit()

    result = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test.id,
        test_date=datetime.date(2026, 2, 10),
        time=95,
        successes=9,
        mistakes=1,
    )
    session.add(result)
    session.commit()

    # PUT con el mismo código pero actualizando name y words
    payload = {
        "code": "1BF",
        "name": "El laurel (Edición Revisada)",
        "words": 770,
    }
    headers = {"X-User-Role": "coordinator"}

    response = client.put(f"/api/v1/tests/{test.id}", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert data["name"] == "El laurel (Edición Revisada)"
    assert data["words"] == 770
    assert data["code"] == "1BF"


def test_scenario_5_soft_delete_preserves_results(client, session):
    """
    Escenario 5: Baja lógica
    Dado una prueba activa
    Cuando se envía DELETE
    Entonces se rellena disabled_at
    Y devuelve 204 No Content
    Y los resultados asociados siguen siendo accesibles
    """
    center = Center(name="Centro Bolueta")
    section = Section(name="1CARMED2", center=center)
    student = Student(name="Alumno Histórico")
    test = Test(code="2CF", name="Un millón de euros", words=697)
    session.add_all([center, section, student, test])
    session.commit()

    result = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test.id,
        test_date=datetime.date(2026, 3, 1),
        time=110,
        successes=10,
        mistakes=0,
    )
    session.add(result)
    session.commit()

    headers = {"X-User-Role": "coordinator"}
    response = client.delete(f"/api/v1/tests/{test.id}", headers=headers)
    assert response.status_code == 204

    # Verificar que disabled_at se ha rellenado
    session.refresh(test)
    assert test.disabled_at == datetime.date.today()

    # Verificar que el resultado histórico sigue existiendo y asociado a la prueba
    session.refresh(result)
    assert result.test_id == test.id
    assert result.test.name == "Un millón de euros"


def test_security_forbidden_for_non_authorized_roles(client, session):
    """
    Seguridad: PUT, PATCH y DELETE requieren rol coordinator o admin.
    Un rol 'tutor' o 'student' debe recibir 403 Forbidden.
    """
    test = Test(code="3BL", name="La venda", words=1212)
    session.add(test)
    session.commit()

    headers_tutor = {"X-User-Role": "tutor"}

    res_put = client.put(f"/api/v1/tests/{test.id}", json={"name": "X"}, headers=headers_tutor)
    assert res_put.status_code == 403

    res_patch = client.patch(f"/api/v1/tests/{test.id}", json={"name": "X"}, headers=headers_tutor)
    assert res_patch.status_code == 403

    res_del = client.delete(f"/api/v1/tests/{test.id}", headers=headers_tutor)
    assert res_del.status_code == 403


def test_nonexistent_test_returns_404(client):
    """
    Intentar actualizar o eliminar una prueba que no existe devuelve 404 Not Found.
    """
    headers = {"X-User-Role": "admin"}
    non_existent_id = "00000000-0000-0000-0000-000000000099"

    res_put = client.put(f"/api/v1/tests/{non_existent_id}", json={"code": "X", "name": "Y", "words": 100}, headers=headers)
    assert res_put.status_code == 404

    res_patch = client.patch(f"/api/v1/tests/{non_existent_id}", json={"name": "Nuevo"}, headers=headers)
    assert res_patch.status_code == 404

    res_del = client.delete(f"/api/v1/tests/{non_existent_id}", headers=headers)
    assert res_del.status_code == 404
