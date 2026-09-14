"""Schemas Marshmallow para secciones."""

from marshmallow import Schema, fields


class SectionResultResponseSchema(Schema):
    """Resultado de una sección."""
    id = fields.UUID()
    student_id = fields.UUID()
    student_name = fields.Str()
    test_id = fields.UUID()
    test_name = fields.Str()
    test_words = fields.Int()
    test_letter = fields.Str(allow_none=True)
    test_date = fields.Date()
    time = fields.Int()
    successes = fields.Int()
    mistakes = fields.Int()
    ppm = fields.Float(allow_none=True)


class SectionHistoryResponseSchema(Schema):
    """Histórico agrupado de sección."""
    results = fields.List(fields.Nested(SectionResultResponseSchema))
    grouped_by_test = fields.Dict(allow_none=True)
    count = fields.Int()
