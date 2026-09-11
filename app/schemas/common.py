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
from marshmallow import Schema, fields, validate


class PaginationQueryArgsSchema(Schema):
    """Parámetros de paginación en query string."""
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    limit = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


class ErrorSchema(Schema):
    """Respuesta de error genérica."""
    error = fields.Str()
