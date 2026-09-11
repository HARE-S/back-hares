from flask import Blueprint, jsonify, request
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.services.student_service import StudentService

students_bp = Blueprint("students_v1", __name__)


@students_bp.route("/<student_id>", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_detail(student_id):
    """
    Consulta la ficha agregada del alumno en una sola petición (BE-28).
    - 200 OK con datos personales, secciones, resultados y lecturas (Escenarios 1, 2, 3 y 4).
    - 400 Bad Request si el UUID no es válido.
    - 404 Not Found si el alumno no existe (Escenario 5).
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 5).
    - 401 Unauthorized si no hay sesión autenticada.
    """
    current_user = get_current_user()
    service = StudentService(db.session)

    try:
        data = service.get_student_detail(
            student_id=student_id,
            current_user=current_user,
        )
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return jsonify(data), 200


@students_bp.route("/<student_id>/report", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_report(student_id):
    """
    Consulta los datos estructurados para el informe individual de un alumno (BE-36).
    - 200 OK con datos personales, secciones, resultados con métricas, lecturas y serie de evolución.
    - Soporta acotación opcional por start_date y end_date.
    - 400 Bad Request si el UUID del alumno no es válido.
    - 404 Not Found si el alumno no existe.
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 4).
    - 401 Unauthorized si la petición no está autenticada.
    """
    current_user = get_current_user()
    service = StudentService(db.session)

    start_date = request.args.get("start_date") or request.args.get("from_date")
    end_date = request.args.get("end_date") or request.args.get("to_date")

    try:
        report_data = service.get_student_report(
            student_id=student_id,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return jsonify(report_data), 200
