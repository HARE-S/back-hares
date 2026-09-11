from marshmallow import Schema, fields, validate as marshmallow_validate, validates, ValidationError
from app.models.enums import validate_book_level


class BookCreateSchema(Schema):
    """Schema para crear un libro (POST /api/v1/books)."""
    title = fields.Str(required=True, data_key="book", validate=marshmallow_validate.Length(min=1))
    level = fields.Str(required=True, validate=marshmallow_validate.Length(min=1))
    copies_note = fields.Str(load_default=None, allow_none=True)
    sessions_note = fields.Str(load_default=None, allow_none=True)

    @validates("level")
    def validate_level(self, value):
        """Valida que el nivel sea uno de los permitidos (BE-15)."""
        try:
            validate_book_level(value)
        except ValueError as e:
            raise ValidationError(str(e))


class BookUpdateSchema(Schema):
    """Schema para actualizar un libro (PUT/PATCH /api/v1/books/<id>)."""
    title = fields.Str(data_key="book", validate=marshmallow_validate.Length(min=1))
    level = fields.Str(validate=marshmallow_validate.Length(min=1))
    copies_note = fields.Str(allow_none=True)
    sessions_note = fields.Str(allow_none=True)

    @validates("level")
    def validate_level(self, value):
        """Valida que el nivel sea uno de los permitidos (BE-15)."""
        try:
            validate_book_level(value)
        except ValueError as e:
            raise ValidationError(str(e))


class BookResponseSchema(Schema):
    """Schema de respuesta para un libro."""
    id = fields.UUID()
    title = fields.Str(attribute="book")
    level = fields.Str()
    copies_note = fields.Str(allow_none=True)
    sessions_note = fields.Str(allow_none=True)
    disabled_at = fields.Date(allow_none=True)
