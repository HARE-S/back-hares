"""Informe de errores de importación (BE-08) y subida de fichero (BE-09).

BE-08: el administrador descarga la lista de filas rechazadas en la última
importación de alumnado como CSV. La descarga queda registrada en auditoría.

BE-09: el administrador sube el CSV de Alexia desde el navegador, previsualiza
las primeras filas sin escribir en base de datos, y confirma la importación
reutilizando exactamente el mismo parser/loader del importador por CLI.
"""
import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from app.auth.decorators import get_current_user, require_role
from app.core.audit import log_audit
from app.core.exceptions import ValidationError
from app.core.upload_store import upload_store
from app.extensions import db
from app.importer import StudentImporter, parse_students_csv_collect
from app.models.import_report import ImportReport

import_bp = Blueprint("import_v1", __name__)

CSV_FILENAME = "informe_errores_importacion.csv"
PREVIEW_MAX_ROWS = 5
ERROR_DETAILS_MAX = 5


def _csv_from_report(report: ImportReport) -> "flask.wrappers.Response":
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["linea", "columna", "motivo"])
    for detail in report.error_details or []:
        writer.writerow([
            detail.get("line", ""),
            detail.get("column", "") or "",
            detail.get("reason", ""),
        ])

    from flask import Response

    return Response(
        output.getvalue(),
        status=200,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{CSV_FILENAME}"',
        },
    )


@import_bp.route("/report")
@require_role("admin")
def get_import_report():
    """Descarga el informe de errores de la última importación (BE-08).

    - 200 con el informe en CSV si existe alguna importación previa.
    - 404 si todavía no se ha importado ningún fichero.
    """
    stmt = (
        select(ImportReport)
        .order_by(ImportReport.created_at.desc(), ImportReport.id.desc())
        .limit(1)
    )
    report = db.session.scalars(stmt).first()

    if report is None:
        return (
            jsonify({"error": "No existe ningún informe de importación todavía"}),
            404,
        )

    log_audit(
        get_current_user(),
        action="descargar_informe_errores",
        resource_type="import_report",
        resource_id=report.id,
        details={
            "total": report.total,
            "processed": report.processed,
            "errors": report.errors,
            "queried_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return _csv_from_report(report)


@import_bp.route("/upload", methods=["POST"])
@require_role("admin")
def upload_import_file():
    """Subida y previsualización del CSV de Alexia (BE-09 Escenarios 1, 3 y 4).

    - 200 con token, previsualización y recuentos; NO escribe en la BD.
    - 400 si falta el fichero, la extensión no es válida, supera el tamaño
      máximo, no es UTF-8 o el CSV no tiene la cabecera esperada.
    """
    current_user = get_current_user()

    allowed_extensions = set(
        current_app.config.get("IMPORT_ALLOWED_EXTENSIONS", {".csv"})
    )
    max_bytes = int(current_app.config.get("IMPORT_UPLOAD_MAX_BYTES", 0) or 0)

    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "El campo 'file' es obligatorio"}), 400

    extension = Path(file.filename).suffix.lower()
    if extension not in allowed_extensions:
        return (
            jsonify(
                {
                    "error": (
                        "Extensión no permitida. Extensiones válidas: "
                        + ", ".join(sorted(allowed_extensions))
                    )
                }
            ),
            400,
        )

    if max_bytes > 0:
        raw = file.stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return (
                jsonify(
                    {
                        "error": (
                            "El fichero supera el tamaño máximo permitido "
                            f"({max_bytes} bytes)"
                        )
                    }
                ),
                400,
            )
    else:
        raw = file.stream.read()

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "El fichero debe estar codificado en UTF-8"}), 400

    try:
        rows, errors = parse_students_csv_collect(content)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    token = upload_store.put(file.filename, content)

    preview = [
        {
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "sections": row["sections"],
            "center": row["center"],
        }
        for row in rows[:PREVIEW_MAX_ROWS]
    ]

    log_audit(
        current_user,
        action="subir_fichero_importacion",
        resource_type="import",
        resource_id=token,
        details={
            "filename": file.filename,
            "total_rows": len(rows) + len(errors),
            "errors": len(errors),
        },
    )

    return (
        jsonify(
            {
                "token": token,
                "filename": file.filename,
                "preview": preview,
                "total_rows": len(rows) + len(errors),
                "errors": len(errors),
                "error_details": errors[:ERROR_DETAILS_MAX],
                "allowed_extensions": sorted(allowed_extensions),
                "max_bytes": max_bytes,
            }
        ),
        200,
    )


@import_bp.route("/confirm", methods=["POST"])
@require_role("admin")
def confirm_import():
    """Confirmación de la importación del fichero subido (BE-09 Escenario 2).

    - 200 con el resumen de ejecución, idéntico al del importador por CLI.
    - 400 si falta el token; 404 si no existe o ha caducado.
    - 500 si falla la escritura (el fichero se conserva para reintentar).
    """
    current_user = get_current_user()

    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "El campo 'token' es obligatorio"}), 400

    entry = upload_store.get(token)
    if entry is None:
        return jsonify({"error": "El fichero subido no existe o ha caducado"}), 404

    try:
        summary = StudentImporter(db.session, current_user=get_current_user()).import_from_csv(
            entry["content"], commit=True
        )
    except Exception as exc:  # noqa: BLE001 - se conserva el fichero para reintentar
        db.session.rollback()
        return jsonify({"error": f"Error durante la importación: {exc}"}), 500

    upload_store.delete(token)

    report = (
        db.session.scalars(
            select(ImportReport)
            .order_by(ImportReport.created_at.desc(), ImportReport.id.desc())
            .limit(1)
        ).first()
    )

    log_audit(
        current_user,
        action="importar_alumnado",
        resource_type="import_report",
        resource_id=report.id if report else token,
        details={
            "filename": entry["filename"],
            "total": summary["total"],
            "processed": summary["processed"],
            "errors": summary["errors"],
            "students_created": summary["students_created"],
            "students_updated": summary["students_updated"],
        },
    )

    return (
        jsonify(
            {
                "message": "Importación completada",
                "report_id": str(report.id) if report else None,
                "summary": summary,
            }
        ),
        200,
    )