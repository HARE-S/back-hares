"""Modelo de auditoría (BE-44)."""

from enum import Enum
from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class AuditAction(Enum):
    """Acciones registradas en auditoría."""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    ROLE_CHANGED = "role_changed"
    USER_CREATED = "user_created"
    USER_DEACTIVATED = "user_deactivated"
    PERMISSION_DENIED = "permission_denied"
    SESSION_EXPIRED = "session_expired"


class AuditLog(BaseModel):
    """Registro de auditoría de acciones."""
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_email = db.Column(db.String(255), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="success")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), server_default=db.func.now(), index=True)

    # Relación
    user = db.relationship("User", foreign_keys=[user_id], lazy="select")

    def __repr__(self):
        return f"<AuditLog id={self.id} action='{self.action}' user='{self.user_email}'>"
