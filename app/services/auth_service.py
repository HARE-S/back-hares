"""Servicio de autenticación con JWT."""

from datetime import datetime, timedelta
import jwt
from flask import current_app
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.exceptions import ValidationError, UnauthorizedError, ConflictError


class AuthService:
    """Gestiona autenticación, registro y tokens JWT."""

    def __init__(self, session: Session):
        self.session = session

    def register(self, email: str, name: str, lastname: str, password: str, area: str) -> dict:
        """Registra un nuevo usuario (login tradicional, sin restricción de dominio)."""
        # Validar email
        if not email or "@" not in email:
            raise ValidationError("Email inválido")

        # Verificar que el email no exista
        existing = self.session.query(User).filter(User.email == email).first()
        if existing:
            raise ConflictError(f"El email '{email}' ya está registrado")

        # Validar contraseña (mínimo 6 caracteres)
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")

        # Crear usuario con rol "pendiente" (requiere aprobación del superadmin)
        user = User(
            email=email,
            name=name,
            lastname=lastname,
            area=area,
        )
        user.role = "pendiente"  # login tradicional inicia con rol pendiente
        user.set_password(password)
        self.session.add(user)
        self.session.commit()

        return self._user_to_dict(user)

    def login(self, email: str, password: str) -> dict:
        """Autentica usuario y retorna token JWT."""
        user = self.session.query(User).filter(User.email == email).first()
        if not user or not user.verify_password(password):
            raise UnauthorizedError("Email o contraseña inválidos")

        if not user.is_active:
            raise UnauthorizedError("Usuario inactivo")

        # Generar token JWT
        token = self._generate_token(user)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": self._user_to_dict(user),
        }

    def verify_token(self, token: str) -> dict:
        """Verifica y decodifica un token JWT."""
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token expirado")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Token inválido")

    def get_current_user(self, token: str) -> User:
        """Obtiene el usuario actual desde el token."""
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError("Usuario no encontrado")
        return user

    def _generate_token(self, user: User) -> str:
        """Genera un token JWT para el usuario."""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "area": user.area,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        return jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def _user_to_dict(self, user: User) -> dict:
        """Convierte usuario a diccionario sin password."""
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "lastname": user.lastname,
            "area": user.area,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
