from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from app.core.decorators import require_role
from app.core.exceptions import (
    DuplicateCodeError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.services.catalog_service import CatalogService
from app.schemas.book_schema import BookCreateSchema, BookUpdateSchema, BookPutSchema, BookResponseSchema
from app.schemas.common import translate_marshmallow_errors
from marshmallow import ValidationError as MarshmallowValidationError


books_bp = Blueprint("books_v1", __name__, description="Catálogo de libros")


@books_bp.route("")
class BooksList(MethodView):
    def get(self):
        """
        Listado del catálogo de libros (BE-15 y BE-16).
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

    @require_role("coordinator", "admin")
    def post(self):
        """
        Alta de libro en el catálogo (BE-16 Escenario 1 y 2).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 422

        schema = BookCreateSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = translate_marshmallow_errors(e.messages)
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            new_book = service.create_book(payload)
        except SchemaValidationError as e:
            return jsonify({"error": str(e)}), 422
        except DuplicateCodeError as e:
            return jsonify({"error": str(e)}), 409
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422

        return jsonify(new_book.to_dict()), 201


@books_bp.route("/<uuid:book_id>")
class BookById(MethodView):
    @books_bp.response(200, BookResponseSchema)
    def get(self, book_id):
        """
        Consulta detallada de un libro por su ID (BE-16 Escenario 3).
        """
        service = CatalogService(db.session)
        book = service.get_book(book_id)
        if not book:
            return {}, 404

        return book.to_dict(), 200

    @require_role("coordinator", "admin")
    def put(self, book_id):
        """
        Reemplazo completo de un libro existente (BE-16 Escenario 3).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 422

        schema = BookPutSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = translate_marshmallow_errors(e.messages)
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            updated = service.update_book(book_id, payload, is_patch=False)
        except SchemaValidationError as e:
            return jsonify({"error": str(e)}), 422
        except DuplicateCodeError as e:
            return jsonify({"error": str(e)}), 409
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422

        if not updated:
            return jsonify({"error": "Libro no encontrado"}), 404

        return jsonify(updated.to_dict()), 200

    @require_role("coordinator", "admin")
    def patch(self, book_id):
        """
        Modificación parcial de un libro existente (BE-16 Escenario 3).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 422

        schema = BookUpdateSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = "; ".join([f"{k}: {v[0]}" for k, v in e.messages.items()])
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            updated = service.update_book(book_id, payload, is_patch=True)
        except SchemaValidationError as e:
            return jsonify({"error": str(e)}), 422
        except DuplicateCodeError as e:
            return jsonify({"error": str(e)}), 409
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422

        if not updated:
            return jsonify({"error": "Libro no encontrado"}), 404

        return jsonify(updated.to_dict()), 200

    @require_role("coordinator", "admin")
    def delete(self, book_id):
        """
        Baja lógica de un libro (BE-04 y BE-16 Escenario 4).
        """
        service = CatalogService(db.session)
        deleted = service.soft_delete_book(book_id)

        if not deleted:
            return jsonify({"error": "Libro no encontrado"}), 404

        return "", 204


from app.auth.decorators import require_role as auth_require_role


@books_bp.route("/<book_id>/students")
class BookStudents(MethodView):
    @auth_require_role("tutor", "coordinator", "coordinador", "admin")
    def get(self, book_id):
        """
        Consulta la lista de alumnos que han leído un libro con sus fechas de lectura (BE-26 Escenario 2).
        """
        from app.auth.decorators import get_current_user
        from app.core.exceptions import ForbiddenError, NotFoundError
        from app.services.reading_service import ReadingService

        current_user = get_current_user()
        status = request.args.get("status")
        service = ReadingService(db.session)

        try:
            results = service.get_book_students(book_id, status=status, current_user=current_user)
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        except NotFoundError as e:
            return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
        except ForbiddenError as e:
            return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

        return jsonify(results), 200
