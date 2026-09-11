from pathlib import Path
import uuid
from flask.views import MethodView
from flask_smorest import Blueprint

from app.core.decorators import require_role
from app.core.exceptions import (
    ConflictError,
    DuplicateCodeError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.repositories.test_repository import TestRepository
from app.services.catalog_service import CatalogService
from app.schemas.test_schema import TestCreateSchema, TestUpdateSchema, TestResponseSchema
from app.schemas.common import PaginationQueryArgsSchema, ErrorSchema

tests_bp = Blueprint("tests_v1", __name__, description="Catálogo de pruebas de lectura")


@tests_bp.route("")
class TestsList(MethodView):
    @tests_bp.arguments(PaginationQueryArgsSchema, location="query")
    @tests_bp.response(200, TestResponseSchema(many=True))
    def get(self, query_args):
        """
        Listado paginado y filtrado de pruebas de lectura (BE-14).
        Query parameters:
        - filter / q / search: Búsqueda de texto en nombre y código insensible a acentos (Escenario 2).
        - level: Filtro por nivel (ej: '1') (Escenario 3).
        - type: Filtro por tipo (ej: 'F' o 'L') (Escenario 3).
        - page: Número de página (default 1) (Escenario 1).
        - limit: Elementos por página (default 10) (Escenario 1).
        - include_disabled: bool (default false, excluye pruebas dadas de baja lógica) (Escenario 5).
        """
        from flask import request
        from app.schemas.common import PaginationParams

        filter_text = request.args.get("filter") or request.args.get("q") or request.args.get("search")
        level = request.args.get("level")
        test_type = request.args.get("type")
        include_disabled_raw = request.args.get("include_disabled", "false")
        include_disabled = include_disabled_raw.lower() in ("true", "1", "yes")

        service = CatalogService(db.session)
        response_data = service.list_tests(
            filter_text=filter_text,
            level=level,
            type=test_type,
            page=query_args.get("page", 1),
            limit=query_args.get("limit", 10),
            include_disabled=include_disabled,
        )

        return response_data.get("items", [])

    @require_role("coordinator", "admin")
    @tests_bp.arguments(TestCreateSchema)
    @tests_bp.response(201, TestResponseSchema)
    @tests_bp.alt_response(409, schema=ErrorSchema)
    @tests_bp.alt_response(422, schema=ErrorSchema)
    def post(self, payload):
        """
        Alta de prueba en el catálogo (BE-11).
        Solo permitida para rol coordinator o admin.
        """
        service = CatalogService(db.session)
        try:
            new_test = service.create_test(
                code=payload.get("code"),
                name=payload.get("name"),
                words=payload.get("words"),
                level=payload.get("level"),
                type=payload.get("type"),
            )
        except ValidationError as e:
            return {"error": str(e)}, 422
        except DuplicateCodeError as e:
            return {"error": str(e)}, 409

        return new_test.to_dict(), 201


@tests_bp.route("/import", methods=["POST"])
@require_role("coordinator", "admin")
def import_tests():
    """
    Importación del catálogo de pruebas desde CSV (BE-12).
    Acepta:
    1. Archivo multipart/form-data con clave 'file'.
    2. Texto plano CSV en el cuerpo de la petición (Content-Type: text/csv).
    3. JSON opcional con {"file_path": "..."}.
    4. Sin parámetros: carga por defecto el catálogo semilla 'data/seeds/tests.csv'.
    """
    from flask import request, jsonify

    file_source = None
    if "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            file_source = uploaded_file

    if file_source is None:
        if request.content_type and "text/csv" in request.content_type:
            file_source = request.get_data(as_text=True)
        elif request.is_json:
            json_data = request.get_json(silent=True) or {}
            custom_path = json_data.get("file_path")
            if custom_path:
                file_source = custom_path

    if file_source is None:
        default_path = Path("data/seeds/tests.csv")
        if default_path.is_file():
            file_source = default_path
        else:
            return jsonify({"error": "No se encontró ningún archivo CSV ni la semilla por defecto"}), 400

    service = CatalogService(db.session)
    try:
        result = service.import_tests_from_csv(file_source)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error al procesar la importación: {str(e)}"}), 500

    return jsonify({
        "message": "Catálogo importado correctamente",
        "total": result["total"],
        "created": result["created"],
        "updated": result["updated"],
        "tests": [t.to_dict() for t in result["tests"]],
    }), 200


@tests_bp.route("/<uuid:test_id>")
class TestById(MethodView):
    @require_role("coordinator", "admin")
    @tests_bp.arguments(TestUpdateSchema)
    @tests_bp.response(200, TestResponseSchema)
    @tests_bp.alt_response(409, schema=ErrorSchema)
    @tests_bp.alt_response(422, schema=ErrorSchema)
    @tests_bp.alt_response(404, schema=ErrorSchema)
    def put(self, payload, test_id):
        """
        Reemplazo completo de una prueba existente (BE-13 Escenario 1).
        Devuelve 200 OK con el recurso actualizado.
        Devuelve 422 si los datos son inválidos o faltan campos obligatorios.
        Devuelve 409 si se intenta alterar el código de una prueba con resultados asociados.
        Devuelve 404 si la prueba no existe.
        """
        service = CatalogService(db.session)
        try:
            updated = service.update_test(test_id, payload, is_patch=False)
        except SchemaValidationError as e:
            return {"error": str(e)}, 422
        except (ConflictError, DuplicateCodeError) as e:
            return {"error": str(e)}, 409
        except ValidationError as e:
            return {"error": str(e)}, 422

        if not updated:
            return {"error": "Prueba no encontrada"}, 404

        return updated.to_dict(), 200

    @require_role("coordinator", "admin")
    @tests_bp.arguments(TestUpdateSchema)
    @tests_bp.response(200, TestResponseSchema)
    @tests_bp.alt_response(409, schema=ErrorSchema)
    @tests_bp.alt_response(422, schema=ErrorSchema)
    @tests_bp.alt_response(404, schema=ErrorSchema)
    def patch(self, payload, test_id):
        """
        Modificación parcial de una prueba existente (BE-13 Escenario 2 y 3).
        Devuelve 200 OK con el recurso actualizado.
        Devuelve 422 si los datos no son válidos (ej: words <= 0).
        Devuelve 409 si se intenta alterar el código de una prueba con resultados asociados.
        Devuelve 404 si la prueba no existe.
        """
        service = CatalogService(db.session)
        try:
            updated = service.update_test(test_id, payload, is_patch=True)
        except SchemaValidationError as e:
            return {"error": str(e)}, 422
        except (ConflictError, DuplicateCodeError) as e:
            return {"error": str(e)}, 409
        except ValidationError as e:
            return {"error": str(e)}, 422

        if not updated:
            return {"error": "Prueba no encontrada"}, 404

        return updated.to_dict(), 200

    @require_role("coordinator", "admin")
    @tests_bp.response(204)
    @tests_bp.alt_response(404, schema=ErrorSchema)
    def delete(self, test_id):
        """
        Baja lógica de una prueba de lectura (BE-04 y BE-13 Escenario 5).
        Establece disabled_at con la fecha actual y devuelve 204 No Content.
        Si la prueba no existe, devuelve 404 Not Found.
        """
        service = CatalogService(db.session)
        deleted = service.soft_delete_test(test_id)
        if not deleted:
            return {"error": "Prueba no encontrada"}, 404

        return "", 204
