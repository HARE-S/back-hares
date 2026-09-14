"""Endpoints de autenticación (login/registro)."""

from flask.views import MethodView
from flask_smorest import Blueprint
from app.extensions import db
from app.services.auth_service import AuthService
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
    url_prefix="/auth",
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
        """Autenticar usuario y retornar token JWT."""
        service = AuthService(db.session)
        try:
            result = service.login(
                email=payload.get("email"),
                password=payload.get("password"),
            )
            return result, 200
        except UnauthorizedError as e:
            return {"error": str(e)}, 401
