"""BE-09: Endpoint de subida de fichero — escenarios 1 a 5.

Cubre la subida con previsualización sin escritura en BD, la confirmación que
reutiliza el importador de BE-06/BE-07, el rechazo por extensión no permitida
(Escenario 3), el rechazo por tamaño máximo (Escenario 4) y la restricción por
rol (Escenario 5), además de robustez (token inválido, UTF-8, cabecera rota).
"""
import io

import pytest

from app.core.audit import clear_audit_logs, get_audit_logs
from app.core.upload_store import upload_store
from app.extensions import db
from app.models.import_report import ImportReport
from app.repositories.student_repository import StudentRepository


@pytest.fixture(autouse=True)
def _clean_state(app):
    """Aísla el depósito en memoria y la auditoría entre tests."""
    clear_audit_logs()
    yield
    upload_store.clear()


def _csv_body(n: int = 3) -> str:
    lines = ["student_id;student_name;sections;center"]
    for i in range(1, n + 1):
        lines.append(f"X{i:03d};Alumno {i};1A;Peñascal")
    return "\n".join(lines)


def _login(client, role: str = "admin") -> None:
    client.post("/api/dev/session", json={"role": role})


def _upload(client, content: str, filename: str = "alexia.csv"):
    return client.post(
        "/api/v1/import/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), filename)},
        content_type="multipart/form-data",
    )


def _upload_bytes(client, raw: bytes, filename: str = "alexia.csv"):
    return client.post(
        "/api/v1/import/upload",
        data={"file": (io.BytesIO(raw), filename)},
        content_type="multipart/form-data",
    )


def test_scenario_1_upload_previews_without_writing(app, client):
    """Escenario 1: Subida y previsualización.

    Dado un administrador con sesión activa
    Cuando sube un CSV válido
    Entonces el sistema devuelve una previsualización de las primeras filas
    Y no ha escrito todavía nada en la base de datos
    """
    _login(client, "admin")

    resp = _upload(client, _csv_body(3))
    assert resp.status_code == 200

    body = resp.get_json()
    assert body["token"]
    assert body["filename"] == "alexia.csv"
    assert body["total_rows"] == 3
    assert body["errors"] == 0
    assert body["allowed_extensions"] == [".csv"]

    preview = body["preview"]
    assert len(preview) == 3
    assert preview[0] == {
        "student_id": "X001",
        "student_name": "Alumno 1",
        "sections": ["1A"],
        "center": "Peñascal",
    }

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0
        assert db.session.query(ImportReport).count() == 0

    with app.app_context():
        assert get_audit_logs(resource_type="import")
        assert any(
            log["action"] == "subir_fichero_importacion"
            for log in get_audit_logs(resource_type="import")
        )


def test_scenario_1_preview_is_capped_to_five_rows(app, client):
    """La previsualización devuelve como máximo las primeras 5 filas."""
    _login(client, "admin")

    resp = _upload(client, _csv_body(9))
    assert resp.status_code == 200
    body = resp.get_json()

    assert body["total_rows"] == 9
    assert len(body["preview"]) == 5
    assert body["preview"][0]["student_id"] == "X001"


def test_scenario_2_confirm_runs_import_and_returns_summary(app, client):
    """Escenario 2: Confirmación de la importación.

    Dado un fichero ya subido y previsualizado
    Cuando el administrador confirma la importación
    Entonces se ejecuta el proceso de BE-06 y BE-07
    Y se devuelve el resumen de la ejecución
    """
    _login(client, "admin")
    token = _upload(client, _csv_body(3)).get_json()["token"]

    resp = client.post("/api/v1/import/confirm", json={"token": token})
    assert resp.status_code == 200

    body = resp.get_json()
    assert body["message"] == "Importación completada"
    summary = body["summary"]
    assert summary["total"] == 3
    assert summary["processed"] == 3
    assert summary["errors"] == 0
    assert summary["students_created"] == 3
    assert summary["centers_created"] == 1
    assert summary["sections_created"] == 1
    assert summary["enrollments_created"] == 3

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 3
        assert db.session.query(ImportReport).count() == 1

    with app.app_context():
        logs = get_audit_logs(resource_type="import_report")
        assert any(log["action"] == "importar_alumnado" for log in logs)


def test_scenario_2_confirm_is_idempotent_via_token_consumption(app, client):
    """Un mismo fichero solo se puede confirmar una vez.

    Dado un fichero subido y confirmado
    Cuando se vuelve a confirmar el mismo token
    Entonces el sistema lo rechaza con 404
    Y no duplica alumnado
    """
    _login(client, "admin")
    token = _upload(client, _csv_body(3)).get_json()["token"]

    first = client.post("/api/v1/import/confirm", json={"token": token})
    assert first.status_code == 200

    second = client.post("/api/v1/import/confirm", json={"token": token})
    assert second.status_code == 404

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 3


def test_scenario_3_extension_not_allowed_returns_400(app, client):
    """Escenario 3: Extensión no permitida.

    Dado un fichero con una extensión distinta a las permitidas
    Cuando se intenta subir
    Entonces el sistema lo rechaza
    Y devuelve 400 Bad Request indicando las extensiones válidas
    """
    _login(client, "admin")

    resp = _upload(client, _csv_body(3), filename="notas.txt")
    assert resp.status_code == 400
    assert ".csv" in resp.get_json()["error"]

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0


def test_scenario_4_file_too_large_returns_400(app, client):
    """Escenario 4: Fichero demasiado grande.

    Dado un fichero que supera el tamaño máximo configurado
    Cuando se intenta subir
    Entonces el sistema lo rechaza con un mensaje claro
    """
    _login(client, "admin")

    max_bytes = app.config["IMPORT_UPLOAD_MAX_BYTES"]
    oversized = (
        "student_id;student_name;sections;center\n"
        f"A1;{'X' * (max_bytes + 1)};1A;Peñascal\n"
    )

    resp = _upload(client, oversized)
    assert resp.status_code == 400
    assert "supera el tamaño máximo" in resp.get_json()["error"]
    assert str(max_bytes) in resp.get_json()["error"]

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0


def test_scenario_5_tutor_is_forbidden(app, client):
    """Escenario 5: Usuario sin permiso.

    Dado un usuario con rol tutor y sesión activa
    Cuando intenta subir un fichero de importación
    Entonces el sistema deniega la operación
    Y devuelve 403 Forbidden
    """
    _login(client, "tutor")

    assert _upload(client, _csv_body(3)).status_code == 403
    confirm = client.post("/api/v1/import/confirm", json={"token": "cualquiera"})
    assert confirm.status_code == 403

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0


def test_upload_without_file_field_returns_400(app, client):
    _login(client, "admin")

    resp = client.post(
        "/api/v1/import/upload",
        data={},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "file" in resp.get_json()["error"]


def test_upload_with_invalid_utf8_returns_400(app, client):
    _login(client, "admin")

    raw = b"student_id;student_name;sections;center\nX1;\xc1\xc1;1A;C\n"
    resp = _upload_bytes(client, raw)
    assert resp.status_code == 400
    assert "UTF-8" in resp.get_json()["error"]

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0


def test_upload_with_broken_header_returns_400(app, client):
    _login(client, "admin")

    resp = _upload(client, "foo;bar\n1;2\n")
    assert resp.status_code == 400
    assert "student_id" in resp.get_json()["error"]

    with app.app_context():
        assert StudentRepository(db.session).count_students() == 0


def test_confirm_with_missing_or_invalid_token(app, client):
    _login(client, "admin")

    missing = client.post("/api/v1/import/confirm", json={})
    assert missing.status_code == 400

    unknown = client.post("/api/v1/import/confirm", json={"token": "no-existe"})
    assert unknown.status_code == 404