"""Endpoints de resultados de pruebas con flask-smorest."""

from flask import Response, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
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
from app.schemas.result_marshmallow import (
    ResultCreateRequestSchema,
    ResultUpdateRequestSchema,
    ResultBatchRequestSchema,
    ResultBatchResponseSchema,
    ResultResponseSchema,
    ResultHistoryResponseSchema,
    ErrorSchema,
)

results_bp = Blueprint(
    "results_v1",
    __name__,
    url_prefix="/students",
    description="Registro y consulta de resultados de pruebas",
)

single_results_bp = Blueprint(
    "single_results_v1",
    __name__,
    url_prefix="/results",
    description="Gestión individual de resultados",
)


@results_bp.route("/<student_id>/results")
class StudentResults(MethodView):
    """Resultados de un alumno."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @results_bp.arguments(ResultCreateRequestSchema)
    @results_bp.response(201, ResultResponseSchema)
    @results_bp.alt_response(400, schema=ErrorSchema)
    @results_bp.alt_response(403, schema=ErrorSchema)
    @results_bp.alt_response(409, schema=ErrorSchema)
    def post(self, payload, student_id):
        """Registrar resultado de prueba (BE-18)."""
        current_user = get_current_user()
        service = ResultService(db.session)

        try:
            result_data = service.register_result(
                student_id=student_id,
                data=payload,
                current_user=current_user,
            )
            return jsonify(result_data), 201
        except ValidationError as e:
            return jsonify({"error": str(e), "field": getattr(e, "field", None)}), 400
        except ForbiddenError as e:
            return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
        except ConflictError as e:
            return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @results_bp.response(200, ResultHistoryResponseSchema(many=True))
    @results_bp.alt_response(400, schema=ErrorSchema)
    @results_bp.alt_response(404, schema=ErrorSchema)
    @results_bp.alt_response(403, schema=ErrorSchema)
    def get(self, student_id):
        """Consultar histórico de resultados (BE-20)."""
        current_user = get_current_user()
        service = ResultService(db.session)

        try:
            history = service.get_student_history(
                student_id=student_id,
                current_user=current_user,
            )
            return jsonify(history), 200
        except ValidationError as e:
            return jsonify({"error": str(e), "field": getattr(e, "field", None)}), 400
        except NotFoundError as e:
            return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
        except ForbiddenError as e:
            return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403


@results_bp.route("/<student_id>/results/<result_id>")
class StudentResultDetail(MethodView):
    """Modificación y borrado de resultado bajo ruta de alumno."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @results_bp.arguments(ResultUpdateRequestSchema)
    @results_bp.response(200, ResultResponseSchema)
    @results_bp.alt_response(422, schema=ErrorSchema)
    @results_bp.alt_response(404, schema=ErrorSchema)
    @results_bp.alt_response(403, schema=ErrorSchema)
    def patch(self, payload, student_id, result_id):
        """Modificar resultado parcialmente (BE-21)."""
        return _update_result(payload, result_id)

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @results_bp.response(204)
    @results_bp.alt_response(404, schema=ErrorSchema)
    @results_bp.alt_response(403, schema=ErrorSchema)
    def delete(self, student_id, result_id):
        """Eliminar resultado (BE-21)."""
        return _delete_result(result_id)


@single_results_bp.route("/<result_id>")
class ResultDetail(MethodView):
    """Operaciones sobre resultado individual."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @single_results_bp.arguments(ResultUpdateRequestSchema)
    @single_results_bp.response(200, ResultResponseSchema)
    @single_results_bp.alt_response(422, schema=ErrorSchema)
    @single_results_bp.alt_response(404, schema=ErrorSchema)
    @single_results_bp.alt_response(403, schema=ErrorSchema)
    def patch(self, payload, result_id):
        """Modificar resultado parcialmente (BE-21)."""
        return _update_result(payload, result_id)

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @single_results_bp.response(204)
    @single_results_bp.alt_response(404, schema=ErrorSchema)
    @single_results_bp.alt_response(403, schema=ErrorSchema)
    def delete(self, result_id):
        """Eliminar resultado (BE-21)."""
        return _delete_result(result_id)


@single_results_bp.route("/batch", methods=["POST"])
class BatchResults(MethodView):
    """Registro en lote de resultados."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @single_results_bp.arguments(ResultBatchRequestSchema)
    @single_results_bp.response(201, ResultBatchResponseSchema)
    @single_results_bp.alt_response(400, schema=ErrorSchema)
    @single_results_bp.alt_response(403, schema=ErrorSchema)
    def post(self, payload):
        """Registrar lote de resultados (BE-22)."""
        current_user = get_current_user()
        service = ResultService(db.session)

        try:
            summary = service.register_batch(
                data=payload,
                current_user=current_user,
            )
            return jsonify(summary), 201
        except BatchValidationError as e:
            return jsonify(
                {
                    "error": "BATCH_VALIDATION_ERROR",
                    "message": e.message,
                    "errors": e.errors,
                }
            ), 400
        except ValidationError as e:
            return jsonify({"error": str(e), "field": getattr(e, "field", None)}), 400
        except ForbiddenError as e:
            return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
        except ConflictError as e:
            return jsonify({"error": "CONFLICT", "message": str(e)}), 409


# Funciones auxiliares privadas
def _update_result(payload, result_id):
    """Lógica compartida de actualización."""
    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        updated = service.update_result(
            result_id=result_id,
            data=payload,
            current_user=current_user,
        )
        return jsonify(updated), 200
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


def _delete_result(result_id):
    """Lógica compartida de borrado."""
    current_user = get_current_user()
    service = ResultService(db.session)

    try:
        service.delete_result(
            result_id=result_id,
            current_user=current_user,
        )
        return Response(status=204)
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
