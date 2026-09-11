from pathlib import Path
from flask import request, jsonify
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
from app.services.catalog_service import CatalogService
from app.schemas.test_schema import TestCreateSchema, TestUpdateSchema, TestPutSchema, TestResponseSchema
from app.schemas.common import PaginationQueryArgsSchema, translate_marshmallow_errors
from marshmallow import ValidationError as MarshmallowValidationError

tests_bp = Blueprint("tests_v1", __name__, description="Catálogo de pruebas de lectura")


@tests_bp.route("")
class TestsList(MethodView):
    def get(self):
        """
        Listado paginado y filtrado de pruebas de lectura (BE-14).
        """
        filter_text = request.args.get("filter") or request.args.get("q") or request.args.get("search")
        course_raw = request.args.get("course")
        course = int(course_raw) if course_raw else None
        test_type = request.args.get("type")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        # Sanitizar valores de paginación
        page = max(1, page)
        limit = max(1, min(100, limit))
        include_disabled_raw = request.args.get("include_disabled", "false")
        include_disabled = include_disabled_raw.lower() in ("true", "1", "yes")

        service = CatalogService(db.session)
        response_data = service.list_tests(
            filter_text=filter_text,
            course=course,
            type=test_type,
            page=page,
            limit=limit,
            include_disabled=include_disabled,
        )

        return jsonify(response_data), 200

    @require_role("coordinator", "admin")
    def post(self):
        """
        Alta de prueba en el catálogo (BE-11).
        Solo permitida para rol coordinator o admin.
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 400

        schema = TestCreateSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = translate_marshmallow_errors(e.messages)
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            new_test = service.create_test(
                code=payload.get("code"),
                name=payload.get("name"),
                words=payload.get("words"),
                course=payload.get("course"),
                test_letter=payload.get("test_letter"),
                type=payload.get("type"),
            )
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422
        except DuplicateCodeError as e:
            return jsonify({"error": str(e)}), 409

        return jsonify(new_test.to_dict()), 201


@tests_bp.route("/import", methods=["POST"])
@require_role("coordinator", "admin")
def import_tests():
    """
    Importación del catálogo de pruebas desde CSV (BE-12).
    """
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
    def put(self, test_id):
        """
        Reemplazo completo de una prueba existente (BE-13 Escenario 1).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 422

        schema = TestPutSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = translate_marshmallow_errors(e.messages)
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            updated = service.update_test(test_id, payload, is_patch=False)
        except SchemaValidationError as e:
            return jsonify({"error": str(e)}), 422
        except (ConflictError, DuplicateCodeError) as e:
            return jsonify({"error": str(e)}), 409
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422

        if not updated:
            return jsonify({"error": "Prueba no encontrada"}), 404

        return jsonify(updated.to_dict()), 200

    @require_role("coordinator", "admin")
    def patch(self, test_id):
        """
        Modificación parcial de una prueba existente (BE-13 Escenario 2 y 3).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}), 422

        schema = TestUpdateSchema()
        try:
            payload = schema.load(data)
        except MarshmallowValidationError as e:
            error_msg = translate_marshmallow_errors(e.messages)
            return jsonify({"error": error_msg}), 422

        service = CatalogService(db.session)
        try:
            updated = service.update_test(test_id, payload, is_patch=True)
        except SchemaValidationError as e:
            return jsonify({"error": str(e)}), 422
        except (ConflictError, DuplicateCodeError) as e:
            return jsonify({"error": str(e)}), 409
        except ValidationError as e:
            return jsonify({"error": str(e)}), 422

        if not updated:
            return jsonify({"error": "Prueba no encontrada"}), 404

        return jsonify(updated.to_dict()), 200

    @require_role("coordinator", "admin")
    def delete(self, test_id):
        """
        Baja lógica de una prueba de lectura (BE-04 y BE-13 Escenario 5).
        """
        service = CatalogService(db.session)
        deleted = service.soft_delete_test(test_id)
        if not deleted:
            return jsonify({"error": "Prueba no encontrada"}), 404

        return "", 204
