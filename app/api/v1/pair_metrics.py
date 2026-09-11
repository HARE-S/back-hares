"""Endpoints de métricas de par (funcional/literario)."""

from flask.views import MethodView
from flask_smorest import Blueprint
from app.core.decorators import require_role
from app.extensions import db
from app.services.pair_metrics_service import PairMetricsService
from app.schemas.pair_metrics_schema import (
    PairSeriesResponseSchema,
    ProgressResponseSchema,
    GroupProgressResponseSchema,
)

pair_metrics_bp = Blueprint(
    "pair_metrics_v1",
    __name__,
    description="Métricas de par: progresión funcional/literario",
)


@pair_metrics_bp.route("/students/<uuid:student_id>/pair-series")
class StudentPairSeries(MethodView):
    @require_role("tutor", "coordinator", "admin")
    @pair_metrics_bp.response(200, PairSeriesResponseSchema)
    def get(self, student_id):
        """Serie de pares por letra de prueba (I, A, B, C, D, E)."""
        service = PairMetricsService(db.session)
        pairs = service.get_student_pair_series(str(student_id))
        return {"pairs": pairs}


@pair_metrics_bp.route("/students/<uuid:student_id>/progress")
class StudentProgress(MethodView):
    @require_role("tutor", "coordinator", "admin")
    @pair_metrics_bp.response(200, ProgressResponseSchema)
    def get(self, student_id):
        """Progresión individual: transiciones (I-A, A-B, ...) y progreso global."""
        service = PairMetricsService(db.session)
        return service.get_student_progress(str(student_id))


@pair_metrics_bp.route("/sections/<uuid:section_id>/group-progress")
class GroupProgress(MethodView):
    @require_role("tutor", "coordinator", "admin")
    @pair_metrics_bp.response(200, GroupProgressResponseSchema)
    def get(self, section_id):
        """
        Progresión del grupo: % de alumnos que mejoran por transición.

        Nota: exluye alumnos sin resultados en ambas pruebas de cada transición.
        """
        service = PairMetricsService(db.session)
        return service.get_group_progress(str(section_id))
