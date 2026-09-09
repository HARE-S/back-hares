import pytest


def test_scenario_1_create_test_success(client):
    """
    Escenario 1: Alta correcta (POST /api/v1/tests)
    Dado un coordinador con sesión activa
    Cuando envía code, name y words, opcionalmente level y type
    Entonces el sistema crea la prueba
    Y devuelve 201 Created con el recurso completo
    """
    payload = {
        "code": "0IF",
        "name": "Normativa piscinas",
        "words": 235,
        "level": "0",
        "type": "F",
    }
    headers = {"X-User-Role": "coordinator"}

    response = client.post("/api/v1/tests", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.get_json()
    assert "id" in data
    assert data["code"] == "0IF"
    assert data["name"] == "Normativa piscinas"
    assert data["words"] == 235
    assert data["level"] == "0"
    assert data["type"] == "F"
    assert data["disabled_at"] is None


def test_scenario_1_auto_deduce_level_and_type(client):
    """
    Prueba adicional para Escenario 1:
    Si no se especifican level ni type, se deducen automáticamente del formato del código.
    """
    payload = {
        "code": "1AL",
        "name": "Los trabajos de Teseo",
        "words": 1032,
    }
    response = client.post("/api/v1/tests", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert data["code"] == "1AL"
    assert data["level"] == "1"
    assert data["type"] == "L"


def test_scenario_2_duplicate_code_conflict(client):
    """
    Escenario 2: Código duplicado
    Dado una prueba existente con código "1AF"
    Cuando se intenta crear otra con el mismo código
    Entonces el sistema rechaza la petición
    Y devuelve 409 Conflict
    """
    payload = {
        "code": "1AF",
        "name": "Warner BROS Park",
        "words": 835,
    }
    res1 = client.post("/api/v1/tests", json=payload)
    assert res1.status_code == 201

    # Intento de duplicado
    res2 = client.post("/api/v1/tests", json=payload)
    assert res2.status_code == 409
    data = res2.get_json()
    assert "ya existe" in data.get("error", "").lower()


@pytest.mark.parametrize("invalid_words", [0, -10, "noventa", False])
def test_scenario_3_invalid_words(client, invalid_words):
    """
    Escenario 3: Número de palabras inválido
    Dado un coordinador con sesión activa
    Cuando envía words con valor cero, negativo o no numérico
    Entonces el sistema rechaza la petición
    Y devuelve 400 Bad Request indicando el campo
    """
    payload = {
        "code": "0BF",
        "name": "Cometas, asteroides y meteoritos",
        "words": invalid_words,
    }
    response = client.post("/api/v1/tests", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "words" in data.get("error", "").lower()


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Solo nombre", "words": 500},
        {"code": "", "name": "Código vacío", "words": 500},
        {"code": "0AL", "words": 500},
        {"code": "0AL", "name": "   ", "words": 500},
    ],
)
def test_scenario_4_missing_required_fields(client, payload):
    """
    Escenario 4: Campos obligatorios ausentes
    Dado una petición sin code o sin name
    Cuando se procesa
    Entonces el sistema devuelve 400 Bad Request
    """
    response = client.post("/api/v1/tests", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "obligatorio" in data.get("error", "").lower()


def test_scenario_5_tutor_role_forbidden(client):
    """
    Escenario 5: Rol sin permiso
    Dado un usuario con rol tutor
    Cuando intenta crear una prueba
    Entonces el sistema deniega la operación
    Y devuelve 403 Forbidden
    """
    payload = {
        "code": "2IF",
        "name": "Fiasco histórico en la F-1",
        "words": 872,
    }
    headers = {"X-User-Role": "tutor"}

    response = client.post("/api/v1/tests", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.get_json()
    assert "permiso denegado" in data.get("error", "").lower()

    # Verificar que con rol coordinator o admin sí se permite
    headers_coord = {"X-User-Role": "coordinator"}
    res_coord = client.post("/api/v1/tests", json=payload, headers=headers_coord)
    assert res_coord.status_code == 201
