import io
import pytest
from app.extensions import db
from app.models.test import Test
from app.repositories.test_repository import TestRepository
from app.services.catalog_service import CatalogService


def test_scenario_1_import_full_catalog(app):
    """
    Escenario 1: Importación del catálogo completo desde tests.csv
    Dado el fichero tests.csv con separador punto y coma
    Cuando se ejecuta la importación del catálogo
    Entonces se crean las 34 pruebas
    Y cada una conserva su código, nombre y número de palabras
    """
    with app.app_context():
        service = CatalogService(db.session)
        result = service.import_tests_from_csv("data/seeds/tests.csv")

        assert result["total"] == 34
        assert result["created"] == 34
        assert result["updated"] == 0

        repo = TestRepository(db.session)
        all_tests = repo.get_all()
        assert len(all_tests) == 34

        # Comprobar primera y última prueba
        t1 = repo.get_by_code("0IF")
        assert t1 is not None
        assert t1.name == "Normativa piscinas"
        assert t1.words == 235

        t_last = repo.get_by_code("3CL")
        assert t_last is not None
        assert t_last.name == "La Tramontana"
        assert t_last.words == 1300


def test_scenario_2_trailing_semicolon_ignored(app):
    """
    Escenario 2: Punto y coma al final de línea
    Dado que cada línea del fichero termina en punto y coma
    Y esto produce una cuarta columna vacía
    Cuando se procesa el fichero
    Entonces el parser ignora la columna sobrante
    Y no rechaza ninguna fila por número de columnas
    """
    csv_sample = (
        "code;name;words\n"
        "TEST1;Prueba de natación;300;\n"
        "TEST2;Carrera de orientación;450;\n"
    )

    with app.app_context():
        service = CatalogService(db.session)
        result = service.import_tests_from_csv(csv_sample)

        assert result["total"] == 2
        assert result["created"] == 2

        repo = TestRepository(db.session)
        t1 = repo.get_by_code("TEST1")
        assert t1 is not None
        assert t1.name == "Prueba de natación"
        assert t1.words == 300


def test_scenario_3_quotes_and_accents_preserved(app):
    """
    Escenario 3: Nombres con comillas y acentos
    Dado una fila cuyo nombre contiene comillas dobles y caracteres acentuados
    Cuando se procesa
    Entonces el nombre se guarda íntegro y correctamente codificado
    """
    csv_sample = (
        "code;name;words\n"
        '2AF;El "paquebote" del aire levanta el vuelo;861;\n'
        "2BF;José María, el Tempranillo, un mito ;836;\n"
        "1EL;Andrés estudia;1104;\n"
    )

    with app.app_context():
        service = CatalogService(db.session)
        result = service.import_tests_from_csv(csv_sample)

        assert result["total"] == 3
        assert result["created"] == 3

        repo = TestRepository(db.session)

        # Comillas dobles internas preservadas
        t_quotes = repo.get_by_code("2AF")
        assert t_quotes is not None
        assert t_quotes.name == 'El "paquebote" del aire levanta el vuelo'
        assert t_quotes.words == 861

        # Acentos y comas preservados con trim
        t_accents = repo.get_by_code("2BF")
        assert t_accents is not None
        assert t_accents.name == "José María, el Tempranillo, un mito"

        t_accent2 = repo.get_by_code("1EL")
        assert t_accent2 is not None
        assert t_accent2.name == "Andrés estudia"


def test_scenario_4_level_and_type_derivation(app):
    """
    Escenario 4: Derivación de nivel y tipo
    Dado una prueba con código "0IF"
    Cuando se importa
    Entonces se guarda con level "0"
    Y con test_letter "I" y type "F"
    """
    csv_sample = (
        "code;name;words\n"
        "0IF;Normativa piscinas;235;\n"
        "1AL;Los trabajos de Teseo;1032;\n"
        "2CF;Un millón de euros;697;\n"
        "3CL;La Tramontana;1300;\n"
    )

    with app.app_context():
        service = CatalogService(db.session)
        service.import_tests_from_csv(csv_sample)

        repo = TestRepository(db.session)

        t0 = repo.get_by_code("0IF")
        assert t0.course == 0
        assert t0.test_letter == "I"
        assert t0.type == "F"

        t1 = repo.get_by_code("1AL")
        assert t1.course == 1
        assert t1.test_letter == "A"
        assert t1.type == "L"

        t2 = repo.get_by_code("2CF")
        assert t2.course == 2
        assert t2.test_letter == "C"
        assert t2.type == "F"

        t3 = repo.get_by_code("3CL")
        assert t3.course == 3
        assert t3.test_letter == "C"
        assert t3.type == "L"


def test_scenario_5_reimport_idempotency_and_update(app):
    """
    Escenario 5: Reimportación
    Dado un catálogo ya importado
    Cuando se vuelve a ejecutar la importación
    Entonces no se duplica ninguna prueba
    Y las existentes se actualizan por su código
    """
    csv_v1 = (
        "code;name;words\n"
        "0IF;Normativa piscinas;235;\n"
        "0IL;Los cazadores de focas;258;\n"
    )

    with app.app_context():
        service = CatalogService(db.session)
        # Primera importación
        res1 = service.import_tests_from_csv(csv_v1)
        assert res1["total"] == 2
        assert res1["created"] == 2
        assert res1["updated"] == 0

        # Segunda importación idéntica
        res2 = service.import_tests_from_csv(csv_v1)
        assert res2["total"] == 2
        assert res2["created"] == 0
        assert res2["updated"] == 2

        # Tercera importación con modificación de nombre y palabras
        csv_v2 = (
            "code;name;words\n"
            "0IF;Normativa piscinas municipal;250;\n"
            "0IL;Los cazadores de focas del Ártico;260;\n"
        )
        res3 = service.import_tests_from_csv(csv_v2)
        assert res3["total"] == 2
        assert res3["created"] == 0
        assert res3["updated"] == 2

        repo = TestRepository(db.session)
        t_updated = repo.get_by_code("0IF")
        assert t_updated.name == "Normativa piscinas municipal"
        assert t_updated.words == 250


def test_endpoint_import_tests_success(client):
    """
    Prueba del endpoint POST /api/v1/tests/import con rol autorizado.
    Importa la semilla por defecto data/seeds/tests.csv.
    """
    headers = {"X-User-Role": "admin"}
    response = client.post("/api/v1/tests/import", headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert data["message"] == "Catálogo importado correctamente"
    assert data["total"] == 34
    assert data["created"] == 34
    assert len(data["tests"]) == 34


def test_endpoint_import_tests_with_file_upload(client):
    """
    Prueba del endpoint POST /api/v1/tests/import subiendo un archivo CSV multipart.
    """
    csv_bytes = (
        b"code;name;words\n"
        b"UP1;Prueba de subida 1;120;\n"
        b"UP2;Prueba de subida 2;240;\n"
    )
    data = {
        "file": (io.BytesIO(csv_bytes), "mis_pruebas.csv"),
    }
    headers = {"X-User-Role": "coordinator"}
    response = client.post(
        "/api/v1/tests/import",
        data=data,
        content_type="multipart/form-data",
        headers=headers,
    )
    assert response.status_code == 200

    res_json = response.get_json()
    assert res_json["total"] == 2
    assert res_json["created"] == 2


def test_endpoint_import_unauthorized(client):
    """
    Prueba que un usuario sin rol 'admin' o 'coordinator' recibe 403 Forbidden.
    """
    headers = {"X-User-Role": "student"}
    response = client.post("/api/v1/tests/import", headers=headers)
    assert response.status_code == 403
