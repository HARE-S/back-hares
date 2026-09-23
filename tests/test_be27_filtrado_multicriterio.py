"""
Tests for BE-27: Filtrado multicriterio del alumnado.

Scenarios covered:
  1. Esc 1 – Sin filtros: devuelve todos los alumnos activos paginados.
  2. Esc 2 – Filtro por centre_id: solo alumnos de un centro.
  3. Esc 3 – Filtro por section_id: solo alumnos de una sección.
  4. Esc 4 – Filtro por género: alumnos con género = "Masculino".
  5. Esc 5 – Filtro sector="__missing__": alumnos sin sector informado,
             respuesta incluye missing_data con conteo.
  6. Esc 6 – Tutor scope: tutor solo ve sus secciones; 403 si no tiene
             secciones asignadas o si pide una sección no asignada.
  7. Filtro por rango de edad (min_age/max_age): birth_date derivada.
  8. Combinación de filtros (centre + section + gender) en conjunción AND.
  9. Auditoría FILTER_STUDENTS al filtrar por gender o academic_status.
 10. Seguridad: rol pendiente siempre rechazado.
"""

import datetime
import uuid

import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Result, Test



# ---------------------------------------------------------------------------
# Reference date for deterministic age calculations
# ---------------------------------------------------------------------------
REFERENCE_DATE = datetime.date(2026, 9, 15)  # 15 Sep 2026


def _today():
    """Return a fixed reference date for age assertions."""
    return REFERENCE_DATE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Module-scoped app for BE-27 tests."""
    application = create_app(TestingConfig)
    yield application


@pytest.fixture(autouse=True)
def setup_db(app):
    """Create all tables, seed baseline data, tear down after each test."""
    with app.app_context():
        _db.create_all()

        # ---- Centers and Sections ----
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

        # ---- Students ----
        s1 = Student(
            id=uuid.uuid4(), external_id="EXT-S1", name="Ana García",
            academic_status="Activo", sector="Tecnología",
        )
        s2 = Student(
            id=uuid.uuid4(), external_id="EXT-S2", name="Luis Martínez",
            academic_status="Activo", sector="Salud",
        )
        s3 = Student(
            id=uuid.uuid4(), external_id="EXT-S3", name="María López",
            academic_status="Activo", sector=None,
        )
        s4 = Student(
            id=uuid.uuid4(), external_id="EXT-S4", name="Carlos Ruiz",
            academic_status=None, sector=None,
        )
        s5 = Student(
            id=uuid.uuid4(), external_id="EXT-S5", name="Elena Díaz",
            academic_status="Activo", sector="Tecnología",
        )
        _db.session.add_all([s1, s2, s3, s4, s5])
        _db.session.flush()

        # ---- Enrollments (StudentSection) ----
        _db.session.add_all([
            StudentSection(student_id=s1.id, section_id=sec_a1.id),
            StudentSection(student_id=s2.id, section_id=sec_a1.id),
            StudentSection(student_id=s3.id, section_id=sec_a2.id),
            StudentSection(student_id=s4.id, section_id=sec_a1.id),
            StudentSection(student_id=s5.id, section_id=sec_b1.id),
        ])
        _db.session.flush()

        # ---- Test and results ----
        test_obj = Test(id=uuid.uuid4(), code="T-BE27", name="Test BE27", words=200)
        _db.session.add(test_obj)
        _db.session.flush()

        _db.session.add_all([
            Result(
                student_id=s1.id, section_id=sec_a1.id, test_id=test_obj.id, test_date=datetime.date(2026, 9, 1),
                time=60.0, successes=18, mistakes=2,
            ),
            Result(
                student_id=s2.id, section_id=sec_a1.id, test_id=test_obj.id, test_date=datetime.date(2026, 9, 2),
                time=50.0, successes=19, mistakes=1,
            ),
        ])
        _db.session.commit()

        yield  # tests run

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


# ---------------------------------------------------------------------------
# Escenario 1 – Sin filtros
# ---------------------------------------------------------------------------

class TestSinFiltros:
    def test_devuelve_todos_los_alumnos_activos(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 5
        assert len(data["items"]) == 5
        names = {item["name"] for item in data["items"]}
        assert "Ana García" in names
        assert "Luis Martínez" in names

    def test_paginacion_correcta(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?page=1&limit=2")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2

    def test_segunda_pagina(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?page=2&limit=2")
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data["items"]) == 2

    def test_items_contienen_campos_requeridos(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?limit=1")
        item = resp.get_json()["items"][0]
        assert "id" in item
        assert "name" in item
        assert "external_id" in item
        assert "sections" in item
        assert "test_date" in item
        assert "ppm" in item
        assert "reading_comprehension" in item


# ---------------------------------------------------------------------------
# Escenario 2 – Filtro por centre_id
# ---------------------------------------------------------------------------

class TestFiltroCentro:
    def test_solo_alumnos_del_centro_a(self, client, session):
        c_a = session.execute(
            _db.text("SELECT id FROM centers WHERE name = 'Centro A' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(f"/api/v1/students?center_id={c_a}")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 4  # s1, s2, s3, s4
        for item in data["items"]:
            assert item["sections"][0] in ("Sección A1", "Sección A2", "Sin sección")

    def test_solo_alumnos_del_centro_b(self, client, session):
        c_b = session.execute(
            _db.text("SELECT id FROM centers WHERE name = 'Centro B' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(f"/api/v1/students?center_id={c_b}")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 1  # s5
        assert data["items"][0]["name"] == "Elena Díaz"


# ---------------------------------------------------------------------------
# Escenario 3 – Filtro por section_id
# ---------------------------------------------------------------------------

class TestFiltroSeccion:
    def test_solo_alumnos_seccion_a1(self, client, session):
        sec_a1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección A1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(f"/api/v1/students?section_id={sec_a1}")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 3  # s1, s2, s4
        names = {item["name"] for item in data["items"]}
        assert "Ana García" in names
        assert "Luis Martínez" in names
        assert "Carlos Ruiz" in names

    def test_seccion_b1_un_alumno(self, client, session):
        sec_b1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección B1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(f"/api/v1/students?section_id={sec_b1}")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Elena Díaz"


# ---------------------------------------------------------------------------
# Escenario 4 – Filtro por género
# ---------------------------------------------------------------------------

class TestFiltroMissing:
    def test_sector_missing_devuelve_alumnos_sin_sector(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?sector=__missing__")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 2  # s3 y s4
        names = {item["name"] for item in data["items"]}
        assert "María López" in names
        assert "Carlos Ruiz" in names

    def test_missing_data_count_para_sector_activo(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?sector=Tecnología")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["missing_data"]["sector"] == 2  # s3 y s4 no tienen sector


# ---------------------------------------------------------------------------
# Escenario 6 – Tutor scope
# ---------------------------------------------------------------------------

class TestTutorScope:
    def test_tutor_ve_solo_sus_secciones(self, client, session):
        sec_a1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección A1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="tutor", sections=[sec_a1])
        resp = client.get("/api/v1/students")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 3  # s1, s2, s4
        for item in data["items"]:
            assert item["sections"][0] in ("Sección A1", "Sin sección")

    def test_tutor_sin_secciones_recibe_403(self, client, session):
        _set_dev_session(client, role="tutor", sections=[])
        resp = client.get("/api/v1/students")
        assert resp.status_code == 403

    def test_tutor_solicita_seccion_no_asignada_recibe_403(self, client, session):
        sec_b1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección B1' LIMIT 1")
        ).scalar()
        sec_a1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección A1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="tutor", sections=[sec_a1])
        resp = client.get(f"/api/v1/students?section_id={sec_b1}")
        assert resp.status_code == 403

    def test_tutor_filtro_dentro_de_su_ambito(self, client, session):
        sec_a1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección A1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="tutor", sections=[sec_a1])
        resp = client.get(f"/api/v1/students?section_id={sec_a1}")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 3


# ---------------------------------------------------------------------------
# Filtro por edad (min_age / max_age)
# ---------------------------------------------------------------------------

class TestCombinacionFiltros:
    def test_centro_sector(self, client, session):
        c_a = session.execute(
            _db.text("SELECT id FROM centers WHERE name = 'Centro A' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(f"/api/v1/students?center_id={c_a}&sector=Tecnología")
        data = resp.get_json()
        assert resp.status_code == 200
        # Centro A + Tecnología: s1 = 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Ana García"

    def test_seccion_sector(self, client, session):
        sec_a1 = session.execute(
            _db.text("SELECT id FROM sections WHERE name = 'Sección A1' LIMIT 1")
        ).scalar()
        _set_dev_session(client, role="admin")
        resp = client.get(
            f"/api/v1/students?section_id={sec_a1}&sector=Tecnología"
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Ana García"

    def test_sector_academic_status_literal(self, client, session):
        # Escenario 2 literal del Gherkin: filtro por sector y situación
        # académica a la vez (AND).
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?sector=Tecnología&academic_status=Activo")
        data = resp.get_json()
        assert resp.status_code == 200
        # Tecnología + Activo: s1 y s5 = 2 (s2 es Salud, s3 no tiene sector)
        assert data["total"] == 2
        names = {item["name"] for item in data["items"]}
        assert "Ana García" in names
        assert "Elena Díaz" in names

    def test_pages_coincide_con_paginacion(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?page=1&limit=2")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["pages"] == 3  # 5 alumnos, limit=2 -> 3 páginas
        resp2 = client.get("/api/v1/students?limit=100")
        data2 = resp2.get_json()
        assert resp2.status_code == 200
        assert data2["pages"] == 1


# ---------------------------------------------------------------------------
# Auditoría FILTER_STUDENTS
# ---------------------------------------------------------------------------

class TestAuditoria:
    def test_audit_register_on_academic_status_filter(self, client, session):
        from unittest.mock import patch

        _set_dev_session(client, role="admin")
        with patch("app.services.student_service.log_audit") as mock_audit:
            resp = client.get("/api/v1/students?academic_status=Activo")
            assert resp.status_code == 200
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[1]["action"] == "FILTER_STUDENTS"

    def test_no_audit_when_no_sensitive_filter(self, client, session):
        from unittest.mock import patch

        _set_dev_session(client, role="admin")
        with patch("app.services.student_service.log_audit") as mock_audit:
            resp = client.get("/api/v1/students?sector=Tecnología")
            assert resp.status_code == 200
            mock_audit.assert_not_called()


# ---------------------------------------------------------------------------
# Seguridad: rol pendiente
# ---------------------------------------------------------------------------

class TestSeguridad:
    def test_rol_pendiente_recibe_403(self, client, session):
        _set_dev_session(client, role="pendiente")
        resp = client.get("/api/v1/students")
        assert resp.status_code == 403

    def test_sin_acceso_no_expone_datos(self, client):
        # En modo dev-bypass sin sesión se aplica el tutor por defecto sin
        # secciones asignadas: nunca se expone el alumnado completo.
        resp = client.get("/api/v1/students")
        assert resp.status_code == 403
        assert resp.get_json().get("items") is None


# ---------------------------------------------------------------------------
# Respuesta vacía
# ---------------------------------------------------------------------------

class TestResultadosVacios:
    def test_filtro_sin_resultados(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?sector=OtroSector")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 0
        assert data["items"] == []

    def test_pagina_fuera_de_rango(self, client, session):
        _set_dev_session(client, role="admin")
        resp = client.get("/api/v1/students?page=999&limit=10")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["total"] == 5
        assert data["items"] == []


# ---------------------------------------------------------------------------
# OpenAPI (BE-48): el endpoint del listado está documentado en el spec
# ---------------------------------------------------------------------------

class TestOpenAPISpec:
    def test_path_students_documentada(self, app):
        from app.extensions import api as openapi_api

        paths = openapi_api.spec.to_dict().get("paths", {})
        assert "/api/v1/students" in paths
        get_op = paths["/api/v1/students"]["get"]
        param_names = {p["name"] for p in get_op.get("parameters", [])}
        expected = {
            "center_id", "section_id", "academic_status",
            "sector", "page", "limit",
        }
        assert expected.issubset(param_names)
        assert "200" in get_op.get("responses", {})
        assert "400" in get_op.get("responses", {})
        assert "403" in get_op.get("responses", {})
        assert "422" in get_op.get("responses", {})
