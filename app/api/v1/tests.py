from pathlib import Path
import uuid
from flask import Blueprint, jsonify, request
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

tests_bp = Blueprint("tests_v1", __name__)



@tests_bp.route("", methods=["POST"])
@require_role("coordinator", "admin")
def create_test():
    """
    Alta de prueba en el catálogo (BE-11).
    Solo permitida para rol coordinator o admin.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    service = CatalogService(db.session)
    try:
        new_test = service.create_test(
            code=data.get("code"),
            name=data.get("name"),
            words=data.get("words"),
            level=data.get("level"),
            type=data.get("type"),
        )
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except DuplicateCodeError as e:
        return jsonify({"error": str(e)}), 409

    return jsonify(new_test.to_dict()), 201


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



@tests_bp.route("", methods=["GET"])
def list_tests():
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
    from app.schemas.common import PaginationParams

    filter_text = request.args.get("filter") or request.args.get("q") or request.args.get("search")
    level = request.args.get("level")
    test_type = request.args.get("type")

    pagination = PaginationParams(
        page=request.args.get("page", 1),
        limit=request.args.get("limit", 10),
    )

    include_disabled_raw = request.args.get("include_disabled", "false")
    include_disabled = include_disabled_raw.lower() in ("true", "1", "yes")

    service = CatalogService(db.session)
    response_data = service.list_tests(
        filter_text=filter_text,
        level=level,
        type=test_type,
        page=pagination.page,
        limit=pagination.limit,
        include_disabled=include_disabled,
    )

    return jsonify(response_data), 200



@tests_bp.route("/<test_id>", methods=["PUT"])
@require_role("coordinator", "admin")
def update_test_put(test_id):
    """
    Reemplazo completo de una prueba existente (BE-13 Escenario 1).
    Devuelve 200 OK con el recurso actualizado.
    Devuelve 422 si los datos son inválidos o faltan campos obligatorios.
    Devuelve 409 si se intenta alterar el código de una prueba con resultados asociados.
    Devuelve 404 si la prueba no existe.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            422,
        )

    service = CatalogService(db.session)
    try:
        updated = service.update_test(test_id, data, is_patch=False)
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 422
    except (ConflictError, DuplicateCodeError) as e:
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    if not updated:
        return jsonify({"error": "Prueba no encontrada"}), 404

    return jsonify(updated.to_dict()), 200


@tests_bp.route("/<test_id>", methods=["PATCH"])
@require_role("coordinator", "admin")
def update_test_patch(test_id):
    """
    Modificación parcial de una prueba existente (BE-13 Escenario 2 y 3).
    Devuelve 200 OK con el recurso actualizado.
    Devuelve 422 si los datos no son válidos (ej: words <= 0).
    Devuelve 409 si se intenta alterar el código de una prueba con resultados asociados.
    Devuelve 404 si la prueba no existe.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            422,
        )

    service = CatalogService(db.session)
    try:
        updated = service.update_test(test_id, data, is_patch=True)
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 422
    except (ConflictError, DuplicateCodeError) as e:
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    if not updated:
        return jsonify({"error": "Prueba no encontrada"}), 404

    return jsonify(updated.to_dict()), 200


@tests_bp.route("/<test_id>", methods=["DELETE"])
@require_role("coordinator", "admin")
def delete_test(test_id):
    """
    Baja lógica de una prueba de lectura (BE-04 y BE-13 Escenario 5).
    Establece disabled_at con la fecha actual y devuelve 204 No Content.
    Si la prueba no existe, devuelve 404 Not Found.
    """
    service = CatalogService(db.session)
    deleted = service.soft_delete_test(test_id)
    if not deleted:
        return jsonify({"error": "Prueba no encontrada"}), 404

    return "", 204

