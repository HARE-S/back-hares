from flask import Blueprint, jsonify, request, send_file
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.services.group_report_service import GroupReportService

centers_bp = Blueprint("centers_v1", __name__)


@centers_bp.route("/<center_id>/report", methods=["GET"])
@require_role("coordinator", "coordinador", "admin")
def get_center_report(center_id):
    """
    Informe agregado de un centro completo (BE-37).
    - Devuelve datos agregados globales del centro y el desglose por sección (Escenario 3).
    - Incluye distribución de resultados por tramos y estadísticos (Escenario 2).
    - Indica ausencia de datos si no hay resultados registrados (Escenario 4).
    - Si ?format=excel, devuelve archivo .xlsx descargable con desglose (Escenario 5).
    - 403 Forbidden si lo solicita un tutor o usuario con rol no autorizado (Escenario 6).
    """
    format_arg = request.args.get("format") or request.args.get("export")
    academic_year = request.args.get("academic_year")

    current_user = get_current_user()
    service = GroupReportService(db.session)

    try:
        report = service.get_center_report(
            center_id=center_id,
            current_user=current_user,
            academic_year=academic_year,
            format=format_arg,
        )
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    if format_arg and str(format_arg).strip().lower() in ("excel", "xlsx"):
        return send_file(
            report,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"informe_centro_{center_id}.xlsx",
        )

    return jsonify(report), 200


@centers_bp.route("/<center_id>/report/export", methods=["GET"])
@require_role("coordinator", "coordinador", "admin")
def export_center_report(center_id):
    """
    Descarga directa en Excel del informe agregado de un centro con desglose por sección (BE-37 / Escenario 5).
    """
    academic_year = request.args.get("academic_year")
    current_user = get_current_user()
    service = GroupReportService(db.session)

    try:
        excel_buffer = service.get_center_report(
            center_id=center_id,
            current_user=current_user,
            academic_year=academic_year,
            format="excel",
        )
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"informe_centro_{center_id}.xlsx",
    )
