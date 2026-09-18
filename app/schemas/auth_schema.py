"""Schemas para autenticación (login/registro)."""

from marshmallow import Schema, fields, validate, ValidationError


class UserRegisterSchema(Schema):
    """Schema para registro de nuevo usuario (login tradicional)."""
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    lastname = fields.Str(required=False, allow_none=True, missing=None)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6),
        load_only=True,
    )
    area = fields.Str(required=False, validate=validate.Length(min=1, max=255), allow_none=True)


class UserLoginSchema(Schema):
    """Schema para login."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserResponseSchema(Schema):
    """Schema para respuesta de usuario (sin contraseña)."""
    id = fields.UUID()
    email = fields.Email()
    name = fields.Str()
    lastname = fields.Str()
    area = fields.Str()
    role = fields.Str()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class TokenResponseSchema(Schema):
    """Schema para respuesta con token JWT."""
    access_token = fields.Str()
    token_type = fields.Str()
    user = fields.Nested(UserResponseSchema)
