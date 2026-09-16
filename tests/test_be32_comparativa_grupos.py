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
    """Datos base para BE-32: dos centros con datos y uno vacío."""
    clear_audit_logs()

    c1 = Center(name="Colegio Cervantes")
    c2 = Center(name="Colegio La Salle")
    c_empty = Center(name="Colegio Sin Datos")
    session.add_all([c1, c2, c_empty])
    session.flush()

    sec1 = Section(name="1º ESO A", center_id=c1.id, academic_year="2025-2026")
    sec2 = Section(name="1º ESO B", center_id=c1.id, academic_year="2025-2026")
    sec_empty = Section(name="1º ESO C", center_id=c1.id, academic_year="2025-2026")
    sec3 = Section(name="2º ESO A", center_id=c2.id, academic_year="2025-2026")
    session.add_all([sec1, sec2, sec_empty, sec3])
    session.flush()

    # sec1: 6 alumnos (4 Funcional, 2 Literario), 1 resultado cada uno.
    a1 = Student(name="Aitor Ortiz", sector="Funcional")
    a2 = Student(name="Leire Blanco", sector="Funcional")
    a3 = Student(name="Lucía Morales", sector="Funcional")
    a4 = Student(name="Mikel Gómez", sector="Funcional")
    a5 = Student(name="Nerea Díaz", sector="Literario")
    a6 = Student(name="Iker Alonso", sector="Literario")
    session.add_all([a1, a2, a3, a4, a5, a6])
    session.flush()
    session.add_all([
        StudentSection(student_id=a1.id, section_id=sec1.id),
        StudentSection(student_id=a2.id, section_id=sec1.id),
        StudentSection(student_id=a3.id, section_id=sec1.id),
        StudentSection(student_id=a4.id, section_id=sec1.id),
        StudentSection(student_id=a5.id, section_id=sec1.id),
        StudentSection(student_id=a6.id, section_id=sec1.id),
    ])

    # sec2: 2 alumnos (Literario). b1 con 2 resultados, b2 con 1.
    b1 = Student(name="Gonzalo Ruiz", sector="Literario")
    b2 = Student(name="Paula Vega", sector="Literario")
    session.add_all([b1, b2])
    session.flush()
    session.add_all([
        StudentSection(student_id=b1.id, section_id=sec2.id),
        StudentSection(student_id=b2.id, section_id=sec2.id),
    ])

    # sec3 (centro 2): 2 alumnos (Funcional), 1 resultado cada uno.
    c_s1 = Student(name="María Santos", sector="Funcional")
    c_s2 = Student(name="Hugo Molina", sector="Funcional")
    session.add_all([c_s1, c_s2])
    session.flush()
    session.add_all([
        StudentSection(student_id=c_s1.id, section_id=sec3.id),
        StudentSection(student_id=c_s2.id, section_id=sec3.id),
    ])

    test1 = Test(code="1CL", name="Prueba Inicial", words=300)
    test2 = Test(code="2CL", name="Prueba Segunda", words=300)
    session.add_all([test1, test2])
    session.flush()

    session.add_all([
        # sec1: 6 resultados (ppm / acc)
        Result(student_id=a1.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=120, successes=15, mistakes=3),  # 150.0 / 67.5
        Result(student_id=a2.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=100, successes=15, mistakes=3),  # 180.0 / 67.5
        Result(student_id=a3.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=150, successes=15, mistakes=3),  # 120.0 / 67.5
        Result(student_id=a4.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=90, successes=15, mistakes=3),   # 200.0 / 67.5
        Result(student_id=a5.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=75, successes=15, mistakes=3),   # 240.0 / 67.5
        Result(student_id=a6.id, section_id=sec1.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=200, successes=15, mistakes=3),  # 90.0 / 67.5
        # sec2
        Result(student_id=b1.id, section_id=sec2.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=100, successes=18, mistakes=2),  # 180.0 / 85.0
        Result(student_id=b1.id, section_id=sec2.id, test_id=test2.id,
               test_date=datetime.date(2025, 12, 15), time=200, successes=8, mistakes=6),  # 90.0 / 25.0
        Result(student_id=b2.id, section_id=sec2.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=120, successes=15, mistakes=3),  # 150.0 / 67.5
        # sec3 (centro 2)
        Result(student_id=c_s1.id, section_id=sec3.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=100, successes=18, mistakes=2),  # 180.0 / 85.0
        Result(student_id=c_s2.id, section_id=sec3.id, test_id=test1.id,
               test_date=datetime.date(2025, 10, 1), time=120, successes=15, mistakes=3),  # 150.0 / 67.5
    ])
    session.commit()

    return {
        "centers": [c1, c2, c_empty],
        "sections": [sec1, sec2, sec_empty, sec3],
    }


def _get_dev_session(client, role, sections=None):
    client.post(
        "/api/dev/session",
        json={"role": role, "sections": sections or []},
    )


def _group(data, name):
    return next((g for g in data["groups"] if g["name"] == name), None)


# --------------------------------------------------------------------------- 1

def test_scenario_1_compara_dos_secciones_media_ppm_y_aciertos(client, setup_data):
    sec1, sec2 = setup_data["sections"][0], setup_data["sections"][1]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec1.id)),
                      ("section_ids", str(sec2.id))],
    )
    assert resp.status_code == 200
    data = resp.get_json()

    group1 = _group(data, "1º ESO A")
    group2 = _group(data, "1º ESO B")
    assert group1 is not None and group2 is not None

    # sec1: PPM medio 163.33, aciertos 67.5
    assert group1["mean_ppm"] == pytest.approx(163.33, abs=0.01)
    assert group1["mean_accuracy"] == pytest.approx(67.5, abs=0.01)
    assert group1["mean_vef"] == pytest.approx(110.25, abs=0.01)

    # sec2: PPM medio 140.0, aciertos 59.17
    assert group2["mean_ppm"] == pytest.approx(140.0, abs=0.01)
    assert group2["mean_accuracy"] == pytest.approx(59.17, abs=0.01)
    assert group2["mean_vef"] == pytest.approx(92.25, abs=0.01)


# --------------------------------------------------------------------------- 2

def test_scenario_2_cada_grupo_indica_tamano_por_alumnos_y_pruebas(client, setup_data):
    sec1, sec2 = setup_data["sections"][0], setup_data["sections"][1]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec1.id)),
                      ("section_ids", str(sec2.id))],
    )
    assert resp.status_code == 200
    data = resp.get_json()

    group1 = _group(data, "1º ESO A")
    group2 = _group(data, "1º ESO B")

    assert group1["students_count"] == 6
    assert group1["results_count"] == 6

    assert group2["students_count"] == 2
    assert group2["results_count"] == 3


# --------------------------------------------------------------------------- 3

def test_scenario_3_grupo_poco_representativo_por_defecto(client, setup_data):
    sec1, sec2 = setup_data["sections"][0], setup_data["sections"][1]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec1.id)),
                      ("section_ids", str(sec2.id))],
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["min_sample"] == 5

    group1 = _group(data, "1º ESO A")
    group2 = _group(data, "1º ESO B")

    assert group1["is_representative"] is True
    assert group1["warning"] is None

    assert group2["is_representative"] is False
    assert group2["warning"] is not None
    assert "poco representativo" in group2["warning"]


def test_escenario_3_umbral_configurable_por_parametro(client, setup_data):
    sec1, sec2 = setup_data["sections"][0], setup_data["sections"][1]

    _get_dev_session(client, "coordinator")

    # min_sample=2: ambos grupos lo cumplen
    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("min_sample", 2),
                      ("section_ids", str(sec1.id)), ("section_ids", str(sec2.id))],
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["min_sample"] == 2
    assert _group(data, "1º ESO B")["is_representative"] is True

    # min_sample=7: la sección A (6 alumnos) deja de ser representativa
    resp2 = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("min_sample", 7),
                      ("section_ids", str(sec1.id)), ("section_ids", str(sec2.id))],
    )
    assert resp2.status_code == 200
    assert _group(resp2.get_json(), "1º ESO A")["is_representative"] is False


# --------------------------------------------------------------------------- 4

def test_scenario_4_comparacion_por_centro(client, setup_data):
    center1, center2, center_empty = setup_data["centers"]

    _get_dev_session(client, "coordinator")

    resp = client.get("/api/v1/comparison/groups", query_string={"group_by": "center"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["group_by"] == "center"

    # Orden alfabético: Cervantes, La Salle, Sin Datos
    names = [g["name"] for g in data["groups"]]
    assert names == ["Colegio Cervantes", "Colegio La Salle", "Colegio Sin Datos"]

    g1 = _group(data, "Colegio Cervantes")
    g2 = _group(data, "Colegio La Salle")
    g3 = _group(data, "Colegio Sin Datos")

    assert g1["results_count"] == 9
    assert g1["students_count"] == 8
    assert g1["mean_ppm"] == pytest.approx(155.56, abs=0.01)
    assert g1["mean_accuracy"] == pytest.approx(64.72, abs=0.01)

    assert g2["results_count"] == 2
    assert g2["students_count"] == 2
    assert g2["mean_ppm"] == pytest.approx(165.0, abs=0.01)
    assert g2["mean_accuracy"] == pytest.approx(76.25, abs=0.01)

    assert g3["has_data"] is False
    assert g3["students_count"] == 0
    assert g3["results_count"] == 0
    assert g3["mean_ppm"] is None
    assert g3["mean_accuracy"] is None


# --------------------------------------------------------------------------- 5

def test_scenario_5_grupo_sin_datos_no_representado_como_cero(client, setup_data):
    sec_empty = setup_data["sections"][2]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec_empty.id))],
    )
    assert resp.status_code == 200
    group = _group(resp.get_json(), "1º ESO C")

    assert group is not None
    assert group["has_data"] is False
    assert group["students_count"] == 0
    assert group["results_count"] == 0
    # Nunca un cero: sin datos = sin media
    assert group["mean_ppm"] is None
    assert group["mean_accuracy"] is None
    assert group["mean_vef"] is None
    assert group["is_representative"] is False
    assert "sin resultados" in group["warning"]


# --------------------------------------------------------------------------- 6

def test_scenario_6_tutor_denegado_en_comparativa_entre_centros(client, setup_data):
    _get_dev_session(client, "tutor", sections=[])

    resp = client.get("/api/v1/comparison/groups", query_string={"group_by": "center"})
    assert resp.status_code == 403


def test_scenario_6_coordinador_puede_comparar_centros(client, setup_data):
    _get_dev_session(client, "coordinator")

    resp = client.get("/api/v1/comparison/groups", query_string={"group_by": "center"})
    assert resp.status_code == 200


def test_tutor_fuera_de_sus_secciones_recibe_403(client, setup_data):
    sec1, sec2 = setup_data["sections"][0], setup_data["sections"][1]

    # Tutor con solo sec1 intenta comparar con sec2
    _get_dev_session(client, "tutor", sections=[str(sec1.id)])

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec1.id)),
                      ("section_ids", str(sec2.id))],
    )
    assert resp.status_code == 403


def test_tutor_en_sus_secciones_puede_comparar(client, setup_data):
    sec1 = setup_data["sections"][0]

    _get_dev_session(client, "tutor", sections=[str(sec1.id)])

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(sec1.id))],
    )
    assert resp.status_code == 200
    assert _group(resp.get_json(), "1º ESO A")["results_count"] == 6


# --------------------------------------------------------------------------- extras

def test_perfil_agrupa_por_sector(client, setup_data):
    sec1 = setup_data["sections"][0]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "profile"), ("section_ids", str(sec1.id))],
    )
    assert resp.status_code == 200
    data = resp.get_json()

    funcional = _group(data, "Funcional")
    literario = _group(data, "Literario")

    assert funcional is not None
    assert literario is not None
    assert funcional["students_count"] == 4
    assert funcional["results_count"] == 4
    assert funcional["mean_ppm"] == pytest.approx(162.5, abs=0.01)
    assert funcional["mean_accuracy"] == pytest.approx(67.5, abs=0.01)

    assert literario["students_count"] == 2
    assert literario["results_count"] == 2
    assert literario["is_representative"] is False


def test_rango_de_fechas_acota_los_resultados(client, setup_data):
    sec2 = setup_data["sections"][1]

    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[
            ("group_by", "section"),
            ("section_ids", str(sec2.id)),
            ("start_date", "2025-11-01"),
        ],
    )
    assert resp.status_code == 200
    group = _group(resp.get_json(), "1º ESO B")
    # Solo queda el resultado de 2025-12-15
    assert group["results_count"] == 1
    assert group["students_count"] == 1
    assert group["mean_ppm"] == pytest.approx(90.0, abs=0.01)


def test_group_by_invalido_devuelve_422(client, setup_data):
    _get_dev_session(client, "coordinator")

    resp = client.get("/api/v1/comparison/groups", query_string={"group_by": "aula"})
    assert resp.status_code == 422


def test_falta_group_by_devuelve_422(client, setup_data):
    _get_dev_session(client, "coordinator")

    resp = client.get("/api/v1/comparison/groups")
    assert resp.status_code == 422


def test_seccion_inexistente_devuelve_404(client, setup_data):
    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section"), ("section_ids", str(uuid.uuid4()))],
    )
    assert resp.status_code == 404


def test_centro_inexistente_devuelve_404(client, setup_data):
    _get_dev_session(client, "coordinator")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string={"group_by": "center", "center_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404


def test_rol_pendiente_recibe_403(client, setup_data):
    _get_dev_session(client, "pendiente")

    resp = client.get(
        "/api/v1/comparison/groups",
        query_string=[("group_by", "section")],
    )
    assert resp.status_code == 403


def test_sin_sesion_devuelve_401(setup_data):
    app = create_app(NoBypassConfig)
    unauth_client = app.test_client()

    resp = unauth_client.get(
        "/api/v1/comparison/groups", query_string={"group_by": "section"}
    )
    assert resp.status_code == 401


def test_auditoria_registra_comparativa(client, setup_data):
    clear_audit_logs()

    _get_dev_session(client, "coordinator")

    resp = client.get("/api/v1/comparison/groups", query_string={"group_by": "center"})
    assert resp.status_code == 200

    logs = [l for l in get_audit_logs() if l["action"] == "GENERATE_GROUP_COMPARISON"]
    assert len(logs) == 1

    entry = logs[0]
    assert entry["resource_type"] == "comparison"
    assert entry["resource_id"] == "center"
    assert entry["details"]["group_by"] == "center"
    assert entry["details"]["groups_count"] == 3
    assert entry["details"]["min_sample"] == 5