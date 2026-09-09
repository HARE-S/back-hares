from typing import Any, Dict
from app.core.exceptions import SchemaValidationError
from app.models.enums import validate_book_level


class BookCreateSchema:
    """
    Esquema de validación para alta de libro (BE-16).
    Requiere 'title' (o 'book') y 'level' (validado contra la enumeración de BE-15).
    Opcionales: 'copies_note' y 'sessions_note'.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise SchemaValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        raw_title = data.get("title") if "title" in data else data.get("book")
        if not raw_title or not str(raw_title).strip():
            raise SchemaValidationError("El campo 'title' es obligatorio y no puede estar vacío")

        raw_level = data.get("level")
        if not raw_level or not str(raw_level).strip():
            raise SchemaValidationError("El campo 'level' es obligatorio y no puede estar vacío")

        try:
            valid_level = validate_book_level(str(raw_level).strip())
        except ValueError as e:
            raise SchemaValidationError(str(e))

        copies_note = data.get("copies_note")
        sessions_note = data.get("sessions_note")

        return {
            "title": str(raw_title).strip(),
            "level": valid_level,
            "copies_note": str(copies_note).strip() if copies_note is not None else None,
            "sessions_note": str(sessions_note).strip() if sessions_note is not None else None,
        }


class BookUpdateSchema:
    """
    Esquema de validación para actualización de libro (PUT y PATCH en BE-16).
    """

    @classmethod
    def validate(cls, data: Dict[str, Any], is_patch: bool = False) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise SchemaValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        cleaned = {}

        if not is_patch:
            # PUT requiere campos obligatorios
            raw_title = data.get("title") if "title" in data else data.get("book")
            if not raw_title or not str(raw_title).strip():
                raise SchemaValidationError("El campo 'title' es obligatorio en PUT")
            if "level" not in data or data["level"] is None or not str(data["level"]).strip():
                raise SchemaValidationError("El campo 'level' es obligatorio en PUT")

        # Validación de title/book si está presente
        if "title" in data or "book" in data:
            raw_title = data.get("title") if "title" in data else data.get("book")
            if raw_title is None or not str(raw_title).strip():
                raise SchemaValidationError("El campo 'title' no puede estar vacío")
            cleaned["title"] = str(raw_title).strip()

        # Validación de level si está presente
        if "level" in data:
            raw_level = data["level"]
            if raw_level is None or not str(raw_level).strip():
                raise SchemaValidationError("El campo 'level' no puede estar vacío")
            try:
                cleaned["level"] = validate_book_level(str(raw_level).strip())
            except ValueError as e:
                raise SchemaValidationError(str(e))

        # Validación de copies_note
        if "copies_note" in data:
            val = data["copies_note"]
            cleaned["copies_note"] = str(val).strip() if val is not None else None

        # Validación de sessions_note
        if "sessions_note" in data:
            val = data["sessions_note"]
            cleaned["sessions_note"] = str(val).strip() if val is not None else None

        return cleaned
