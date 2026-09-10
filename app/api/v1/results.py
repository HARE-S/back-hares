from flask import Blueprint, jsonify, request
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import (
    BatchValidationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.services.result_service import ResultService

results_bp = Blueprint("results_v1", __name__)
single_results_bp = Blueprint("single_results_v1", __name__)


@results_bp.route("/<student_id>/results", methods=["POST"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def register_student_result(student_id):
    """
    Registra el resultado de una prueba para un alumno (BE-18).
    - 201 Created con el recurso completo y PPM calculado (Escenario 1).
    - 400 Bad Request si los datos son inválidos, negativos o no existen referencias (Escenarios 2 y 3).
    - 401 Unauthorized si no hay sesión (Escenario 5, gestionado por @require_role).
    - 403 Forbidden si el tutor no tiene permiso sobre la sección o rol 'pendiente' (Escenarios 6 y 7).
    - 409 Conflict si el alumno ya tiene un resultado para la misma prueba y fecha (Escenario 4).
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        result_data = service.register_result(
            student_id=student_id,
            data=data,
            current_user=current_user,
        )
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(result_data), 201


@results_bp.route("/<student_id>/results", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_results(student_id):
    """
    Consulta el histórico ordenado de resultados de un alumno (BE-19 Escenario 4 y BE-20).
    - Devuelve 200 OK con la lista ordenada por test_date ascendente.
    - Cada resultado incluye PPM y porcentaje de aciertos (accuracy).
    - 400 Bad Request si el ID es inválido.
    - 404 Not Found si el alumno no existe.
    - 401 Unauthorized si no hay sesión autenticada.
    - 403 Forbidden si el tutor no tiene permisos sobre el alumno o rol 'pendiente'.
    """
    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        history = service.get_student_history(
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

    return jsonify(history), 200


@single_results_bp.route("/<result_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_result(result_id):
    """
    Modificación parcial de un resultado existente (BE-21 Escenario 1).
    - 200 OK con el resultado actualizado y PPM recalculado.
    - 422 Unprocessable Entity si los datos no son válidos (Escenario 2).
    - 404 Not Found si el resultado no existe (Escenario 4).
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno (Escenario 5).
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "UNPROCESSABLE_ENTITY", "message": "Cuerpo de la petición inválido o ausente"}),
            422,
        )

    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        updated = service.update_result(
            result_id=result_id,
            data=data,
            current_user=current_user,
        )
    except SchemaValidationError as e:
        return jsonify({"error": "UNPROCESSABLE_ENTITY", "message": str(e)}), 422
    except ValidationError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(updated), 200


@single_results_bp.route("/<result_id>", methods=["DELETE"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def delete_result(result_id):
    """
    Anulación y borrado físico de un resultado (BE-21 Escenario 3).
    - 204 No Content si se elimina con éxito.
    - 404 Not Found si el resultado no existe (Escenario 4).
    - 403 Forbidden si el tutor no tiene permiso (Escenario 5).
    """
    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        service.delete_result(
            result_id=result_id,
            current_user=current_user,
        )
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return "", 204


@results_bp.route("/<student_id>/results/<result_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_student_result(student_id, result_id):
    """Alias para actualización bajo la ruta /api/students/<student_id>/results/<result_id>."""
    return update_result(result_id)


@results_bp.route("/<student_id>/results/<result_id>", methods=["DELETE"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def delete_student_result(student_id, result_id):
    """Alias para borrado bajo la ruta /api/students/<student_id>/results/<result_id>."""
    return delete_result(result_id)


@single_results_bp.route("/batch", methods=["POST"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def register_batch_results():
    """
    Registra un lote de resultados de pruebas para una sección (BE-22).
    - 201 Created con el resumen de lo registrado y PPM calculado (Escenario 1).
    - Omite automáticamente alumnos ausentes (Escenario 2).
    - 400 Bad Request con 'errors' detallando fila, campo y mensaje si alguna fila es inválida (Escenario 3).
    - Garantiza atomicidad total: ante cualquier error no se persiste nada (Escenario 4).
    - 400 Bad Request identificando el conflicto si un alumno ya tiene resultado en la fecha (Escenario 5).
    - 403 Forbidden si el tutor no tiene asignada la sección o rol 'pendiente' (Escenario 6).
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        summary = service.register_batch(
            data=data,
            current_user=current_user,
        )
    except BatchValidationError as e:
        return jsonify({
            "error": "BATCH_VALIDATION_ERROR",
            "message": e.message,
            "errors": e.errors,
        }), 400
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(summary), 201




