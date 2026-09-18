"""Endpoints de autenticación (login/registro)."""

from uuid import uuid4
from flask import session
from flask.views import MethodView
from flask_smorest import Blueprint
from app.extensions import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.schemas.auth_schema import (
    UserRegisterSchema,
    UserLoginSchema,
    TokenResponseSchema,
    UserResponseSchema,
)
from app.core.exceptions import ValidationError, UnauthorizedError, ConflictError

auth_bp = Blueprint(
    "auth_v1",
    __name__,
    description="Autenticación con login local",
)


@auth_bp.route("/register")
class Register(MethodView):
    """Registro de nuevos usuarios."""

    @auth_bp.arguments(UserRegisterSchema)
    @auth_bp.response(201, UserResponseSchema)
    def post(self, payload):
        """Registrar nuevo usuario."""
        service = AuthService(db.session)
        try:
            user = service.register(
                email=payload.get("email"),
                name=payload.get("name"),
                lastname=payload.get("lastname"),
                password=payload.get("password"),
                area=payload.get("area"),
            )
            return user, 201
        except ValidationError as e:
            return {"error": str(e)}, 422
        except ConflictError as e:
            return {"error": str(e)}, 409


@auth_bp.route("/login")
class Login(MethodView):
    """Login de usuarios."""

    @auth_bp.arguments(UserLoginSchema)
    @auth_bp.response(200, TokenResponseSchema)
    def post(self, payload):
        """Autenticar usuario, crear sesión y retornar token JWT (BE-40)."""
        auth_service = AuthService(db.session)
        try:
            result = auth_service.login(
                email=payload.get("email"),
                password=payload.get("password"),
            )

            # Crear sesión en BD
            session_service = SessionService(db.session)
            session_id = str(uuid4())
            session_service.create_session(
                user_id=result["user"]["id"],
                session_id=session_id,
            )

            # Guardar en Flask session
            session["session_id"] = session_id
            session["user_id"] = result["user"]["id"]
            session["user_email"] = result["user"]["email"]
            session["user_role"] = result["user"]["role"]
            session["user_area"] = result["user"]["area"]

            return result, 200
        except UnauthorizedError as e:
            return {"error": str(e)}, 401


@auth_bp.route("/me")
class CurrentUser(MethodView):
    """Obtener usuario actual."""

    @auth_bp.response(200, UserResponseSchema)
    def get(self):
        """Retorna los datos del usuario autenticado."""
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "No autenticado"}, 401

        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}, 404

        auth_service = AuthService(db.session)
        return auth_service._user_to_dict(user), 200


@auth_bp.route("/logout")
class Logout(MethodView):
    """Logout de usuarios."""

    @auth_bp.response(200, description="Sesión cerrada exitosamente")
    def post(self):
        """Cerrar sesión (BE-40)."""
        session_id = session.get("session_id")
        if session_id:
            try:
                session_service = SessionService(db.session)
                session_service.invalidate_session(session_id)
            except Exception:
                pass  # Continuar aunque falle la invalidación

        session.clear()
        return {"message": "Sesión cerrada"}, 200
