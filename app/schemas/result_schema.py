import datetime
from typing import Any, Dict, List, Optional
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
    if isinstance(val, str):
        try:
            return datetime.date.fromisoformat(val.strip())
        except ValueError:
            pass
    raise ValidationError(f"El campo '{field_name}' debe ser una fecha válida (YYYY-MM-DD)", field=field_name)


class ResultCreateSchema:
    """
    Esquema de validación para registro de resultado (BE-18).
    Valida que los campos obligatorios existan y que time, successes y mistakes sean valores válidos y no negativos.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        # 1. test_id
        if "test_id" not in data or data["test_id"] is None:
            raise ValidationError("El campo 'test_id' es obligatorio", field="test_id")
        test_id = _parse_uuid(data["test_id"], "test_id")

        # 2. section_id
        if "section_id" not in data or data["section_id"] is None:
            raise ValidationError("El campo 'section_id' es obligatorio", field="section_id")
        section_id = _parse_uuid(data["section_id"], "section_id")

        # 3. test_date
        if "test_date" not in data or data["test_date"] is None:
            raise ValidationError("El campo 'test_date' es obligatorio", field="test_date")
        test_date = _parse_date(data["test_date"], "test_date")

        # 4. time
        if "time" not in data or data["time"] is None:
            raise ValidationError("El campo 'time' es obligatorio", field="time")
        raw_time = data["time"]
        if isinstance(raw_time, bool):
            raise ValidationError("El campo 'time' debe ser un número entero de segundos", field="time")
        try:
            time_val = int(raw_time)
        except (ValueError, TypeError):
            raise ValidationError("El campo 'time' debe ser un número entero de segundos", field="time")
        if time_val < 0:
            raise ValidationError("El campo 'time' no puede ser negativo", field="time")
        if time_val == 0:
            raise ValidationError("El campo 'time' debe ser mayor que cero", field="time")

        # 5. successes
        if "successes" not in data or data["successes"] is None:
            raise ValidationError("El campo 'successes' es obligatorio", field="successes")
        raw_successes = data["successes"]
        if isinstance(raw_successes, bool):
            raise ValidationError("El campo 'successes' debe ser un número entero no negativo", field="successes")
        try:
            successes_val = int(raw_successes)
        except (ValueError, TypeError):
            raise ValidationError("El campo 'successes' debe ser un número entero", field="successes")
        if successes_val < 0:
            raise ValidationError("El campo 'successes' no puede ser negativo", field="successes")

        # 6. mistakes
        if "mistakes" not in data or data["mistakes"] is None:
            raise ValidationError("El campo 'mistakes' es obligatorio", field="mistakes")
        raw_mistakes = data["mistakes"]
        if isinstance(raw_mistakes, bool):
            raise ValidationError("El campo 'mistakes' debe ser un número entero no negativo", field="mistakes")
        try:
            mistakes_val = int(raw_mistakes)
        except (ValueError, TypeError):
            raise ValidationError("El campo 'mistakes' debe ser un número entero", field="mistakes")
        if mistakes_val < 0:
            raise ValidationError("El campo 'mistakes' no puede ser negativo", field="mistakes")

        return {
            "test_id": test_id,
            "section_id": section_id,
            "test_date": test_date,
            "time": time_val,
            "successes": successes_val,
            "mistakes": mistakes_val,
        }


class ResultSchema:
    """
    Serializador para entidades Result con el PPM inyectado (BE-18 Escenario 1).
    """

    @classmethod
    def dump(cls, result: Any, ppm: Optional[float] = None) -> Dict[str, Any]:
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        if ppm is not None:
            data["ppm"] = float(ppm)
        return data


class ResultUpdateSchema:
    """
    Esquema de validación para actualización parcial de resultado (BE-21).
    Todos los campos son opcionales. Lanza SchemaValidationError (422) si algún valor es inválido o negativo.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise SchemaValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        validated: Dict[str, Any] = {}

        if "time" in data and data["time"] is not None:
            raw_time = data["time"]
            if isinstance(raw_time, bool):
                raise SchemaValidationError("El campo 'time' debe ser un número entero de segundos")
            try:
                time_val = int(raw_time)
            except (ValueError, TypeError):
                raise SchemaValidationError("El campo 'time' debe ser un número entero de segundos")
            if time_val <= 0:
                raise SchemaValidationError("El campo 'time' debe ser mayor que cero")
            validated["time"] = time_val

        if "successes" in data and data["successes"] is not None:
            raw_succ = data["successes"]
            if isinstance(raw_succ, bool):
                raise SchemaValidationError("El campo 'successes' debe ser un número entero no negativo")
            try:
                succ_val = int(raw_succ)
            except (ValueError, TypeError):
                raise SchemaValidationError("El campo 'successes' debe ser un número entero")
            if succ_val < 0:
                raise SchemaValidationError("El campo 'successes' no puede ser negativo")
            validated["successes"] = succ_val

        if "mistakes" in data and data["mistakes"] is not None:
            raw_mist = data["mistakes"]
            if isinstance(raw_mist, bool):
                raise SchemaValidationError("El campo 'mistakes' debe ser un número entero no negativo")
            try:
                mist_val = int(raw_mist)
            except (ValueError, TypeError):
                raise SchemaValidationError("El campo 'mistakes' debe ser un número entero")
            if mist_val < 0:
                raise SchemaValidationError("El campo 'mistakes' no puede ser negativo")
            validated["mistakes"] = mist_val

        if "test_date" in data and data["test_date"] is not None:
            val = data["test_date"]
            if isinstance(val, datetime.date):
                validated["test_date"] = val
            elif isinstance(val, str):
                try:
                    validated["test_date"] = datetime.date.fromisoformat(val.strip())
                except ValueError:
                    raise SchemaValidationError("El campo 'test_date' debe ser una fecha válida (YYYY-MM-DD)")
            else:
                raise SchemaValidationError("El campo 'test_date' debe ser una fecha válida (YYYY-MM-DD)")

        if "section_id" in data and data["section_id"] is not None:
            val = data["section_id"]
            if isinstance(val, uuid.UUID):
                validated["section_id"] = val
            else:
                try:
                    validated["section_id"] = uuid.UUID(str(val).strip())
                except (ValueError, TypeError, AttributeError):
                    raise SchemaValidationError("El campo 'section_id' debe ser un identificador válido")

        if "test_id" in data and data["test_id"] is not None:
            val = data["test_id"]
            if isinstance(val, uuid.UUID):
                validated["test_id"] = val
            else:
                try:
                    validated["test_id"] = uuid.UUID(str(val).strip())
                except (ValueError, TypeError, AttributeError):
                    raise SchemaValidationError("El campo 'test_id' debe ser un identificador válido")

        return validated


class ResultBatchSchema:
    """
    Esquema de validación para registro de resultados en lote (BE-22).
    Valida cabecera (test_id, section_id, test_date) y lista de resultados por alumno.
    Omite alumnos ausentes (sin datos) y acumula errores por fila.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        errors: List[Dict[str, Any]] = []

        # 1. Validar cabecera
        if "test_id" not in data or data["test_id"] is None:
            raise ValidationError("El campo 'test_id' es obligatorio", field="test_id")
        test_id = _parse_uuid(data["test_id"], "test_id")

        if "section_id" not in data or data["section_id"] is None:
            raise ValidationError("El campo 'section_id' es obligatorio", field="section_id")
        section_id = _parse_uuid(data["section_id"], "section_id")

        if "test_date" not in data or data["test_date"] is None:
            raise ValidationError("El campo 'test_date' es obligatorio", field="test_date")
        test_date = _parse_date(data["test_date"], "test_date")

        raw_results = data.get("results")
        if raw_results is None:
            raw_results = data.get("items")
        if not isinstance(raw_results, list):
            raise ValidationError("El campo 'results' debe ser una lista de resultados", field="results")

        valid_items: List[Dict[str, Any]] = []
        absent_count = 0
        seen_students = set()

        for idx, item in enumerate(raw_results):
            if not isinstance(item, dict):
                errors.append({
                    "index": idx,
                    "field": "row",
                    "error": "La fila debe ser un objeto JSON válido",
                })
                continue

            raw_student_id = item.get("student_id")
            if not raw_student_id:
                errors.append({
                    "index": idx,
                    "field": "student_id",
                    "error": "El campo 'student_id' es obligatorio en cada fila",
                })
                continue

            try:
                student_id = (
                    raw_student_id if isinstance(raw_student_id, uuid.UUID) else uuid.UUID(str(raw_student_id).strip())
                )
            except (ValueError, TypeError, AttributeError):
                errors.append({
                    "index": idx,
                    "student_id": str(raw_student_id),
                    "field": "student_id",
                    "error": "El identificador del alumno no es válido",
                })
                continue

            # Detectar duplicados dentro del mismo lote (Escenario 5)
            if student_id in seen_students:
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "student_id",
                    "error": "El alumno aparece duplicado dentro del mismo lote",
                })
                continue
            seen_students.add(student_id)

            # Detectar ausente (Escenario 2 y notas)
            is_explicit_absent = item.get("absent") is True
            raw_time = item.get("time")
            raw_succ = item.get("successes")
            raw_mist = item.get("mistakes")

            is_empty_data = (
                (raw_time is None and raw_succ is None and raw_mist is None)
                or (raw_time == "" and raw_succ is None)
                or ("time" not in item and "successes" not in item and "mistakes" not in item)
            )

            if is_explicit_absent or is_empty_data:
                absent_count += 1
                continue

            # Validar fila presente
            row_has_error = False

            # time
            if raw_time is None or raw_time == "":
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "time",
                    "error": "El campo 'time' es obligatorio para alumnos presentes",
                })
                row_has_error = True
            elif isinstance(raw_time, bool):
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "time",
                    "error": "El campo 'time' debe ser un número entero de segundos",
                })
                row_has_error = True
            else:
                try:
                    time_val = int(raw_time)
                    if time_val <= 0:
                        errors.append({
                            "index": idx,
                            "student_id": str(student_id),
                            "field": "time",
                            "error": "El tiempo debe ser mayor que cero",
                        })
                        row_has_error = True
                except (ValueError, TypeError):
                    errors.append({
                        "index": idx,
                        "student_id": str(student_id),
                        "field": "time",
                        "error": "El campo 'time' debe ser un número entero de segundos",
                    })
                    row_has_error = True

            # successes
            if raw_succ is None or raw_succ == "":
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "successes",
                    "error": "El campo 'successes' es obligatorio para alumnos presentes",
                })
                row_has_error = True
            elif isinstance(raw_succ, bool):
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "successes",
                    "error": "El campo 'successes' debe ser un número entero",
                })
                row_has_error = True
            else:
                try:
                    succ_val = int(raw_succ)
                    if succ_val < 0:
                        errors.append({
                            "index": idx,
                            "student_id": str(student_id),
                            "field": "successes",
                            "error": "Los aciertos no pueden ser negativos",
                        })
                        row_has_error = True
                except (ValueError, TypeError):
                    errors.append({
                        "index": idx,
                        "student_id": str(student_id),
                        "field": "successes",
                        "error": "El campo 'successes' debe ser un número entero",
                    })
                    row_has_error = True

            # mistakes
            if raw_mist is None or raw_mist == "":
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "mistakes",
                    "error": "El campo 'mistakes' es obligatorio para alumnos presentes",
                })
                row_has_error = True
            elif isinstance(raw_mist, bool):
                errors.append({
                    "index": idx,
                    "student_id": str(student_id),
                    "field": "mistakes",
                    "error": "El campo 'mistakes' debe ser un número entero",
                })
                row_has_error = True
            else:
                try:
                    mist_val = int(raw_mist)
                    if mist_val < 0:
                        errors.append({
                            "index": idx,
                            "student_id": str(student_id),
                            "field": "mistakes",
                            "error": "Los errores no pueden ser negativos",
                        })
                        row_has_error = True
                except (ValueError, TypeError):
                    errors.append({
                        "index": idx,
                        "student_id": str(student_id),
                        "field": "mistakes",
                        "error": "El campo 'mistakes' debe ser un número entero",
                    })
                    row_has_error = True

            if not row_has_error:
                valid_items.append({
                    "index": idx,
                    "student_id": student_id,
                    "time": time_val,
                    "successes": succ_val,
                    "mistakes": mist_val,
                })

        return {
            "test_id": test_id,
            "section_id": section_id,
            "test_date": test_date,
            "items": valid_items,
            "absent_count": absent_count,
            "errors": errors,
        }


