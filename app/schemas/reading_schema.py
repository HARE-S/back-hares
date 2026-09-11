import datetime
from typing import Any, Dict, Optional, Union
import uuid
from app.core.exceptions import SchemaValidationError, ValidationError


def _parse_uuid(val: Any, field_name: str) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(f"El campo '{field_name}' debe ser un identificador válido", field=field_name)


def _parse_date(val: Any, field_name: str) -> datetime.date:
    if isinstance(val, datetime.date):
        return val
    s = str(val).strip()
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError, AttributeError):
        pass
    try:
        return datetime.datetime.strptime(s, "%d/%m/%Y").date()
    except (ValueError, TypeError, AttributeError):
        pass
    raise ValidationError(
        f"El campo '{field_name}' debe tener un formato de fecha válido (YYYY-MM-DD o DD/MM/YYYY)",
        field=field_name,
    )


class ReadingCreateSchema:
    """
    Esquema de validación para asignación de una lectura a un alumno (BE-23).
    - 'book_id': obligatorio, UUID.
    - 'start_date': obligatorio, fecha ISO (YYYY-MM-DD).
    - 'end_date': opcional, fecha ISO (YYYY-MM-DD) o None.
    - Validación de coherencia temporal: end_date >= start_date (422 SchemaValidationError).
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        # 1. book_id
        if "book_id" not in data or data["book_id"] is None:
            raise ValidationError("El campo 'book_id' es obligatorio", field="book_id")
        book_id = _parse_uuid(data["book_id"], "book_id")

        # 2. start_date
        if "start_date" not in data or data["start_date"] is None:
            raise ValidationError("El campo 'start_date' es obligatorio", field="start_date")
        start_date = _parse_date(data["start_date"], "start_date")

        # 3. end_date (opcional)
        end_date: Optional[datetime.date] = None
        if "end_date" in data and data["end_date"] is not None and data["end_date"] != "":
            end_date = _parse_date(data["end_date"], "end_date")
            if end_date < start_date:
                raise SchemaValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio")

        return {
            "book_id": book_id,
            "start_date": start_date,
            "end_date": end_date,
        }


class ReadingUpdateSchema:
    """
    Esquema de validación para cierre y reapertura de lecturas (BE-24).
    - Permite fijar o limpiar 'end_date'.
    - Si 'end_date' es None o cadena vacía, representa reapertura.
    - Si 'end_date' se proporciona y es anterior a start_date, lanza SchemaValidationError (422).
    """

    @classmethod
    def validate(
        cls,
        data: Dict[str, Any],
        start_date: Optional[datetime.date] = None,
    ) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        result: Dict[str, Any] = {}

        if "end_date" in data:
            raw_val = data["end_date"]
            if raw_val is None or str(raw_val).strip().lower() in ("", "null", "none"):
                result["end_date"] = None
            else:
                end_date = _parse_date(raw_val, "end_date")
                if start_date is not None and end_date < start_date:
                    raise SchemaValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio")
                result["end_date"] = end_date

        return result


class ReadingSchema:
    """
    Serializador de entidades ReadBook para respuestas API (BE-23, BE-24, BE-26).
    """

    @classmethod
    def dump(cls, reading: Any) -> Dict[str, Any]:
        is_finished = reading.end_date is not None
        status = "finalizada" if is_finished else "en curso"

        book_title = None
        book_level = None
        if hasattr(reading, "book") and reading.book:
            book_title = reading.book.title
            book_level = reading.book.level

        data = {
            "id": str(reading.id),
            "student_id": str(reading.student_id),
            "book_id": str(reading.book_id),
            "book_title": book_title,
            "title": book_title,
            "book_level": book_level,
            "level": book_level,
            "start_date": reading.start_date.isoformat() if reading.start_date else None,
            "end_date": reading.end_date.isoformat() if reading.end_date else None,
            "status": status,
        }
        return data
