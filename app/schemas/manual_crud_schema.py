"""Esquemas de alta y modificación manual de alumnado, centros y secciones (BE-50)."""

from marshmallow import Schema, fields, validate


class ManualStudentCreateSchema(Schema):
    """Alta manual de un alumno (BE-50, Escenario 1).

    El sistema genera un `external_id` propio con prefijo reservado
    (`MAN-`) y marca el registro como de origen manual.
    """
    name = fields.Str(required=True, metadata={"description": "Nombre y apellidos del alumno."})
    center_id = fields.UUID(required=True, metadata={"description": "Centro al que pertenece."})
    section_ids = fields.List(
        fields.UUID(),
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Secciones del alumno (al menos una)."},
    )
    academic_status = fields.Str(allow_none=True)
    sector = fields.Str(allow_none=True)
    area = fields.Str(allow_none=True)


class ManualStudentUpdateSchema(Schema):
    """Modificación de los datos de un alumno (BE-50, Escenario 2).

    Solo se aplican los campos presentes. La auditoría registra el valor
    anterior de cada campo modificado.
    """
    name = fields.Str(allow_none=False)
    academic_status = fields.Str(allow_none=True)
    sector = fields.Str(allow_none=True)
    area = fields.Str(allow_none=True)


class ManualSectionMembershipSchema(Schema):
    """Asignación o retirada de una sección a un alumno."""
    section_id = fields.UUID(required=True)


class ManualCenterCreateSchema(Schema):
    """Alta manual de un centro."""
    name = fields.Str(required=True)


class ManualCenterUpdateSchema(Schema):
    """Modificación de un centro. Solo campos presentes."""
    name = fields.Str()


class ManualSectionCreateSchema(Schema):
    """Alta manual de una sección.

    El centro es obligatorio por criterio de aceptación (Escenario 7 → 400),
    se valida en el servicio para mantener el código de estado pedido.
    """
    name = fields.Str(required=True)
    center_id = fields.UUID()
    academic_year = fields.Str(allow_none=True)


class ManualSectionUpdateSchema(Schema):
    """Modificación de una sección. Solo campos presentes."""
    name = fields.Str()
    academic_year = fields.Str(allow_none=True)


class ManualSectionItemSchema(Schema):
    """Sección dentro de la respuesta de un alumno (BE-50)."""
    id = fields.UUID()
    name = fields.Str()
    center_id = fields.UUID()
    center_name = fields.Str()


class ManualStudentResponseSchema(Schema):
    """Respuesta de un alumno tras alta/modificación manual."""
    id = fields.UUID()
    external_id = fields.Str()
    name = fields.Str()
    origin = fields.Str()
    area = fields.Str()
    academic_status = fields.Str(allow_none=True)
    sector = fields.Str(allow_none=True)
    disabled_at = fields.Date(allow_none=True)
    sections = fields.List(fields.Nested(ManualSectionItemSchema))


class ManualCenterResponseSchema(Schema):
    """Respuesta de un centro tras alta/modificación manual."""
    id = fields.UUID()
    external_id = fields.Str(allow_none=True)
    name = fields.Str()
    origin = fields.Str()
    disabled_at = fields.Date(allow_none=True)


class ManualSectionResponseSchema(Schema):
    """Respuesta de una sección tras alta/modificación manual."""
    id = fields.UUID()
    center_id = fields.UUID()
    external_id = fields.Str(allow_none=True)
    name = fields.Str()
    academic_year = fields.Str(allow_none=True)
    origin = fields.Str()
    disabled_at = fields.Date(allow_none=True)


class ManualErrorResponseSchema(Schema):
    """Respuesta de error para endpoints de CRUD manual (BE-50)."""
    code = fields.Int()
    status = fields.Str()
    message = fields.Str()