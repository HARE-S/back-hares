"""Endpoints de gestión de usuarios (BE-42, BE-43)."""

from flask.views import MethodView
from flask_smorest import Blueprint
from app.auth.decorators import require_role, get_current_user
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.extensions import db
from app.services.user_service import UserService
from app.schemas.user_schema import (
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema,
    UserAssignSectionSchema,
)
from app.schemas.common import PaginationQueryArgsSchema
from app.schemas.result_marshmallow import ErrorSchema

users_bp = Blueprint(
    "users_v1",
    __name__,
    url_prefix="/users",
    description="Gestión de usuarios y roles (BE-42, BE-43, BE-44)",
)


@users_bp.route("")
class UsersList(MethodView):
    """Listado y creación de usuarios."""

    @require_role("admin", "director")
    @users_bp.arguments(PaginationQueryArgsSchema, location="query")
    @users_bp.response(200, UserResponseSchema(many=True))
    def get(self, args):
        """Listar usuarios (solo admin/director)."""
        page = args.get("page", 1)
        limit = args.get("limit", 10)

        service = UserService(db.session)
        result = service.list_users(page=page, limit=limit)
        return result["items"], 200

    @require_role("admin", "director")
    @users_bp.arguments(UserCreateSchema)
    @users_bp.response(201, UserResponseSchema)
    @users_bp.alt_response(409, schema=ErrorSchema)
    def post(self, payload):
        """Crear usuario y asignar rol (BE-42)."""
        service = UserService(db.session)

        try:
            user = service.create_user(
                email=payload.get("email"),
                name=payload.get("name"),
                role=payload.get("role"),
            )
            return user, 201
        except ValidationError as e:
            return {"error": str(e)}, 422
        except ConflictError as e:
            return {"error": str(e)}, 409


@users_bp.route("/<user_id>")
class UserDetail(MethodView):
    """Operaciones sobre un usuario individual."""

    @require_role("admin", "director")
    @users_bp.response(200, UserResponseSchema)
    @users_bp.alt_response(404, schema=ErrorSchema)
    def get(self, user_id):
        """Obtener detalles del usuario."""
        service = UserService(db.session)

        try:
            user = service.get_user(user_id)
            return user, 200
        except NotFoundError as e:
            return {"error": str(e)}, 404

    @require_role("admin", "director")
    @users_bp.arguments(UserUpdateSchema)
    @users_bp.response(200, UserResponseSchema)
    @users_bp.alt_response(404, schema=ErrorSchema)
    @users_bp.alt_response(422, schema=ErrorSchema)
    def patch(self, payload, user_id):
        """Modificar usuario (rol, estado)."""
        service = UserService(db.session)

        try:
            if "role" in payload:
                user = service.update_user_role(user_id, payload["role"])
            else:
                user = service.get_user(user_id)
            return user, 200
        except NotFoundError as e:
            return {"error": str(e)}, 404
        except ValidationError as e:
            return {"error": str(e)}, 422


@users_bp.route("/<user_id>/sections")
class UserSections(MethodView):
    """Asignación de usuario a secciones."""

    @require_role("admin", "director")
    @users_bp.arguments(UserAssignSectionSchema)
    @users_bp.response(201, UserResponseSchema)
    @users_bp.alt_response(404, schema=ErrorSchema)
    @users_bp.alt_response(409, schema=ErrorSchema)
    def post(self, payload, user_id):
        """Asignar usuario a sección (BE-43)."""
        service = UserService(db.session)

        try:
            user = service.assign_section(
                user_id=user_id,
                section_id=str(payload.get("section_id")),
            )
            return user, 201
        except NotFoundError as e:
            return {"error": str(e)}, 404
        except ConflictError as e:
            return {"error": str(e)}, 409

    @require_role("admin", "director")
    @users_bp.arguments(UserAssignSectionSchema)
    @users_bp.response(204)
    @users_bp.alt_response(404, schema=ErrorSchema)
    def delete(self, payload, user_id):
        """Remover usuario de sección."""
        service = UserService(db.session)

        try:
            service.remove_section(
                user_id=user_id,
                section_id=str(payload.get("section_id")),
            )
            return "", 204
        except NotFoundError as e:
            return {"error": str(e)}, 404
