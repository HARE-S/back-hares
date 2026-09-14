"""Modelo de sesiones de usuario (BE-40)."""

from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class Session(BaseModel):
    """Almacena sesiones de usuario en la BD."""
    __tablename__ = "sessions"

    id = db.Column(
        db.String(255),
        primary_key=True,
        default=lambda: str(uuidv7()),
    )
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_email = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(20), nullable=False)
    user_area = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), server_default=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")

    # Relación con User
    user = db.relationship("User", foreign_keys=[user_id], lazy="select")

    def __repr__(self):
        return f"<Session id={self.id} user_id={self.user_id}>"
