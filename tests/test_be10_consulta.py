import datetime
import uuid
import pytest

from app import create_app
from app.config import TestingConfig
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


class NoBypassConfig(TestingConfig):
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False


@pytest.fixture
def setup_data(session):
    """Datos base de BE-10: centros/secciones activos y deshabilitados, alumnado matriculado."""
    center_active = Center(name="Colegio Cervantes")
    center_disabled = Center(
        name="Colegio Antiguo",
        disabled_at=datetime.date(2025, 6, 30),
    )
    session.add_all([center_active, center_disabled])
    session.flush()

    section_a = Section(
        name="1º ESO A",
        center_id=center_active.id,
        academic_year="2025-2026",
    )
    section_b = Section(
        name="1º ESO B",
        center_id=center_active.id,
        academic_year="2025-2026",
    )
    section_empty = Section(
        name="1º ESO C",
        center_id=center_active.id,
        academic_year="2025-2026",
    )
    section_disabled = Section(
        name="2º ESO A",
        center_id=center_active.id,
        academic_year="2024-2025",
        disabled_at=datetime.date(2025, 6, 30),
    )
    section_other_center = Section(
        name="Única",
        center_id=center_disabled.id,
    )
    center_other = Center(name="Colegio Altamira")
    session.add(center_other)
    session.flush()
    section_foreign = Section(
        name="1º Primaria",
        center_id=center_other.id,
        academic_year="2025-2026",
    )
    session.add_all([section_a, section_b, section_empty, section_disabled, section_other_center, section_foreign])
    session.flush()

    s1 = Student(name="Aitor Ortiz", external_id="AIT-001")
    s2 = Student(name="Leire Blanco", external_id="LEI-002")
    s3 = Student(name="Mikel Gómez", external_id="MIK-003")
    s4_disabled = Student(
        name="Elena Ruiz",
        external_id="ELE-004",
        disabled_at=datetime.date(2026, 1, 15),
    )
    session.add_all([s1, s2, s3, s4_disabled])
    session.flush()

    session.add_all([
        StudentSection(student_id=s1.id, section_id=section_a.id),
        StudentSection(student_id=s2.id, section_id=section_a.id),
        StudentSection(student_id=s4_disabled.id, section_id=section_a.id),
        StudentSection(student_id=s3.id, section_id=section_b.id),
    ])
    session.commit()

    return {
        "center_active": center_active,
        "center_disabled": center_disabled,
        "center_other": center_other,
        "section_a": section_a,
        "section_b": section_b,
        "section_empty": section_empty,
        "section_disabled": section_disabled,
        "section_foreign": section_foreign,
        "students": [s1, s2, s3, s4_disabled],
    }


def test_scenario_1_list_active_centers(client, setup_data):
    """
    Escenario 1: Listado de centros
    Dado un usuario con sesión activa y rol asignado
    Cuando consulta GET /api/centers
    Entonces recibe la lista de centros activos
    Y devuelve 200 OK (los deshabilitados no aparecen)
    """
    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get("/api/v1/centers")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    center = data[0]
    assert center["name"] == "Colegio Altamira"
    assert center["id"] == str(setup_data["center_other"].id)
    assert "external_id" in center

    cervical = next(c for c in data if c["name"] == "Colegio Cervantes")
    assert cervical["id"] == str(setup_data["center_active"].id)

    # Ruta directa sin prefijo v1
    resp_direct = client.get("/api/centers")
    assert resp_direct.status_code == 200
    assert len(resp_direct.get_json()) == 2


def test_scenario_2_sections_of_center(client, setup_data):
    """
    Escenario 2: Secciones de un centro
    Dado un centro existente
    Cuando consulta GET /api/centers/{id}/sections
    Entonces recibe las secciones activas de ese centro
    Y devuelve 200 OK
    """
    center_active = setup_data["center_active"]
    section_disabled = setup_data["section_disabled"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get(f"/api/v1/centers/{center_active.id}/sections")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 3  # 1º ESO A, 1º ESO B, 1º ESO C
    names = [s["name"] for s in data]
    assert names == ["1º ESO A", "1º ESO B", "1º ESO C"]

    section = data[0]
    assert section["id"] == str(setup_data["section_a"].id)
    assert section["center_id"] == str(center_active.id)
    assert section["academic_year"] == "2025-2026"
    assert section["students_count"] == 2

    # La sección deshabilitada no aparece
    ids = [s["id"] for s in data]
    assert str(section_disabled.id) not in ids


def test_scenario_3_students_of_section(client, setup_data):
    """
    Escenario 3: Alumnado de una sección
    Dado una sección existente
    Cuando consulta GET /api/sections/{id}/students
    Entonces recibe el alumnado activo matriculado en esa sección
    Y devuelve 200 OK
    """
    section_a = setup_data["section_a"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section_a.id)]},
    )

    resp = client.get(f"/api/v1/sections/{section_a.id}/students")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert [s["name"] for s in data] == ["Aitor Ortiz", "Leire Blanco"]

    student = data[0]
    assert student["id"] == str(setup_data["students"][0].id)
    assert student["external_id"] == "AIT-001"

    # El alumno deshabilitado y los de otras secciones no aparecen
    assert "Elena Ruiz" not in [s["name"] for s in data]
    assert "Mikel Gómez" not in [s["name"] for s in data]

    # Ruta directa sin prefijo v1
    resp_direct = client.get(f"/api/sections/{section_a.id}/students")
    assert resp_direct.status_code == 200
    assert len(resp_direct.get_json()) == 2


def test_scenario_3b_empty_section_returns_200_empty_list(client, setup_data):
    """Una sección sin alumnado devuelve lista vacía con 200 OK."""
    section_empty = setup_data["section_empty"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section_empty.id)]},
    )

    resp = client.get(f"/api/v1/sections/{section_empty.id}/students")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_scenario_4_nonexistent_resource_returns_404(client, setup_data):
    """
    Escenario 4: Recurso inexistente
    Dado un identificador que no corresponde a ningún centro o sección
    Cuando se consulta
    Entonces el sistema devuelve 404 Not Found
    """
    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    random_uuid = uuid.uuid4()

    # Sección inexistente
    resp_section = client.get(f"/api/v1/sections/{random_uuid}/students")
    assert resp_section.status_code == 404
    assert resp_section.get_json()["error"] == "NOT_FOUND"

    # Centro inexistente
    resp_center = client.get(f"/api/v1/centers/{random_uuid}/sections")
    assert resp_center.status_code == 404
    assert resp_center.get_json()["error"] == "NOT_FOUND"

    # Centro deshabilitado equivale a inexistente
    resp_disabled_center = client.get(f"/api/v1/centers/{setup_data['center_disabled'].id}/sections")
    assert resp_disabled_center.status_code == 404

    # Sección deshabilitada equivale a inexistente
    resp_disabled_section = client.get(f"/api/v1/sections/{setup_data['section_disabled'].id}/students")
    assert resp_disabled_section.status_code == 404

    # Identificador malformado devuelve 400 Bad Request
    resp_bad_center = client.get("/api/v1/centers/id-no-valido/sections")
    assert resp_bad_center.status_code == 400

    resp_bad_section = client.get("/api/v1/sections/id-no-valido/students")
    assert resp_bad_section.status_code == 400


def test_scenario_5_read_only_resources_return_405(client, setup_data):
    """
    Escenario 5: Recursos de solo lectura
    Dado un usuario con cualquier rol
    Cuando intenta un POST, PUT o DELETE sobre centros o secciones
    Entonces el sistema no ofrece esa operación
    Y devuelve 405 Method Not Allowed
    """
    section_a = setup_data["section_a"]
    center_active = setup_data["center_active"]

    client.post("/api/dev/session", json={"role": "admin", "sections": []})

    # POST /api/centers
    resp = client.post("/api/centers", json={"name": "Nuevo Centro"})
    assert resp.status_code == 405

    # PUT /api/centers -> 405
    resp = client.put("/api/centers")
    assert resp.status_code == 405

    # DELETE /api/centers -> 405
    resp = client.delete("/api/centers")
    assert resp.status_code == 405

    # POST /api/centers/{id}/sections -> 405
    resp = client.post(f"/api/centers/{center_active.id}/sections", json={})
    assert resp.status_code == 405

    # PUT /api/centers/{id}/sections -> 405
    resp = client.put(f"/api/centers/{center_active.id}/sections", json={})
    assert resp.status_code == 405

    # DELETE /api/centers/{id}/sections -> 405
    resp = client.delete(f"/api/centers/{center_active.id}/sections")
    assert resp.status_code == 405

    # POST /api/sections/{id}/students -> 405
    resp = client.post(f"/api/sections/{section_a.id}/students", json={})
    assert resp.status_code == 405

    # PUT /api/sections/{id}/students -> 405
    resp = client.put(f"/api/sections/{section_a.id}/students", json={})
    assert resp.status_code == 405

    # DELETE /api/sections/{id}/students -> 405
    resp = client.delete(f"/api/sections/{section_a.id}/students")
    assert resp.status_code == 405


def test_scenario_6_tutor_limited_to_assigned_sections(client, setup_data):
    """
    Escenario 6: Tutor limitado a sus secciones
    Dado un tutor con una sección asignada
    Cuando consulta el alumnado de una sección que no tiene asignada
    Entonces el sistema deniega la operación
    Y devuelve 403 Forbidden
    """
    section_a = setup_data["section_a"]
    section_b = setup_data["section_b"]

    # Tutor asignado únicamente a section_b
    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section_b.id)]},
    )

    # Consulta section_a -> 403
    resp = client.get(f"/api/v1/sections/{section_a.id}/students")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # Su sección asignada -> 200
    resp_ok = client.get(f"/api/v1/sections/{section_b.id}/students")
    assert resp_ok.status_code == 200
    assert [s["name"] for s in resp_ok.get_json()] == ["Mikel Gómez"]


def test_pending_role_returns_403(client, setup_data):
    """Usuario con rol 'pendiente' recibe 403 Forbidden al consultar alumnado."""
    section_a = setup_data["section_a"]

    client.post(
        "/api/dev/session",
        json={"role": "pendiente", "sections": [str(section_a.id)]},
    )

    resp = client.get(f"/api/v1/sections/{section_a.id}/students")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_unauthenticated_returns_401():
    """Petición sin autenticación devuelve 401 Unauthorized."""
    app = create_app(NoBypassConfig)
    unauth_client = app.test_client()

    resp = unauth_client.get("/api/centers")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "UNAUTHORIZED"

    resp_section = unauth_client.get("/api/sections/any-id/students")
    assert resp_section.status_code == 401


def test_coordinator_can_view_any_section(client, setup_data):
    """Un coordinador ve el alumnado de cualquier sección sin restricción."""
    section_a = setup_data["section_a"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get(f"/api/v1/sections/{section_a.id}/students")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_center_sections_exclude_disabled_center_sections(client, setup_data):
    """Las secciones de un centro deshabilitado no se pueden consultar."""
    center_disabled = setup_data["center_disabled"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get(f"/api/v1/centers/{center_disabled.id}/sections")
    assert resp.status_code == 404


def test_centers_include_sections_count(client, setup_data):
    """Escenario 1 (FE-25): cada centro incluye sections_count de secciones activas."""
    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get("/api/v1/centers")
    assert resp.status_code == 200

    by_name = {c["name"]: c for c in resp.get_json()}
    assert by_name["Colegio Cervantes"]["sections_count"] == 3
    assert by_name["Colegio Altamira"]["sections_count"] == 1


def test_sections_include_students_count(client, setup_data):
    """Escenario 2 (FE-25): cada sección incluye students_count de alumnos activos."""
    center_active = setup_data["center_active"]

    client.post("/api/dev/session", json={"role": "coordinator", "sections": []})

    resp = client.get(f"/api/v1/centers/{center_active.id}/sections")
    assert resp.status_code == 200

    by_name = {s["name"]: s for s in resp.get_json()}
    assert by_name["1º ESO A"]["students_count"] == 2
    assert by_name["1º ESO B"]["students_count"] == 1
    assert by_name["1º ESO C"]["students_count"] == 0


def test_tutor_sees_only_centers_and_sections_assigned(client, setup_data):
    """
    Escenario 4 (FE-25): tutor con dos secciones asignadas solo ve su centro
    y sus secciones, con sus conteos.
    """
    section_a = setup_data["section_a"]
    section_b = setup_data["section_b"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section_a.id), str(section_b.id)]},
    )

    resp = client.get("/api/v1/centers")
    assert resp.status_code == 200
    data = resp.get_json()
    assert [c["name"] for c in data] == ["Colegio Cervantes"]
    assert data[0]["sections_count"] == 2

    resp_sections = client.get(f"/api/v1/centers/{setup_data['center_active'].id}/sections")
    assert resp_sections.status_code == 200
    sections = resp_sections.get_json()
    assert [s["name"] for s in sections] == ["1º ESO A", "1º ESO B"]
    by_name = {s["name"]: s for s in sections}
    assert by_name["1º ESO A"]["students_count"] == 2
    assert by_name["1º ESO B"]["students_count"] == 1


def test_tutor_cannot_access_foreign_center_sections(client, setup_data):
    """
    Escenario 4 (FE-25): un tutor asignado a secciones de otro centro recibe
    403 al consultar las secciones de un centro ajeno.
    """
    section_b = setup_data["section_b"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(section_b.id)]},
    )

    resp = client.get(f"/api/v1/centers/{setup_data['center_other'].id}/sections")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"

    # En su centro solo ve su sección asignada
    resp_ok = client.get(f"/api/v1/centers/{setup_data['center_active'].id}/sections")
    assert resp_ok.status_code == 200
    assert [s["name"] for s in resp_ok.get_json()] == ["1º ESO B"]


def test_tutor_without_sections_gets_403_on_center_sections(client, setup_data):
    """Un tutor sin secciones asignadas recibe 403 en un centro y lista vacía de centros."""
    client.post("/api/dev/session", json={"role": "tutor", "sections": []})

    resp = client.get(f"/api/v1/centers/{setup_data['center_active'].id}/sections")
    assert resp.status_code == 403

    resp_centers = client.get("/api/v1/centers")
    assert resp_centers.status_code == 200
    assert resp_centers.get_json() == []


def test_pending_role_gets_403_on_centers_and_sections(client, setup_data):
    """El rol 'pendiente' recibe 403 también al listar centros y sus secciones."""
    client.post("/api/dev/session", json={"role": "pendiente", "sections": []})

    assert client.get("/api/v1/centers").status_code == 403
    assert client.get(f"/api/v1/centers/{setup_data['center_active'].id}/sections").status_code == 403