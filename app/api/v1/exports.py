from flask import Blueprint, jsonify, request, send_file
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, ValidationError
from app.extensions import db
from app.services.export_service import ExportService

exports_bp = Blueprint("exports_v1", __name__)


@exports_bp.route("/results/export/excel", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def export_results_excel():
    """
    Descarga de resultados en formato Excel (.xlsx) con filtros aplicados (BE-35).
    - 200 OK con el archivo binario descargable y cabeceras legibles en castellano.
    - Soporta filtros por section_id, student_id, test_id, start_date, end_date y academic_year.
    - 400 Bad Request si algún identificador o fecha no es válido.
    - 403 Forbidden si el rol es 'pendiente' o el tutor filtra por una sección no asignada.
    - 401 Unauthorized si la petición no está autenticada.
    """
    current_user = get_current_user()
    service = ExportService(db.session)

    filters = {
        "section_id": request.args.get("section_id"),
        "student_id": request.args.get("student_id"),
        "test_id": request.args.get("test_id"),
        "start_date": request.args.get("start_date") or request.args.get("from_date"),
        "end_date": request.args.get("end_date") or request.args.get("to_date"),
        "academic_year": request.args.get("academic_year"),
    }

    # Limpiar filtros nulos o vacíos
    clean_filters = {k: v for k, v in filters.items() if v is not None and str(v).strip() != ""}

    try:
        excel_buffer = service.export_results_to_excel(
            filters=clean_filters,
            current_user=current_user,
        )
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="resultados_lectura.xlsx",
    )
