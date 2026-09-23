from typing import Any, Dict, List, Optional

from marshmallow import Schema, fields

from app.models.student import Student


class StudentListItemSchema(Schema):
    """Un alumno dentro del listado filtrado paginado (BE-27)."""
    id = fields.UUID()
    name = fields.Str()
    external_id = fields.Str()
    sections = fields.List(fields.Str())
    test_date = fields.Date(allow_none=True)
    ppm = fields.Float(allow_none=True)
    reading_comprehension = fields.Float(allow_none=True)


class StudentListResponseSchema(Schema):
    """Respuesta paginada del listado con filtros multicriterio (BE-27)."""
    items = fields.List(fields.Nested(StudentListItemSchema))
    total = fields.Int()
    page = fields.Int()
    limit = fields.Int()
    pages = fields.Int()
    missing_data = fields.Dict(keys=fields.Str(), values=fields.Int(), allow_none=True)


class StudentErrorResponseSchema(Schema):
    """Respuesta de error del listado (formato flask-smorest: code/status/message)."""
    code = fields.Int()
    status = fields.Str()
    message = fields.Str()


class StudentSearchSectionItemSchema(Schema):
    """Sección activa de un alumno en resultados de búsqueda (BE-29)."""
    id = fields.UUID()
    name = fields.Str()
    center = fields.Str()
    center_id = fields.UUID(allow_none=True)


class StudentSearchItemSchema(Schema):
    """Un alumno en los resultados de búsqueda por nombre (BE-29)."""
    id = fields.UUID()
    name = fields.Str()
    external_id = fields.Str()
    sections = fields.List(fields.Nested(StudentSearchSectionItemSchema))


class StudentSearchResponseSchema(Schema):
    """Respuesta paginada de la búsqueda de alumnos (BE-29)."""
    items = fields.List(fields.Nested(StudentSearchItemSchema))
    total = fields.Int()
    page = fields.Int()
    limit = fields.Int()
    pages = fields.Int()


class StudentDetailSchema:
    """
    Serializador agregado para la ficha completa del alumno (BE-28).
    Compone en un único payload:
    - Datos personales del alumno.
    - Secciones actuales e históricas distinguidas claramente.
    - Resultados de pruebas con métricas derivadas (PPM, eficacia/aciertos).
    - Historial de lecturas con estado y datos del libro.
    """

    @classmethod
    def dump(
        cls,
        student: Student,
        current_sections: List[Dict[str, Any]],
        historical_sections: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        readings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "id": str(student.id),
            "external_id": student.external_id,
            "name": student.name,
            "academic_status": student.academic_status,
            "sector": student.sector,
            "disabled_at": student.disabled_at.isoformat() if student.disabled_at else None,
            "sections": {
                "current": current_sections,
                "historical": historical_sections,
            },
            "current_sections": current_sections,
            "historical_sections": historical_sections,
            "results": results,
            "readings": readings,
            "total_results": len(results),
            "total_readings": len(readings),
        }
