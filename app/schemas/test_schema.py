from typing import Any, Dict
from app.core.exceptions import SchemaValidationError


class TestUpdateSchema:
    """
    Esquema de validación para actualización de pruebas (BE-13).
    Soporta validación de reemplazo completo (PUT) y actualización parcial (PATCH)
    donde todos los campos son opcionales (T-BE13-01).
    Lanza SchemaValidationError (mapeado a HTTP 422) si algún dato no es válido.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any], is_patch: bool = False) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise SchemaValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        cleaned = {}

        if not is_patch:
            # PUT requiere campos principales obligatorios
            for required_field in ("code", "name", "words"):
                if required_field not in data or data[required_field] is None:
                    raise SchemaValidationError(f"El campo '{required_field}' es obligatorio en PUT")

        # Validación de 'code'
        if "code" in data:
            code_val = data["code"]
            if code_val is None or not str(code_val).strip():
                raise SchemaValidationError("El campo 'code' no puede estar vacío")
            cleaned["code"] = str(code_val).strip()

        # Validación de 'name'
        if "name" in data:
            name_val = data["name"]
            if name_val is None or not str(name_val).strip():
                raise SchemaValidationError("El campo 'name' no puede estar vacío")
            cleaned["name"] = str(name_val).strip()

        # Validación de 'words'
        if "words" in data:
            words_val = data["words"]
            if words_val is None or isinstance(words_val, bool):
                raise SchemaValidationError("El campo 'words' debe ser un número entero mayor que cero")
            try:
                words_int = int(words_val)
                if words_int <= 0:
                    raise SchemaValidationError("El campo 'words' debe ser mayor que cero")
                cleaned["words"] = words_int
            except (ValueError, TypeError):
                raise SchemaValidationError("El campo 'words' debe ser un número entero mayor que cero")

        # Validación de 'level'
        if "level" in data:
            level_val = data["level"]
            cleaned["level"] = str(level_val).strip() if level_val is not None else None

        # Validación de 'type'
        if "type" in data:
            type_val = data["type"]
            cleaned["type"] = str(type_val).strip() if type_val is not None else None

        return cleaned
