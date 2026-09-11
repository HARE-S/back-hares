from flask import Blueprint, jsonify, request
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.services.reading_service import ReadingService

readings_bp = Blueprint("readings_v1", __name__)
single_readings_bp = Blueprint("single_readings_v1", __name__)


@readings_bp.route("/<student_id>/books", methods=["POST"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def assign_student_book(student_id):
    """
    Asigna un libro a un alumno registrando el inicio de lectura (BE-23).
    - 201 Created con el recurso y estado de lectura (Escenario 1 y 2).
    - 400 Bad Request si el libro no existe o está deshabilitado (Escenarios 3 y 4).
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 5).
    - 404 Not Found si el alumno no existe.
    - 409 Conflict si ya existe lectura idéntica para la misma fecha de inicio.
    - 422 Unprocessable Entity si la fecha de fin es anterior al inicio.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ReadingService(db.session)

    try:
        reading_data = service.assign_book(
            student_id=student_id,
            data=data,
            current_user=current_user,
        )
    except SchemaValidationError as e:
        return jsonify({"error": "UNPROCESSABLE_ENTITY", "message": str(e)}), 422
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(reading_data), 201


@single_readings_bp.route("/<reading_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_reading(reading_id):
    """
    Cierre o reapertura de una lectura de libro (BE-24).
    - 200 OK con status 'finalizada' al fijar end_date (Escenario 1).
    - 422 Unprocessable Entity si end_date < start_date (Escenario 2).
    - 200 OK con status 'en curso' al pasar end_date nulo (reapertura, Escenario 4).
    - 404 Not Found si la lectura no existe (Escenario 5).
    - 403 Forbidden si el tutor no tiene asignada la sección del alumno o rol pendiente.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ReadingService(db.session)

    try:
        reading_data = service.close_or_update_reading(
            reading_id=reading_id,
            data=data,
            current_user=current_user,
        )
    except SchemaValidationError as e:
        return jsonify({"error": "UNPROCESSABLE_ENTITY", "message": str(e)}), 422
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(reading_data), 200


@readings_bp.route("/<student_id>/books/<reading_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_student_reading(student_id, reading_id):
    """Alias anidado para actualización de lectura bajo /api/students/<student_id>/books/<reading_id>."""
    return update_reading(reading_id)


@readings_bp.route("/<student_id>/books", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_books(student_id):
    """
    Consulta el listado de lecturas de un alumno (BE-24 Escenario 3 y BE-26 Escenario 1).
    - 200 OK con la lista de lecturas con estado claramente indicado.
    - Soporta filtro opcional query param ?status=en curso o ?status=finalizada.
    - 404 Not Found si el alumno no existe.
    - 403 Forbidden si el tutor no tiene asignada la sección del alumno o rol pendiente.
    """
    current_user = get_current_user()
    service = ReadingService(db.session)

    status = request.args.get("status")

    try:
        readings = service.get_student_readings(
            student_id=student_id,
            status=status,
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

    return jsonify(readings), 200
