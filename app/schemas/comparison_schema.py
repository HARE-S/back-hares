"""Schemas Marshmallow para la comparativa de evolución por grupos (BE-32)."""

from marshmallow import Schema, fields, validate


class GroupComparisonQuerySchema(Schema):
    """Parámetros de consulta de la comparativa de grupos (BE-32)."""
    group_by = fields.Str(
        required=True,
        validate=validate.OneOf(["section", "center", "profile"]),
        description="Agrupación: section, center o profile (sector).",
    )
    section_ids = fields.List(
        fields.UUID(),
        load_default=None,
        description="Secciones a comparar (repetible). Opcional en modo section.",
    )
    center_id = fields.UUID(
        load_default=None,
        description="Centro para acotar una comparativa por secciones o perfiles.",
    )
    min_sample = fields.Int(
        validate=validate.Range(min=1),
        load_default=None,
        description="Mínimo de alumnos para representatividad (configurable).",
    )
    start_date = fields.Date(
        load_default=None,
        description="Inicio del rango de fechas (YYYY-MM-DD).",
    )
    end_date = fields.Date(
        load_default=None,
        description="Fin del rango de fechas (YYYY-MM-DD).",
    )


class ComparisonGroupSchema(Schema):
    """Un grupo dentro de la comparativa (BE-32)."""
    id = fields.Str()
    name = fields.Str()
    group_by = fields.Str()
    center_id = fields.Str(allow_none=True)
    center_name = fields.Str(allow_none=True)
    has_data = fields.Bool()
    students_count = fields.Int()
    results_count = fields.Int()
    mean_ppm = fields.Float(allow_none=True)
    mean_accuracy = fields.Float(allow_none=True)
    mean_vef = fields.Float(allow_none=True)
    is_representative = fields.Bool()
    warning = fields.Str(allow_none=True)


class GroupComparisonResponseSchema(Schema):
    """Respuesta de la comparativa de evolución por grupos."""
    group_by = fields.Str()
    min_sample = fields.Int()
    groups = fields.List(fields.Nested(ComparisonGroupSchema))


class ComparisonErrorResponseSchema(Schema):
    """Respuesta de error de la comparativa (formato flask-smorest)."""
    code = fields.Int()
    status = fields.Str()
    message = fields.Str()