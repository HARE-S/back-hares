import math
from typing import Any, Dict, List, Optional
import unicodedata


def remove_accents(input_str: str) -> str:
    """
    Elimina los acentos y signos diacríticos de una cadena para comparaciones insensibles a tildes.
    Ej: 'José María' -> 'Jose Maria'
    """
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join(c for c in nfkd_form if not unicodedata.combining(c))


class PaginationParams:
    """
    Parámetros de paginación comunes para listados (Contrato 4 / T-BE14-01).
    """

    def __init__(self, page: Optional[Any] = 1, limit: Optional[Any] = 10):
        try:
            p = int(page) if page is not None else 1
            self.page = max(1, p)
        except (ValueError, TypeError):
            self.page = 1

        try:
            l = int(limit) if limit is not None else 10
            self.limit = max(1, min(100, l))
        except (ValueError, TypeError):
            self.limit = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def paginate_response(
    items: List[Any],
    total: int,
    page: int,
    limit: int,
) -> Dict[str, Any]:
    """
    Construye la respuesta paginada canónica para la API.
    """
    pages = math.ceil(total / limit) if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


# Schemas Marshmallow para flask-smorest (BE-48)
from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class PaginationQueryArgsSchema(Schema):
    """Parámetros de paginación en query string."""
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    limit = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


class StudentFilterArgsSchema(Schema):
    """
    Filtros combinables para el listado del alumnado (BE-27, T-BE27-01).

    Todos los criterios son opcionales y se combinan en conjunción (AND):
    - center_id / section_id: ámbito de centro y sección (T-BE27-02).
    - gender / academic_status / sector: igualdad sobre las columnas nullable
      (T-BE27-04); `__missing__` selecciona a los alumnos sin el dato (T-BE27-05).
    - min_age / max_age: edad derivada de birth_date en la consulta, nunca
      almacenada (T-BE27-03).
    - page / limit: paginación reutilizando los rangos canónicos del contrato 4.
    """
    center_id = fields.UUID(load_default=None, data_key="center_id")
    section_id = fields.UUID(load_default=None, data_key="section_id")
    gender = fields.Str(load_default=None, validate=validate.Length(max=20))
    academic_status = fields.Str(load_default=None, validate=validate.Length(max=100))
    sector = fields.Str(load_default=None, validate=validate.Length(max=100))
    min_age = fields.Int(load_default=None, validate=validate.Range(min=0, max=120))
    max_age = fields.Int(load_default=None, validate=validate.Range(min=0, max=120))
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    limit = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))

    @validates_schema
    def _validate_age_range(self, data, **kwargs):
        min_age = data.get("min_age")
        max_age = data.get("max_age")
        if min_age is not None and max_age is not None and min_age > max_age:
            raise ValidationError(
                "El rango de edad no es válido: min_age debe ser menor o igual que max_age",
                field_names=["min_age", "max_age"],
            )


class ErrorSchema(Schema):
    """Respuesta de error genérica."""
    error = fields.Str()


def translate_marshmallow_errors(messages: dict) -> str:
    """
    Convierte mensajes de error de Marshmallow a un formato amigable en español.
    Ej: {'code': ['Missing data for required field.']} -> 'code: es obligatorio'
    """
    translations = {
        "missing data for required field.": "es obligatorio",
        "shorter than minimum length": "es muy corto",
        "must be greater than or equal to": "debe ser mayor o igual a",
    }

    error_parts = []
    for field, errors in messages.items():
        if isinstance(errors, list) and errors:
            msg = errors[0].lower()
            # Try to find a translation
            translated = msg
            for en_phrase, es_phrase in translations.items():
                if en_phrase in msg:
                    translated = es_phrase
                    break
            error_parts.append(translated if field == "overall" else f"{field} {translated}")
        elif isinstance(errors, str):
            error_parts.append(f"{field} {errors}")

    return "; ".join(error_parts) if error_parts else "Datos inválidos"
