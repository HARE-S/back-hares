"""Schemas Marshmallow para resultados (flask-smorest)."""

from marshmallow import Schema, fields, validate


class ResultCreateRequestSchema(Schema):
    """Registro de un resultado de prueba."""
    test_id = fields.UUID(required=True)
    section_id = fields.UUID(required=True)
    test_date = fields.Date(required=True)
    time = fields.Int(required=True, validate=validate.Range(min=1))
    successes = fields.Int(required=True, validate=validate.Range(min=0))
    mistakes = fields.Int(required=True, validate=validate.Range(min=0))


class ResultUpdateRequestSchema(Schema):
    """Modificación parcial de resultado."""
    test_id = fields.UUID()
    section_id = fields.UUID()
    test_date = fields.Date()
    time = fields.Int(validate=validate.Range(min=1))
    successes = fields.Int(validate=validate.Range(min=0))
    mistakes = fields.Int(validate=validate.Range(min=0))


class ResultBatchItemSchema(Schema):
    """Un resultado en lote."""
    student_id = fields.UUID(required=True)
    time = fields.Int()
    successes = fields.Int()
    mistakes = fields.Int()
    absent = fields.Bool()


class ResultBatchRequestSchema(Schema):
    """Registro de resultados en lote."""
    test_id = fields.UUID(required=True)
    section_id = fields.UUID(required=True)
    test_date = fields.Date(required=True)
    results = fields.List(fields.Nested(ResultBatchItemSchema), required=True)


class ResultResponseSchema(Schema):
    """Respuesta con resultado completo."""
    id = fields.UUID()
    student_id = fields.UUID()
    test_id = fields.UUID()
    section_id = fields.UUID()
    test_date = fields.Date()
    time = fields.Int()
    successes = fields.Int()
    mistakes = fields.Int()
    ppm = fields.Float(allow_none=True)
    accuracy = fields.Float(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


class ResultHistoryResponseSchema(Schema):
    """Histórico de resultados de un alumno."""
    id = fields.UUID()
    test_id = fields.UUID()
    test_name = fields.Str()
    test_words = fields.Int()
    test_letter = fields.Str(allow_none=True)
    test_type = fields.Str(allow_none=True)
    test_date = fields.Date()
    time = fields.Int()
    successes = fields.Int()
    mistakes = fields.Int()
    ppm = fields.Float(allow_none=True)
    accuracy = fields.Float(allow_none=True)


class ResultBatchResponseSchema(Schema):
    """Resumen de registro en lote."""
    registered = fields.Int()
    absent = fields.Int()
    results = fields.List(fields.Nested(ResultResponseSchema))


class ErrorSchema(Schema):
    """Respuesta de error."""
    error = fields.Str()
    message = fields.Str()
    field = fields.Str(allow_none=True)
