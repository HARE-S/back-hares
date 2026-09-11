"""Informe de errores de importación (BE-08).

El administrador descarga la lista de filas rechazadas en la última
importación de alumnado como CSV. La descarga queda registrada en
auditoría (Nota de Seguridad de BE-08).
"""
import csv
import io
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlalchemy import select

from app.auth.decorators import get_current_user, require_role
from app.core.audit import log_audit
from app.extensions import db
from app.models.import_report import ImportReport

import_bp = Blueprint("import_v1", __name__)

CSV_FILENAME = "informe_errores_importacion.csv"


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