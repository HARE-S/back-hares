import uuid
from flask import Blueprint, jsonify, request
from app.core.decorators import require_role
from app.core.exceptions import (
    DuplicateCodeError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.services.catalog_service import CatalogService

books_bp = Blueprint("books_v1", __name__)


def _parse_uuid(value: str):
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError):
        return None


@books_bp.route("", methods=["GET"])
def list_books():
    """
    Listado del catálogo de libros (BE-15 y BE-16).
    Acepta query parameters:
      - include_disabled: bool (por defecto false)
      - level: str (ej: '0', '0-I', 'I', 'I/II', 'II')
      - order_by_level: bool (por defecto false)
    """
    include_disabled_raw = request.args.get("include_disabled", "false")
    include_disabled = include_disabled_raw.lower() in ("true", "1", "yes")

    order_by_level_raw = request.args.get("order_by_level", "false")
    order_by_level = order_by_level_raw.lower() in ("true", "1", "yes")

    level = request.args.get("level")

    service = CatalogService(db.session)
    try:
        books = service.list_books(
            level=level,
            order_by_level=order_by_level,
            include_disabled=include_disabled,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify([b.to_dict() for b in books]), 200


@books_bp.route("", methods=["POST"])
@require_role("coordinator", "admin")
def create_book():
    """
    Alta de libro en el catálogo (BE-16 Escenario 1 y 2).
    Requiere rol coordinator o admin.
    - 201 Created si es exitoso.
    - 409 Conflict si el título ya existe.
    - 422 Unprocessable Entity si faltan datos o el nivel no es válido (BE-15).
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            422,
        )

    service = CatalogService(db.session)
    try:
        new_book = service.create_book(data)
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 422
    except DuplicateCodeError as e:
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    return jsonify(new_book.to_dict()), 201


@books_bp.route("/<book_id>", methods=["GET"])
def get_book(book_id):
    """
    Consulta detallada de un libro por su ID (BE-16 Escenario 3).
    - 200 OK con los datos del libro.
    - 404 Not Found si no existe.
    """
    parsed_id = _parse_uuid(book_id)
    if not parsed_id:
        return jsonify({"error": "Libro no encontrado"}), 404

    service = CatalogService(db.session)
    book = service.get_book(parsed_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    return jsonify(book.to_dict()), 200


@books_bp.route("/<book_id>", methods=["PUT"])
@require_role("coordinator", "admin")
def update_book_put(book_id):
    """
    Reemplazo completo de un libro existente (BE-16 Escenario 3).
    - 200 OK si es exitoso.
    - 422 Unprocessable Entity si faltan campos o el nivel es inválido.
    - 409 Conflict si el título colisiona con otro libro.
    - 404 Not Found si el libro no existe.
    """
    parsed_id = _parse_uuid(book_id)
    if not parsed_id:
        return jsonify({"error": "Libro no encontrado"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            422,
        )

    service = CatalogService(db.session)
    try:
        updated = service.update_book(parsed_id, data, is_patch=False)
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 422
    except DuplicateCodeError as e:
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    if not updated:
        return jsonify({"error": "Libro no encontrado"}), 404

    return jsonify(updated.to_dict()), 200


@books_bp.route("/<book_id>", methods=["PATCH"])
@require_role("coordinator", "admin")
def update_book_patch(book_id):
    """
    Modificación parcial de un libro existente (BE-16 Escenario 3).
    - 200 OK si es exitoso.
    - 422 Unprocessable Entity si los datos no son válidos (ej: nivel no permitido).
    - 409 Conflict si el título colisiona con otro libro.
    - 404 Not Found si el libro no existe.
    """
    parsed_id = _parse_uuid(book_id)
    if not parsed_id:
        return jsonify({"error": "Libro no encontrado"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            422,
        )

    service = CatalogService(db.session)
    try:
        updated = service.update_book(parsed_id, data, is_patch=True)
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 422
    except DuplicateCodeError as e:
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    if not updated:
        return jsonify({"error": "Libro no encontrado"}), 404

    return jsonify(updated.to_dict()), 200


@books_bp.route("/<book_id>", methods=["DELETE"])
@require_role("coordinator", "admin")
def delete_book(book_id):
    """
    Baja lógica de un libro (BE-04 y BE-16 Escenario 4).
    Establece disabled_at con la fecha actual y devuelve 204 No Content.
    Si el libro no existe, devuelve 404 Not Found.
    Las lecturas registradas en readed_books no son eliminadas.
    """
    parsed_id = _parse_uuid(book_id)
    if not parsed_id:
        return jsonify({"error": "Libro no encontrado"}), 404

    service = CatalogService(db.session)
    deleted = service.soft_delete_book(parsed_id)

    if not deleted:
        return jsonify({"error": "Libro no encontrado"}), 404

    return "", 204

