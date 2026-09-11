"""Schemas Marshmallow para usuarios."""

from marshmallow import Schema, fields, validate


class UserCreateSchema(Schema):
    """Creación de usuario (asignación de rol)."""
    email = fields.Email(required=True)
    name = fields.Str(required=True)
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["pendiente", "tutor", "coordinador", "admin", "director"])
    )


class UserUpdateSchema(Schema):
    """Modificación de usuario."""
    role = fields.Str(
        validate=validate.OneOf(["pendiente", "tutor", "coordinador", "admin", "director"])
    )
    is_active = fields.Bool()
    name = fields.Str()


class UserResponseSchema(Schema):
    """Respuesta con datos de usuario."""
    id = fields.UUID()
    email = fields.Email()
    name = fields.Str()
    role = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    sections = fields.List(fields.UUID(), allow_none=True)


class UserAssignSectionSchema(Schema):
    """Asignación de usuario a sección."""
    section_id = fields.UUID(required=True)


class UserRemoveSectionSchema(Schema):
    """Remoción de usuario de sección."""
    section_id = fields.UUID(required=True)
