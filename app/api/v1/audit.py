"""Endpoints de auditoría (BE-44)."""

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from app.auth.decorators import require_role, get_current_user
from app.extensions import db
from app.services.audit_service import AuditService
from marshmallow import Schema, fields
from app.schemas.fields import DateTimeOrString

audit_bp = Blueprint(
    "audit_v1",
    __name__,
    url_prefix="/audit",
    description="Auditoría y logs de acciones (BE-44)",
)


class AuditLogSchema(Schema):
    """Schema de respuesta para logs de auditoría."""
    id = fields.UUID()
    user_email = fields.Email()
    action = fields.Str()
    resource_type = fields.Str(allow_none=True)
    resource_id = fields.Str(allow_none=True)
    details = fields.Str(allow_none=True)
    ip_address = fields.Str(allow_none=True)
    status = fields.Str()
    timestamp = DateTimeOrString()


@audit_bp.route("/logs")
class AuditLogs(MethodView):
    """Consulta de logs de auditoría."""

    @require_role("admin", "director", "coordinator")
    @audit_bp.response(200, AuditLogSchema(many=True))
    def get(self):
        """Obtener logs de auditoría (solo admin/coordinador)."""
        user = get_current_user()
        user_email = request.args.get("user_email")
        action = request.args.get("action")
        limit = request.args.get("limit", 50, type=int)

        service = AuditService(db.session)
        result = service.get_logs(
            user_email=user_email,
            action=action,
            limit=min(limit, 500),  # Máximo 500
        )

        return result["logs"], 200


@audit_bp.route("/logs/me")
class MyAuditLogs(MethodView):
    """Consulta de logs propios del usuario."""

    @audit_bp.response(200, AuditLogSchema(many=True))
    def get(self):
        """Obtener mis propios logs de auditoría."""
        user = get_current_user()
        if not user:
            return {"error": "UNAUTHORIZED"}, 401

        service = AuditService(db.session)
        logs = service.get_user_logs(user.get("email"), limit=100)

        return logs, 200
