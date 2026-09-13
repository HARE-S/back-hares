"""Blueprints de consulta de centros, secciones y alumnado (BE-10).

Recursos de solo lectura: únicamente se exponen GET; cualquier otro
método devuelve 405 Method Not Allowed automáticamente.
"""
from flask import Blueprint, jsonify

from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.services.directory_service import DirectoryService

directory_bp = Blueprint("directory_v1", __name__)


@directory_bp.route("/centers", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def list_centers():
    """
    Listado de centros activos (BE-10, Escenario 1).

    Devuelve 200 OK con la lista de centros no deshabilitados.
    """
    current_user = get_current_user()
    service = DirectoryService(db.session)

    try:
        centers = service.list_centers(current_user=current_user)
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return jsonify(centers), 200


@directory_bp.route("/centers/<center_id>/sections", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_center_sections(center_id):
    """
    Secciones activas de un centro (BE-10, Escenario 2).

    Devuelve 200 OK con las secciones del centro no deshabilitadas.
    Devuelve 404 Not Found si el centro no existe o está deshabilitado.
    """
    current_user = get_current_user()
    service = DirectoryService(db.session)

    try:
        sections = service.get_center_sections(
            center_id=center_id,
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

    return jsonify(sections), 200


@directory_bp.route("/sections/<section_id>/students", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_section_students(section_id):
    """
    Alumnado activo matriculado en una sección (BE-10, Escenario 3).

    Devuelve 200 OK con la lista de alumnos no deshabilitados.
    Devuelve 404 Not Found si la sección no existe o está deshabilitada.
    Devuelve 403 Forbidden si el tutor no tiene asignada la sección o su
    rol es 'pendiente' (Escenario 6).
    """
    current_user = get_current_user()
    service = DirectoryService(db.session)

    try:
        students = service.get_section_students(
            section_id=section_id,
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

    return jsonify(students), 200