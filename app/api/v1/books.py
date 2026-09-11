import uuid
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
from app.schemas.book_schema import BookCreateSchema, BookUpdateSchema, BookResponseSchema
from app.schemas.common import ErrorSchema


books_bp = Blueprint("books_v1", __name__, description="Catálogo de libros")


@books_bp.route("")
class BooksList(MethodView):
    @books_bp.response(200, BookResponseSchema(many=True))
    def get(self):
        """
        Listado del catálogo de libros (BE-15 y BE-16).
        Acepta query parameters:
          - include_disabled: bool (por defecto false)
          - level: str (ej: '0', '0-I', 'I', 'I/II', 'II')
          - order_by_level: bool (por defecto false)
        """
        from flask import request

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
            return {"error": str(e)}, 400

        return [b.to_dict() for b in books], 200

    @require_role("coordinator", "admin")
    @books_bp.arguments(BookCreateSchema)
    @books_bp.response(201, BookResponseSchema)
    @books_bp.alt_response(409, schema=ErrorSchema)
    @books_bp.alt_response(422, schema=ErrorSchema)
    def post(self, payload):
        """
        Alta de libro en el catálogo (BE-16 Escenario 1 y 2).
        Requiere rol coordinator o admin.
        - 201 Created si es exitoso.
        - 409 Conflict si el título ya existe.
        - 422 Unprocessable Entity si faltan datos o el nivel no es válido (BE-15).
        """
        service = CatalogService(db.session)
        try:
            new_book = service.create_book(payload)
        except SchemaValidationError as e:
            return {"error": str(e)}, 422
        except DuplicateCodeError as e:
            return {"error": str(e)}, 409
        except ValidationError as e:
            return {"error": str(e)}, 422

        return new_book.to_dict(), 201


@books_bp.route("/<uuid:book_id>")
class BookById(MethodView):
    @books_bp.response(200, BookResponseSchema)
    @books_bp.alt_response(404, schema=ErrorSchema)
    def get(self, book_id):
        """
        Consulta detallada de un libro por su ID (BE-16 Escenario 3).
        - 200 OK con los datos del libro.
        - 404 Not Found si no existe.
        """
        service = CatalogService(db.session)
        book = service.get_book(book_id)
        if not book:
            return {"error": "Libro no encontrado"}, 404

        return book.to_dict(), 200

    @require_role("coordinator", "admin")
    @books_bp.arguments(BookUpdateSchema)
    @books_bp.response(200, BookResponseSchema)
    @books_bp.alt_response(409, schema=ErrorSchema)
    @books_bp.alt_response(422, schema=ErrorSchema)
    @books_bp.alt_response(404, schema=ErrorSchema)
    def put(self, payload, book_id):
        """
        Reemplazo completo de un libro existente (BE-16 Escenario 3).
        - 200 OK si es exitoso.
        - 422 Unprocessable Entity si faltan campos o el nivel es inválido.
        - 409 Conflict si el título colisiona con otro libro.
        - 404 Not Found si el libro no existe.
        """
        service = CatalogService(db.session)
        try:
            updated = service.update_book(book_id, payload, is_patch=False)
        except SchemaValidationError as e:
            return {"error": str(e)}, 422
        except DuplicateCodeError as e:
            return {"error": str(e)}, 409
        except ValidationError as e:
            return {"error": str(e)}, 422

        if not updated:
            return {"error": "Libro no encontrado"}, 404

        return updated.to_dict(), 200

    @require_role("coordinator", "admin")
    @books_bp.arguments(BookUpdateSchema)
    @books_bp.response(200, BookResponseSchema)
    @books_bp.alt_response(409, schema=ErrorSchema)
    @books_bp.alt_response(422, schema=ErrorSchema)
    @books_bp.alt_response(404, schema=ErrorSchema)
    def patch(self, payload, book_id):
        """
        Modificación parcial de un libro existente (BE-16 Escenario 3).
        - 200 OK si es exitoso.
        - 422 Unprocessable Entity si los datos no son válidos (ej: nivel no permitido).
        - 409 Conflict si el título colisiona con otro libro.
        - 404 Not Found si el libro no existe.
        """
        service = CatalogService(db.session)
        try:
            updated = service.update_book(book_id, payload, is_patch=True)
        except SchemaValidationError as e:
            return {"error": str(e)}, 422
        except DuplicateCodeError as e:
            return {"error": str(e)}, 409
        except ValidationError as e:
            return {"error": str(e)}, 422

        if not updated:
            return {"error": "Libro no encontrado"}, 404

        return updated.to_dict(), 200

    @require_role("coordinator", "admin")
    @books_bp.response(204)
    @books_bp.alt_response(404, schema=ErrorSchema)
    def delete(self, book_id):
        """
        Baja lógica de un libro (BE-04 y BE-16 Escenario 4).
        Establece disabled_at con la fecha actual y devuelve 204 No Content.
        Si el libro no existe, devuelve 404 Not Found.
        Las lecturas registradas en readed_books no son eliminadas.
        """
        service = CatalogService(db.session)
        deleted = service.soft_delete_book(book_id)

        if not deleted:
            return {"error": "Libro no encontrado"}, 404

        return "", 204
