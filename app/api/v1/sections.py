from flask import Blueprint, jsonify, request
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.services.result_service import ResultService

sections_bp = Blueprint("sections_v1", __name__)


@sections_bp.route("/<section_id>/results", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_section_results(section_id):
    """
    Consulta el historial de pruebas de una sección (BE-51).
    - 200 OK con la lista de resultados y metadatos de alumno y prueba (Escenario 1).
    - Soporta agrupación por prueba con query param ?group_by=test (Escenario 2).
    - Soporta acotación por rango de fechas ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (Escenario 3).
    - Preserva fidelidad de resultados de alumnos que cambiaron de grupo (Escenario 4).
    - Devuelve 200 OK con lista vacía si la sección no tiene resultados registrados (Escenario 5).
    - Devuelve 404 Not Found si la sección no existe (Escenario 5).
    - Devuelve 403 Forbidden si el tutor no tiene asignada la sección o rol 'pendiente' (Escenario 6).
    - Devuelve 401 Unauthorized si la petición no está autenticada.
    """
    group_by = request.args.get("group_by")
    start_date = request.args.get("start_date") or request.args.get("from_date")
    end_date = request.args.get("end_date") or request.args.get("to_date")

    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        history = service.get_section_history(
            section_id=section_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            current_user=current_user,
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

    return jsonify(history), 200
