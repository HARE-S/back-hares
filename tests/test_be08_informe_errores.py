"""BE-08: Informe de errores de importación — escenarios 1 a 4.

Cubrimos la tolerancia a filas inválidas (la importación no se detiene),
el detalle de cada error (línea, columna, motivo), los cuatro casos del
escenario 3 con motivo específico, y la descarga del informe por el
administrador con registro en auditoría.
"""
from pathlib import Path

import pytest

from app.core.audit import clear_audit_logs, get_audit_logs
from app.extensions import db
from app.importer import StudentImporter, parse_students_csv_collect
from app.models.import_report import ImportReport
from app.repositories.student_repository import StudentRepository


def _csv_with_all_valid_rows(n: int) -> str:
    lines = ["student_id;student_name;sections;center"]
    for i in range(1, n + 1):
        lines.append(f"STU{i:03d};Alumno {i};1CARMED2;Peñascal")
    return "\n".join(lines)


def _make_bad_row_csv(reason: str) -> str:
    header = "student_id;student_name;sections;center\n"
    rows = {
        "empty_external_id": "X1;Alumno;1CARMED2;Peñascal\n;Sin id;1CARMED2;Peñascal\nX2;Otro;1CARMED2;Peñascal\n",
        "empty_center": "X1;Alumno;1CARMED2;Peñascal\nX2;Sin centro;1CARMED2;\nX3;Otro;1CARMED2;Peñascal\n",
        "malformed_sections": "X1;Alumno;1CARMED2;Peñascal\nX2;Sections vacío;;Peñascal\nX3;Otro;1CARMED2;Peñascal\n",
        "too_few_columns": "X1;Alumno;1CARMED2;Peñascal\nX2;Faltan columnas;Peñascal\nX3;Otro;1CARMED2;Peñascal\n",
        "too_many_columns": "X1;Alumno;1CARMED2;Peñascal\nX2;Columnas extra;1CARMED2;Peñascal;EXTRA\nX3;Otro;1CARMED2;Peñascal\n",
    }
    return header + rows[reason]


def _import_content(content: str, commit: bool = True):
    return StudentImporter(db.session).import_from_csv(content, commit=commit)


def test_scenario_1_invalid_row_does_not_stop_the_process(app):
    """Escenario 1: la fila inválida se registra y las demás se procesan.

    Dado un fichero de 28 filas donde la número 12 es inválida
    Cuando se ejecuta la importación
    Entonces se procesan las 27 filas válidas
    Y la fila 12 se registra como error
    Y el resumen indica 27 procesadas y 1 con error
    """
    with app.app_context():
        content_lines = _csv_with_all_valid_rows(28).splitlines()
        content_lines[12] = ";;;"
        content = "\n".join(content_lines)

        summary = _import_content(content)

        assert summary["errors"] == 1
        assert summary["processed"] == 27
        assert summary["total"] == 28
        assert summary["error_details"][0]["line"] == 13

        repo = StudentRepository(db.session)
        assert repo.count_students() == 27


def test_scenario_2_error_detail_has_line_column_and_reason(app):
    """Escenario 2: cada error indica línea, columna y motivo comprensible.

    Dado una fila rechazada
    Cuando se consulta el informe de errores
    Entonces cada error indica el número de línea
    Y la columna afectada
    Y el motivo del rechazo en lenguaje comprensible
    """
    with app.app_context():
        summary = _import_content(_make_bad_row_csv("empty_external_id"))

        error = summary["error_details"][0]
        assert error["line"] == 3
        assert error["column"] == "student_id"
        assert "no puede estar vacío" in error["reason"]


@pytest.mark.parametrize(
    "case,expected_column,fragment",
    [
        ("empty_external_id", "student_id", "no puede estar vacío"),
        ("empty_center", "center", "no puede estar vacío"),
        ("malformed_sections", "sections", "al menos una sección"),
        ("too_few_columns", None, "columnas"),
        ("too_many_columns", None, "columnas"),
    ],
)
def test_scenario_3_specific_reason_for_each_case(app, case, expected_column, fragment):
    """Escenario 3: cada caso se rechaza con su motivo específico.

    Dado filas con external_id vacío, centro vacío, secciones malformadas
        o un número de columnas distinto al esperado
    Cuando se procesan
    Entonces cada una se rechaza con su motivo específico
    Y ninguna genera un error genérico sin explicación
    """
    with app.app_context():
        rows, errors = parse_students_csv_collect(_make_bad_row_csv(case))
        assert len(rows) == 2
        assert len(errors) == 1

        error = errors[0]
        assert error["column"] == expected_column
        assert fragment.lower() in error["reason"].lower()

        summary = _import_content(_make_bad_row_csv(case))
        assert summary["errors"] == 1
        assert summary["processed"] == 2


def test_scenario_4_admin_downloads_report_csv(app, client):
    """Escenario 4: el administrador descarga el informe en CSV.

    Dado una importación terminada con errores
    Cuando el administrador solicita el informe
    Entonces se descarga un fichero con la lista de errores
    Y la descarga queda registrada en auditoría
    """
    with app.app_context():
        clear_audit_logs()
        _import_content(_make_bad_row_csv("empty_external_id"))

        report = db.session.query(ImportReport).order_by(ImportReport.created_at.desc()).first()
        assert report is not None
        assert report.errors == 1
        assert report.processed == 2
        assert report.error_details[0]["column"] == "student_id"

        client.post("/api/dev/session", json={"role": "admin"})

    resp = client.get("/api/v1/import/report")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "informe_errores_importacion.csv" in resp.headers.get("Content-Disposition", "")

    lines = resp.data.decode("utf-8").splitlines()
    assert lines[0] == "linea;columna;motivo"
    assert "3;student_id;" in lines[1]

    with app.app_context():
        logs = get_audit_logs(resource_type="import_report")
        assert any(log["action"] == "descargar_informe_errores" for log in logs)


def test_non_admin_cannot_download_report(app, client):
    """Solo el administrador puede descargar el informe (Nota de Seguridad).

    Dado un usuario con rol tutor
    Cuando intenta descargar el informe
    Entonces el sistema deniega la operación con 403
    """
    with app.app_context():
        clear_audit_logs()
        _import_content(_make_bad_row_csv("empty_external_id"))

    client.post("/api/dev/session", json={"role": "tutor"})

    resp = client.get("/api/v1/import/report")
    assert resp.status_code == 403

    with app.app_context():
        assert get_audit_logs(resource_type="import_report") == []


def test_report_without_import_returns_404(app, client):
    """Sin importaciones previas no existe informe que descargar (404)."""
    client.post("/api/dev/session", json={"role": "admin"})

    resp = client.get("/api/v1/import/report")
    assert resp.status_code == 404