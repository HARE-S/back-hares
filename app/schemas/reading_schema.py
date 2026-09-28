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
    - 'test_id' (UUID) o 'test_code' o 'book_title' / 'title' / 'book': obligatorio para identificar la prueba/libro.
    - 'start_date': obligatorio, fecha ISO (YYYY-MM-DD).
    - 'end_date': opcional, fecha ISO (YYYY-MM-DD) o None.
    - Validación de coherencia temporal: end_date >= start_date (422 SchemaValidationError).
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        # 1. Identificación del test/libro
        raw_test_id = data.get("test_id")
        raw_code = data.get("test_code") or data.get("code")
        raw_title = data.get("book_title") or data.get("title") or data.get("book")

        test_id: Optional[uuid.UUID] = None
        if raw_test_id:
            test_id = _parse_uuid(raw_test_id, "test_id")

        test_identifier = None
        if not test_id:
            test_identifier = raw_code or raw_title
            if not test_identifier or not str(test_identifier).strip():
                raise ValidationError("Debe especificar 'test_id', 'test_code' o el título del libro", field="test_id")
            test_identifier = str(test_identifier).strip()

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

        copies_note = data.get("copies_note")
        sessions_note = data.get("sessions_note")

        return {
            "test_id": test_id,
            "test_identifier": test_identifier,
            "start_date": start_date,
            "end_date": end_date,
            "copies_note": str(copies_note).strip() if copies_note is not None else None,
            "sessions_note": str(sessions_note).strip() if sessions_note is not None else None,
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

        if "copies_note" in data:
            result["copies_note"] = str(data["copies_note"]).strip() if data["copies_note"] is not None else None
        if "sessions_note" in data:
            result["sessions_note"] = str(data["sessions_note"]).strip() if data["sessions_note"] is not None else None

        return result


class ReadingSchema:
    """
    Serializador de entidades ReadBook para respuestas API (BE-23, BE-24, BE-26).
    """

    @classmethod
    def dump(cls, reading: Any) -> Dict[str, Any]:
        is_finished = reading.end_date is not None
        status = "finalizada" if is_finished else "en curso"

        book_title = getattr(reading, "title", None) or getattr(reading, "book_title", "Libro")
        level = getattr(reading, "level", "0")
        test_id_str = str(reading.test_id) if getattr(reading, "test_id", None) else None
        test_code = getattr(reading, "test_code", None)

        data = {
            "id": str(reading.id),
            "student_id": str(reading.student_id),
            "test_id": test_id_str,
            "test_code": test_code,
            "book_id": test_id_str or str(reading.id),  # retrocompatible
            "book_title": book_title,
            "title": book_title,
            "book": book_title,
            "book_level": level,
            "level": level,
            "status": status,
            "copies_note": getattr(reading, "copies_note", None),
            "sessions_note": getattr(reading, "sessions_note", None),
            "start_date": reading.start_date.isoformat() if reading.start_date else None,
            "end_date": reading.end_date.isoformat() if reading.end_date else None,
            "duration_days": getattr(reading, "duration_days", None),
        }

        # Datos adicionales del alumno si está cargado
        if hasattr(reading, "student") and reading.student is not None:
            data["student_name"] = reading.student.name
            data["student"] = {
                "id": str(reading.student.id),
                "name": reading.student.name,
                "academic_status": reading.student.academic_status,
                "sector": reading.student.sector,
            }

        return data
