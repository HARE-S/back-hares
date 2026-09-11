"""Modelo de usuario y roles."""

from enum import Enum
from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class UserRole(Enum):
    """Roles de usuario en el sistema."""
    PENDING = "pendiente"
    TUTOR = "tutor"
    COORDINATOR = "coordinador"
    ADMIN = "admin"
    DIRECTOR = "director"


class User(BaseModel):
    """Usuario del sistema."""
    __tablename__ = "users"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default=UserRole.PENDING.value,
        server_default=UserRole.PENDING.value,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now(), server_default=db.func.now())

    # Relaciones
    sections = db.relationship(
        "Section",
        secondary="user_sections",
        back_populates="users",
        lazy="select",
    )

    @property
    def role_enum(self) -> UserRole:
        """Devuelve el rol como enum."""
        try:
            return UserRole(self.role)
        except ValueError:
            return UserRole.PENDING

    def has_role(self, *allowed_roles: str) -> bool:
        """Verifica si el usuario tiene alguno de los roles permitidos."""
        return self.role in allowed_roles

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"


class UserSection(BaseModel):
    """Asociación entre usuario y sección."""
    __tablename__ = "user_sections"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("user_id", "section_id", name="uq_user_section"),
    )

    def __repr__(self):
        return f"<UserSection user_id={self.user_id} section_id={self.section_id}>"
