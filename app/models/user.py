"""Modelo de usuario con autenticación local."""

from enum import Enum
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
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
    """Usuario del sistema con autenticación local."""
    __tablename__ = "users"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    area = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default=UserRole.TUTOR.value,
        server_default=UserRole.TUTOR.value,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now(), server_default=db.func.now())

    def set_password(self, password: str):
        """Hash y guarda la contraseña."""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.password_hash, password)

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

    def to_dict(self, include_password=False):
        """Convierte a diccionario, opcionalmente sin password_hash."""
        result = super().to_dict()
        if not include_password and "password_hash" in result:
            del result["password_hash"]
        return result

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}' area='{self.area}'>"
