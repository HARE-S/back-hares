"""
Tests for BE-29: Búsqueda de alumnos.

Scenarios covered:
  1. Esc 1 - Búsqueda por fragmento: "garc" devuelve los nombres que lo contienen.
  2. Esc 2 - Insensible a mayúsculas y acentos: "GARCIA" / "garcia" encuentra "García".
  3. Esc 3 - Búsquedas cortas: 1 y 2 caracteres responden sin mínimo de tres.
  4. Esc 4 - Homónimos: cada resultado incluye secciones activas con su centro.
  5. Esc 5 - Ámbito del tutor: solo busca en sus secciones asignadas.
  6. Seguridad: rol pendiente y tutor sin secciones -> 403.
  7. Validación: q vacío o solo espacios -> 422.
  8. Alumnos deshabilitados excluidos.
  9. Paginación correcta.
 10. OpenAPI: ruta /api/v1/students/search documentada.
"""

import datetime
import uuid

import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Module-scoped app for BE-29 tests."""
    application = create_app(TestingConfig)
    yield application


@pytest.fixture(autouse=True)
def setup_db(app):
    """Create all tables, seed baseline data, tear down after each test."""
    with app.app_context():
        _db.create_all()

        c1 = Center(id=uuid.uuid4(), name="Centro A", external_id="EXT-CA")
        c2 = Center(id=uuid.uuid4(), name="Centro B", external_id="EXT-CB")
        _db.session.add_all([c1, c2])
        _db.session.flush()

        sec_a1 = Section(
            id=uuid.uuid4(), name="Sección A1", center_id=c1.id,
            academic_year="2025-2026",
        )
        sec_a2 = Section(
            id=uuid.uuid4(), name="Sección A2", center_id=c1.id,
            academic_year="2025-2026",
        )
        sec_b1 = Section(
            id=uuid.uuid4(), name="Sección B1", center_id=c2.id,
            academic_year="2025-2026",
        )
        _db.session.add_all([sec_a1, sec_a2, sec_b1])
        _db.session.flush()

        s1 = Student(id=uuid.uuid4(), external_id="EXT-S1", name="Ana García")
        s2 = Student(id=uuid.uuid4(), external_id="EXT-S2", name="María García")
        s3 = Student(id=uuid.uuid4(), external_id="EXT-S3", name="José María")
        s4 = Student(id=uuid.uuid4(), external_id="EXT-S4", name="Elena Díaz")
        s5 = Student(id=uuid.uuid4(), external_id="EXT-S5", name="Elena Díaz")
        s6 = Student(id=uuid.uuid4(), external_id="EXT-S6", name="Lucía Pérez")
        s7 = Student(
            id=uuid.uuid4(), external_id="EXT-S7", name="Carlos Oculta",
            disabled_at=datetime.date(2026, 1, 1),
        )
        _db.session.add_all([s1, s2, s3, s4, s5, s6, s7])
        _db.session.flush()

        _db.session.add_all([
            StudentSection(student_id=s1.id, section_id=sec_a1.id),
            StudentSection(student_id=s2.id, section_id=sec_a2.id),
            StudentSection(student_id=s3.id, section_id=sec_a1.id),
            StudentSection(student_id=s4.id, section_id=sec_a1.id),
            StudentSection(student_id=s5.id, section_id=sec_b1.id),
            StudentSection(student_id=s6.id, section_id=sec_b1.id),
            StudentSection(student_id=s7.id, section_id=sec_a1.id),
        ])
        _db.session.commit()

        yield

        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    with app.app_context():
        yield _db.session


def _set_dev_session(client, role="admin", sections=None):
    """Set dev session vars for a given role and section list."""
    with client.session_transaction() as sess:
        sess["user_email"] = f"dev.{role}@test.com"
        sess["dev_role"] = role
        sess["dev_sections"] = [str(s) for s in (sections or [])]


def _get_center_and_section_ids(session, center_name, section_name):
    center_id = session.execute(
        _db.text("SELECT id FROM centers WHERE name = :n LIMIT 1"),
        {"n": center_name},
    ).scalar()
    section_id = session.execute(
        _db.text("SELECT id FROM sections WHERE name = :n LIMIT 1"),
        {"n": section_name},
    ).scalar()
    assert center_id is not None and section_id is not None
    return str(uuid.UUID(str(center_id))), str(uuid.UUID(str(section_id)))


# ---------------------------------------------------------------------------
# Escenario 1 - Búsqueda por fragmento
# ---------------------------------------------------------------------------

class TestEscenario1Fragmento:
    def test_devuelve_alumnos_cuyo_nombre_contiene_el_fragmento(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=garc")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2
        names = {item["name"] for item in data["items"]}
        assert "Ana García" in names
        assert "María García" in names

    def test_fragmento_en_medio_del_nombre(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=lena")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2
        assert all("Elena" in item["name"] for item in data["items"])


# ---------------------------------------------------------------------------
# Escenario 2 - Insensible a mayúsculas y acentos
# ---------------------------------------------------------------------------

class TestEscenario2AcentosYMayusculas:
    def test_sin_tildes_encuentra_con_tildes(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=garcia")
        data = resp.get_json()
        assert resp.status_code == 200
        names = {item["name"] for item in data["items"]}
        assert "Ana García" in names

    def test_mayusculas_encuentra_minusculas(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=MARIA")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2  # María García y José María
        names = {item["name"] for item in data["items"]}
        assert "José María" in names

    def test_con_til_encuentra_y_nombre_con_ene(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=josé")
        data = resp.get_json()
        assert resp.status_code == 200
        names = {item["name"] for item in data["items"]}
        assert "José María" in names

    def test_nombre_con_tilde_se_busca_sin_ella(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=perez")
        data = resp.get_json()
        assert resp.status_code == 200
        names = {item["name"] for item in data["items"]}
        assert "Lucía Pérez" in names


# ---------------------------------------------------------------------------
# Escenario 3 - Búsquedas cortas (sin mínimo de 3 caracteres)
# ---------------------------------------------------------------------------

class TestEscenario3BusquedaCorta:
    def test_dos_caracteres_devuelve_resultados(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=di")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2  # Elena Díaz (A1) y Elena Díaz (B1)

    def test_un_caracter_devuelve_resultados(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=z")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 3  # Elena Díaz (x2) + Lucía Pérez


# ---------------------------------------------------------------------------
# Escenario 4 - Homónimos: centro y sección en cada resultado
# ---------------------------------------------------------------------------

class TestEscenario4Homonimos:
    def test_resultados_incluyen_centro_y_seccion(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=Elena")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2

        centers = set()
        for item in data["items"]:
            assert item["name"] == "Elena Díaz"
            sections = item["sections"]
            assert len(sections) == 1
            centers.add(sections[0]["center"])
        assert centers == {"Centro A", "Centro B"}

    def test_homonimos_se_distinguen_por_su_seccion(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=elena")
        data = resp.get_json()
        section_names = {
            item["sections"][0]["name"] for item in data["items"]
        }
        assert section_names == {"Sección A1", "Sección B1"}


# ---------------------------------------------------------------------------
# Escenario 5 - Ámbito del tutor
# ---------------------------------------------------------------------------

class TestEscenario5AmbitoTutor:
    def test_tutor_no_ve_alumnos_de_otras_secciones(self, client, session):
        _, sec_a1_id = _get_center_and_section_ids(session, "Centro A", "Sección A1")
        _, sec_a2_id = _get_center_and_section_ids(session, "Centro A", "Sección A2")
        _set_dev_session(client, role="tutor", sections=[sec_a1_id, sec_a2_id])

        resp = client.get("/api/v1/students/search?q=elena")
        data = resp.get_json()
        assert resp.status_code == 200
        # La Elena de Centro B (Sección B1) no está en el ámbito del tutor.
        assert data["total"] == 1
        assert data["items"][0]["sections"][0]["center"] == "Centro A"

    def test_tutor_busca_en_sus_dos_secciones(self, client, session):
        _, sec_a1_id = _get_center_and_section_ids(session, "Centro A", "Sección A1")
        _, sec_a2_id = _get_center_and_section_ids(session, "Centro A", "Sección A2")
        _set_dev_session(client, role="tutor", sections=[sec_a1_id, sec_a2_id])

        resp = client.get("/api/v1/students/search?q=garcia")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2  # Ana (A1) y María (A2)


# ---------------------------------------------------------------------------
# Seguridad y validación
# ---------------------------------------------------------------------------

class TestSeguridad:
    def test_rol_pendiente_recibe_403(self, client, session):
        _set_dev_session(client, role="pendiente")
        resp = client.get("/api/v1/students/search?q=garcia")
        assert resp.status_code == 403
        assert resp.get_json().get("items") is None

    def test_tutor_sin_secciones_recibe_403(self, client, session):
        _set_dev_session(client, role="tutor", sections=[])
        resp = client.get("/api/v1/students/search?q=garcia")
        assert resp.status_code == 403

    def test_dev_sin_sesion_no_expone_datos(self, client):
        # Sin sesión el bypass usa tutor por defecto sin secciones: 403.
        resp = client.get("/api/v1/students/search?q=garcia")
        assert resp.status_code == 403
        assert resp.get_json().get("items") is None


class TestValidacion:
    def test_q_vacio_devuelve_422(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=")
        assert resp.status_code == 422

    def test_q_solo_espacios_devuelve_422(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=%20%20")
        assert resp.status_code == 422

    def test_falta_q_devuelve_422(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Comportamiento adicional
# ---------------------------------------------------------------------------

class TestComportamiento:
    def test_alumno_deshabilitado_excluido(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=ocult")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 0

    def test_sin_resultados_devuelve_lista_vacia(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=zzzxx")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 0
        assert data["items"] == []

    def test_paginacion_correcta(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students/search?q=a&page=1&limit=2")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 6  # Ana, María, José, Elena x2, Lucía
        assert len(data["items"]) == 2
        assert data["pages"] == 3


# ---------------------------------------------------------------------------
# OpenAPI (BE-48): la ruta de búsqueda está documentada
# ---------------------------------------------------------------------------

class TestOpenAPISpec:
    def test_path_search_documentada(self, app):
        from app.extensions import api as openapi_api

        paths = openapi_api.spec.to_dict().get("paths", {})
        assert "/api/v1/students/search" in paths
        get_op = paths["/api/v1/students/search"]["get"]
        param_names = {p["name"] for p in get_op.get("parameters", [])}
        assert {"q", "page", "limit"}.issubset(param_names)
        assert "200" in get_op.get("responses", {})
        assert "403" in get_op.get("responses", {})
        assert "422" in get_op.get("responses", {})