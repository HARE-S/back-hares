import datetime
import pytest
from app.extensions import db
from app.models.test import Test
from app.services.catalog_service import CatalogService


@pytest.fixture(autouse=True)
def seed_catalog(app):
    """Inicializa la base de datos con las 34 pruebas oficiales para los tests de BE-14."""
    with app.app_context():
        service = CatalogService(db.session)
        service.import_tests_from_csv("data/seeds/tests.csv")


def test_scenario_1_paginated_listing(client):
    """
    Escenario 1: Listado paginado
    Dado un catálogo con 34 pruebas
    Cuando se consulta con page=1 y limit=10
    Entonces se devuelven 10 pruebas
    Y la respuesta incluye el total de elementos (34) y el número de páginas (4)
    """
    response = client.get("/api/v1/tests?page=1&limit=10")
    assert response.status_code == 200

    data = response.get_json()
    assert "items" in data
    assert len(data["items"]) == 10
    assert data["total"] == 34
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["pages"] == 4

    # Segunda página
    res_p2 = client.get("/api/v1/tests?page=2&limit=10")
    assert res_p2.status_code == 200
    data_p2 = res_p2.get_json()
    assert len(data_p2["items"]) == 10
    assert data_p2["page"] == 2

    # Cuarta página (últimas 4 pruebas)
    res_p4 = client.get("/api/v1/tests?page=4&limit=10")
    assert res_p4.status_code == 200
    data_p4 = res_p4.get_json()
    assert len(data_p4["items"]) == 4
    assert data_p4["page"] == 4


def test_scenario_2_search_by_text(client):
    """
    Escenario 2: Búsqueda por texto
    Dado un catálogo de pruebas
    Cuando se consulta con filter="Warner"
    Entonces se devuelven las pruebas cuyo código o nombre contienen ese texto
    """
    response = client.get("/api/v1/tests?filter=Warner")
    assert response.status_code == 200

    data = response.get_json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert item["code"] == "1AF"
    assert "Warner BROS Park" in item["name"]


def test_scenario_2_accent_insensitive_search(client):
    """
    Notas de BE-14: Búsqueda insensible a acentos (el profesorado no teclea tildes).
    """
    # 1. Buscar "Andres" sin tilde debe encontrar "Andrés estudia" (1EL)
    res_andres = client.get("/api/v1/tests?filter=Andres")
    assert res_andres.status_code == 200
    data_andres = res_andres.get_json()
    assert data_andres["total"] == 1
    assert data_andres["items"][0]["code"] == "1EL"
    assert data_andres["items"][0]["name"] == "Andrés estudia"

    # 2. Buscar "Jose Maria" sin tilde debe encontrar "José María, el Tempranillo, un mito" (2BF)
    res_jose = client.get("/api/v1/tests?filter=Jose Maria")
    assert res_jose.status_code == 200
    data_jose = res_jose.get_json()
    assert data_jose["total"] == 1
    assert data_jose["items"][0]["code"] == "2BF"
    assert "José María" in data_jose["items"][0]["name"]

    # 3. Buscar "millon" sin tilde debe encontrar "Un millón de euros" (2CF)
    res_millon = client.get("/api/v1/tests?filter=millon")
    assert res_millon.status_code == 200
    data_millon = res_millon.get_json()
    assert data_millon["total"] == 1
    assert data_millon["items"][0]["code"] == "2CF"

    # 4. Buscar por código también funciona
    res_code = client.get("/api/v1/tests?filter=3cl")
    assert res_code.status_code == 200
    data_code = res_code.get_json()
    assert any(item["code"] == "3CL" for item in data_code["items"])


def test_scenario_3_filter_by_level_and_type(client):
    """
    Escenario 3: Filtro por curso y tipo
    Dado un catálogo con pruebas de varios cursos
    Cuando se consulta con course=1 y type=F
    Entonces se devuelven solo las pruebas de curso 1 y tipo F
    """
    response = client.get("/api/v1/tests?course=1&type=F")
    assert response.status_code == 200

    data = response.get_json()
    assert data["total"] == 6  # 1IF, 1AF, 1BF, 1CF, 1DF, 1EF
    for item in data["items"]:
        assert item["course"] == 1
        assert item["type"] == "F"


def test_scenario_4_combined_filters(client):
    """
    Escenario 4: Filtros combinados
    Dado un catálogo de pruebas
    Cuando se consulta con filter, course y page a la vez
    Entonces los tres criterios se aplican conjuntamente
    """
    # En curso 1, buscar texto "el"
    response = client.get("/api/v1/tests?course=1&filter=el&page=1&limit=2")
    assert response.status_code == 200

    data = response.get_json()
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) <= 2

    for item in data["items"]:
        assert item["course"] == 1
        assert "el" in item["name"].lower() or "el" in item["code"].lower()


def test_scenario_5_disabled_tests_excluded_by_default(client, session):
    """
    Escenario 5: Deshabilitadas excluidas
    Dado una prueba con disabled_at relleno
    Cuando se consulta el listado sin parámetros adicionales
    Entonces esa prueba no aparece
    """
    # Deshabilitar una prueba existente
    test = session.query(Test).filter_by(code="0IF").first()
    test.disabled_at = datetime.date.today()
    session.commit()

    # Consulta sin include_disabled
    response = client.get("/api/v1/tests")
    assert response.status_code == 200
    data = response.get_json()

    codes = [item["code"] for item in data["items"]]
    assert "0IF" not in codes
    assert data["total"] == 33  # 34 - 1

    # Consulta con include_disabled=true
    res_disabled = client.get("/api/v1/tests?include_disabled=true")
    assert res_disabled.status_code == 200
    data_disabled = res_disabled.get_json()

    codes_all = [item["code"] for item in data_disabled["items"]]
    assert "0IF" in codes_all
    assert data_disabled["total"] == 34


def test_pagination_bounds_and_safety(client):
    """
    Verifica que valores inválidos o fuera de rango de page y limit se manejen de forma segura.
    """
    # page negativa y limit enorme
    response = client.get("/api/v1/tests?page=-5&limit=999")
    assert response.status_code == 200
    data = response.get_json()
    assert data["page"] == 1
    assert data["limit"] == 100  # Acotado al máximo 100
