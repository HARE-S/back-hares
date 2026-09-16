"""Endpoints de comparativas de evolución por grupos (BE-32)."""

from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint

from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.schemas.comparison_schema import (
    ComparisonErrorResponseSchema,
    GroupComparisonQuerySchema,
    GroupComparisonResponseSchema,
)
from app.services.comparison_service import ComparisonService

comparison_bp = Blueprint(
    "comparison_v1",
    __name__,
    url_prefix="/comparison",
    description="Comparativas de evolución por grupos",
)


@comparison_bp.route("/groups")
class GroupComparison(MethodView):
    """Comparativa de evolución media entre secciones, centros o perfiles."""

    @require_role("tutor", "profesor", "coordinator", "coordinador", "admin")
    @comparison_bp.arguments(GroupComparisonQuerySchema, location="query")
    @comparison_bp.response(200, GroupComparisonResponseSchema)
    @comparison_bp.alt_response(400, schema=ComparisonErrorResponseSchema)
    @comparison_bp.alt_response(403, schema=ComparisonErrorResponseSchema)
    @comparison_bp.alt_response(404, schema=ComparisonErrorResponseSchema)
    @comparison_bp.alt_response(422, schema=ComparisonErrorResponseSchema)
    def get(self, args):
        """
        Comparativa de evolución media por grupos (BE-32).

        - Agrupa por sección, centro o perfil (sector).
        - Cada grupo aporta media de PPM, comprensión y Vef con tamaño de la
          muestra (alumnos y pruebas consideradas).
        - Umbral de representatividad configurable (min_sample).
        - Grupos sin datos con tamaño cero y sin media.
        - Comparativas entre centros solo para coordinador y responsable
          pedagógico; tutores limitados a sus secciones.
        """
        current_user = get_current_user()
        service = ComparisonService(db.session)

        try:
            return service.get_group_comparison(
                group_by=args.get("group_by"),
                section_ids=args.get("section_ids"),
                center_id=args.get("center_id"),
                min_sample=args.get("min_sample"),
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                current_user=current_user,
            )
        except ValidationError as e:
            abort(400, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))
        except ForbiddenError as e:
            abort(403, description=str(e))