"""Schemas Marshmallow de centros, secciones y alumnado (T-BE10-01).

Solo se usan para serializar respuestas de solo lectura (BE-10).
Los UUID se devuelven en su forma canónica con guiones (str(uuid)).
"""
from marshmallow import Schema, fields


class CenterSchema(Schema):
    """Representación de un centro activo."""

    id = fields.Function(lambda obj: str(obj.id))
    external_id = fields.Str(attribute="external_id", allow_none=True)
    name = fields.Str(attribute="name")


class SectionSchema(Schema):
    """Representación de una sección activa de un centro."""

    id = fields.Function(lambda obj: str(obj.id))
    external_id = fields.Str(attribute="external_id", allow_none=True)
    name = fields.Str(attribute="name")
    academic_year = fields.Str(attribute="academic_year", allow_none=True)
    center_id = fields.Function(lambda obj: str(obj.center_id))


class StudentSummarySchema(Schema):
    """Representación resumida de un alumno matriculado en una sección."""

    id = fields.Function(lambda obj: str(obj.id))
    external_id = fields.Str(attribute="external_id", allow_none=True)
    name = fields.Str(attribute="name")