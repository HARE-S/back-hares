"""Endpoints de secciones con flask-smorest."""

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.services.result_service import ResultService
from app.schemas.section_marshmallow import SectionHistoryResponseSchema
from app.schemas.result_marshmallow import ErrorSchema

sections_bp = Blueprint(
    "sections_v1",
    __name__,
    url_prefix="/sections",
    description="Gestión de secciones",
)


class SectionQueryArgsSchema(Schema):
    """Parámetros de consulta para histórico de sección."""
    group_by = fields.Str(load_default=None)
    start_date = fields.Str(load_default=None)
    end_date = fields.Str(load_default=None)


@sections_bp.route("/<section_id>/results")
class SectionResults(MethodView):
    """Histórico de resultados de una sección."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @sections_bp.arguments(SectionQueryArgsSchema, location="query")
    @sections_bp.response(200, SectionHistoryResponseSchema)
    @sections_bp.alt_response(400, schema=ErrorSchema)
    @sections_bp.alt_response(404, schema=ErrorSchema)
    @sections_bp.alt_response(403, schema=ErrorSchema)
    def get(self, args, section_id):
        """Consultar histórico de resultados de sección (BE-51)."""
        current_user = get_current_user()
        service = ResultService(db.session)

        try:
            history = service.get_section_history(
                section_id=section_id,
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                group_by=args.get("group_by"),
                current_user=current_user,
            )
            return history, 200
        except ValidationError as e:
            return {"error": str(e), "field": getattr(e, "field", None)}, 400
        except NotFoundError as e:
            return {"error": "NOT_FOUND", "message": str(e)}, 404
        except ForbiddenError as e:
            return {"error": "FORBIDDEN", "message": str(e)}, 403
