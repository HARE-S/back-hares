"""Tests de BE-50: alta y modificación manual de alumnado, centros y secciones.

Cubre los escenarios 1 a 7 de la historia: CRUD manual, duplicados,
baja lógica, política de conflictos con la importación de Alexia,
seguridad (solo admin) y auditoría con valor anterior.
"""

import uuid

import pytest
from sqlalchemy import select

from app.core.audit import clear_audit_logs, get_audit_logs
from app.extensions import db
from app.importer.loader import StudentImporter
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


@pytest.fixture
def setup_data(session):
    """Centro y secciones base para el CRUD manual."""
    clear_audit_logs()
    c1 = Center(name="Colegio Cervantes")
    c2 = Center(name="Colegio La Salle")
    session.add_all([c1, c2])
    session.flush()
    sec_a = Section(name="1º ESO A", center_id=c1.id, academic_year="2025-2026")
    sec_b = Section(name="1º ESO B", center_id=c1.id, academic_year="2025-2026")
    sec_c2 = Section(name="2º ESO A", center_id=c2.id, academic_year="2025-2026")
    session.add_all([sec_a, sec_b, sec_c2])
    session.commit()
    return {"c1": c1, "c2": c2, "sec_a": sec_a, "sec_b": sec_b, "sec_c2": sec_c2}


def _login(client, role):
    client.post("/api/dev/session", json={"role": role})


def _audit(action, resource_type=None):
    logs = [l for l in get_audit_logs() if l["action"] == action]
    if resource_type:
        logs = [l for l in logs if l["resource_type"] == resource_type]
    return logs


# ----------------------------------------------------------------- Escenario 1

def test_escenario1_alta_manual_alumno_201(client, session, setup_data):
    _login(client, "admin")
    resp = client.post(
        "/api/v1/students",
        json={
            "name": "Lara Núñez",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
            "area": "Funcional",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    assert data["name"] == "Lara Núñez"
    assert data["external_id"].startswith("MAN-")
    assert data["origin"] == "manual"
    assert data["area"] == "Funcional"
    assert [s["id"] for s in data["sections"]] == [str(setup_data["sec_a"].id)]

    student = session.scalars(
        select(Student).where(Student.name == "Lara Núñez")
    ).first()
    assert student is not None
    assert student.external_id.startswith("MAN-")
    assert student.origin == "manual"

    create_logs = _audit("CREATE_STUDENT_MANUAL", "student")
    assert create_logs, "Falta auditoría de alta manual"


# ----------------------------------------------------------------- Escenario 2

def test_escenario2_modificacion_auditoria_valor_anterior(client, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/students",
        json={
            "name": "Ana Pérez",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
        },
    ).get_json()

    resp = client.patch(
        f"/api/v1/students/{created['id']}",
        json={"name": "Ana Pérez García", "area": "Literario"},
    )
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["name"] == "Ana Pérez García"

    update_logs = _audit("UPDATE_STUDENT", "student")
    assert update_logs
    details = update_logs[-1]["details"]
    assert details["name"]["anterior"] == "Ana Pérez"
    assert details["name"]["nuevo"] == "Ana Pérez García"
    assert details["area"]["anterior"] == "Sin área"
    assert details["area"]["nuevo"] == "Literario"


def test_escenario2_alumno_inexistente_404(client, setup_data):
    _login(client, "admin")
    resp = client.patch(
        f"/api/v1/students/{uuid.uuid4()}",
        json={"name": "Nadie"},
    )
    assert resp.status_code == 404


# ------------------------------------------------------ Escenario 3 y actualización

def test_escenario3_importacion_no_borra_alta_manual(session, client, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/students",
        json={
            "name": "Manual Persistente",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
        },
    ).get_json()

    csv_content = (
        "student_id;student_name;sections;center\n"
        f"ALEX-1;Alumno De Alexia;{setup_data['sec_a'].name};{setup_data['c1'].name}\n"
    )
    summary = StudentImporter(
        session, current_user={"email": "dev.admin@penascal.org"}
    ).import_from_csv(csv_content, commit=True)

    assert summary["students_created"] == 1
    still = session.scalars(
        select(Student).where(Student.id == created["id"])
    ).first()
    assert still is not None, "El alta manual se perdió tras reimportar"
    assert still.external_id.startswith("MAN-")
    assert still.origin == "manual"

    enrollments = session.scalars(
        select(StudentSection).where(StudentSection.student_id == still.id)
    ).all()
    assert len(enrollments) == 1


def test_escenario4_alexia_manda_sobre_modificado_a_mano(session, setup_data):
    alex = Student(
        external_id="ALEX-4",
        name="Nombre De Alexia",
        origin="alexia",
    )
    session.add(alex)
    session.flush()
    session.add(StudentSection(student_id=alex.id, section_id=setup_data["sec_a"].id))
    session.commit()

    csv_content = (
        "student_id;student_name;sections;center\n"
        f"ALEX-4;Nombre Corregido Manual;{setup_data['sec_a'].name};{setup_data['c1'].name}\n"
    )
    summary = StudentImporter(
        session, current_user={"email": "dev.admin@penascal.org"}
    ).import_from_csv(csv_content, commit=True)

    assert summary["students_updated"] == 1
    session.expire_all()
    refreshed = session.get(Student, alex.id)
    assert refreshed.name == "Nombre Corregido Manual"

    overwrite_logs = _audit("IMPORT_OVERWRITE_STUDENT", "student")
    assert overwrite_logs
    details = overwrite_logs[-1]["details"]
    assert details["anterior"] == "Nombre De Alexia"
    assert details["nuevo"] == "Nombre Corregido Manual"


# ----------------------------------------------------------------- Escenario 5

def test_escenario5_baja_logica_alumno(client, session, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/students",
        json={
            "name": "Baja Lógica",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
        },
    ).get_json()

    resp = client.delete(f"/api/v1/students/{created['id']}")
    assert resp.status_code == 204

    student = session.get(Student, created["id"])
    assert student.disabled_at is not None

    deactivate_logs = _audit("DEACTIVATE_STUDENT", "student")
    assert deactivate_logs


# ----------------------------------------------------------------- Escenario 6

@pytest.mark.parametrize("role", ["tutor", "coordinator"])
def test_escenario6_no_admin_403(client, setup_data, role):
    _login(client, role)
    resp = client.post(
        "/api/v1/students",
        json={
            "name": "Intruso",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
        },
    )
    assert resp.status_code == 403


def test_escenario6_no_admin_403_centros_secciones(client, setup_data):
    _login(client, "tutor")
    assert client.post("/api/v1/centers", json={"name": "X"}).status_code == 403
    assert client.post(
        "/api/v1/sections",
        json={"name": "1º A", "center_id": str(setup_data["c1"].id)},
    ).status_code == 403


# ----------------------------------------------------------------- Escenario 7

def test_escenario7_seccion_sin_centro_400(client):
    _login(client, "admin")
    resp = client.post(
        "/api/v1/sections",
        json={"name": "1º ESO C"},
    )
    assert resp.status_code == 400


# ------------------------------------------------------------------- Centros

def test_crud_manual_centros_y_duplicado_409(client, setup_data):
    _login(client, "admin")
    created = client.post("/api/v1/centers", json={"name": "Colegio Nuevo"})
    assert created.status_code == 201, created.get_json()
    data = created.get_json()
    assert data["origin"] == "manual"
    assert _audit("CREATE_CENTER_MANUAL", "center")

    renamed = client.patch(f"/api/v1/centers/{data['id']}", json={"name": "Colegio Renovado"})
    assert renamed.status_code == 200, renamed.get_json()
    assert renamed.get_json()["name"] == "Colegio Renovado"
    update_logs = _audit("UPDATE_CENTER", "center")
    assert update_logs
    assert update_logs[-1]["details"]["name"]["anterior"] == "Colegio Nuevo"

    duplicated = client.post("/api/v1/centers", json={"name": "Colegio Renovado"})
    assert duplicated.status_code == 409, duplicated.get_json()

    deleted = client.delete(f"/api/v1/centers/{data['id']}")
    assert deleted.status_code == 204
    assert _audit("DEACTIVATE_CENTER", "center")


def test_centro_inexistente_404(client):
    _login(client, "admin")
    assert client.patch(f"/api/v1/centers/{uuid.uuid4()}", json={"name": "X"}).status_code == 404
    assert client.delete(f"/api/v1/centers/{uuid.uuid4()}").status_code == 404


# ------------------------------------------------------------------ Secciones

def test_crud_manual_secciones_duplicado_y_400(client, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/sections",
        json={"name": "1º ESO D", "center_id": str(setup_data["c1"].id), "academic_year": "2025-2026"},
    )
    assert created.status_code == 201, created.get_json()
    data = created.get_json()
    assert data["origin"] == "manual"
    assert _audit("CREATE_SECTION_MANUAL", "section")

    duplicated = client.post(
        "/api/v1/sections",
        json={"name": "1º ESO D", "center_id": str(setup_data["c1"].id)},
    )
    assert duplicated.status_code == 409, duplicated.get_json()

    other_center = client.post(
        "/api/v1/sections",
        json={"name": "1º ESO D", "center_id": str(setup_data["c2"].id)},
    )
    assert other_center.status_code == 201

    renamed = client.patch(
        f"/api/v1/sections/{data['id']}", json={"name": "1º ESO E"}
    )
    assert renamed.status_code == 200, renamed.get_json()
    update_logs = _audit("UPDATE_SECTION", "section")
    assert update_logs
    assert update_logs[-1]["details"]["name"]["nuevo"] == "1º ESO E"

    deleted = client.delete(f"/api/v1/sections/{data['id']}")
    assert deleted.status_code == 204
    assert _audit("DEACTIVATE_SECTION", "section")


def test_crud_manual_secciones_penascal_dates_and_sector(client, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/sections",
        json={
            "name": "Soldadura 1 A",
            "center_id": str(setup_data["c1"].id),
            "academic_year": "2025-2026",
            "start_date": "2025-09-01",
            "end_date": "2026-06-30",
            "sector": "Metal",
        },
    )
    assert created.status_code == 201, created.get_json()
    data = created.get_json()
    assert data["sector"] == "Metal"
    assert data["start_date"] == "2025-09-01"
    assert data["end_date"] == "2026-06-30"

    updated = client.patch(
        f"/api/v1/sections/{data['id']}",
        json={"sector": "Soldadura Avanzada", "end_date": "2026-07-15"},
    )
    assert updated.status_code == 200, updated.get_json()
    assert updated.get_json()["sector"] == "Soldadura Avanzada"
    assert updated.get_json()["end_date"] == "2026-07-15"


def test_seccion_centro_inexistente_404(client):
    _login(client, "admin")
    resp = client.post(
        "/api/v1/sections",
        json={"name": "1º ESO Z", "center_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404


# ---------------------------------------------------- Matrícula en secciones

def test_asignar_y_retirar_seccion(client, setup_data):
    _login(client, "admin")
    created = client.post(
        "/api/v1/students",
        json={
            "name": "Matrícula",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_a"].id)],
        },
    ).get_json()

    assigned = client.post(
        f"/api/v1/students/{created['id']}/sections",
        json={"section_id": str(setup_data["sec_b"].id)},
    )
    assert assigned.status_code == 200, assigned.get_json()
    assert len(assigned.get_json()["sections"]) == 2
    assert _audit("ASSIGN_STUDENT_SECTION", "student_section")

    repeated = client.post(
        f"/api/v1/students/{created['id']}/sections",
        json={"section_id": str(setup_data["sec_b"].id)},
    )
    assert repeated.status_code == 409, repeated.get_json()

    removed = client.delete(
        f"/api/v1/students/{created['id']}/sections/{setup_data['sec_b'].id}"
    )
    assert removed.status_code == 204
    assert _audit("REMOVE_STUDENT_SECTION", "student_section")


def test_seccion_de_otro_centro_400(client, setup_data):
    _login(client, "admin")
    resp = client.post(
        "/api/v1/students",
        json={
            "name": "Cruce Centros",
            "center_id": str(setup_data["c1"].id),
            "section_ids": [str(setup_data["sec_c2"].id)],
        },
    )
    assert resp.status_code == 400, resp.get_json()