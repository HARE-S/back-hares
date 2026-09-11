from marshmallow import Schema, fields, validate


class TestCreateSchema(Schema):
    """Schema para crear una prueba (POST /api/v1/tests)."""
    code = fields.Str(required=True, validate=validate.Length(min=1))
    name = fields.Str(required=True, validate=validate.Length(min=1))
    words = fields.Int(required=True, validate=validate.Range(min=1))
    level = fields.Str(load_default=None, allow_none=True)
    type = fields.Str(load_default=None, allow_none=True)


class TestUpdateSchema(Schema):
    """Schema para actualizar una prueba (PUT/PATCH /api/v1/tests/<id>)."""
    code = fields.Str(validate=validate.Length(min=1))
    name = fields.Str(validate=validate.Length(min=1))
    words = fields.Int(validate=validate.Range(min=1))
    level = fields.Str(allow_none=True)
    type = fields.Str(allow_none=True)


class TestResponseSchema(Schema):
    """Schema de respuesta para una prueba."""
    id = fields.UUID()
    code = fields.Str()
    name = fields.Str()
    words = fields.Int()
    level = fields.Str(allow_none=True)
    type = fields.Str(allow_none=True)
    disabled_at = fields.Date(allow_none=True)
