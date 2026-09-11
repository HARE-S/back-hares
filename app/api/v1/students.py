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
