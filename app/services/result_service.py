import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy.orm import Session
from app.analytics.metrics import calculate_ppm
from app.core.audit import log_audit
from app.core.exceptions import (
    BatchValidationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.models.center import Section
from app.models.student import Student
from app.models.test import Test
from app.repositories.result_repository import ResultRepository
from app.schemas.result_schema import (
    ResultBatchSchema,
    ResultCreateSchema,
    ResultSchema,
    ResultUpdateSchema,
)


class ResultService:
    """
    Servicio de lógica de negocio para registro y gestión de resultados de pruebas (Bloque B).
    """

    def __init__(self, session: Session):
        self.session = session
        self.result_repo = ResultRepository(session)

    def register_result(
        self,
        student_id: Union[str, uuid.UUID],
        data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registra el resultado de una prueba para un alumno (BE-18).
        - Valida referencias de alumno, prueba y sección (Escenario 3: 400 Bad Request si no existen).
        - Valida campos numéricos y no negativos (Escenario 2: 400 Bad Request).
        - Comprueba permisos del tutor sobre la sección (Escenario 6: 403 Forbidden si no la tiene asignada).
        - Comprueba duplicado exacto por alumno, prueba y fecha (Escenario 4: 409 Conflict).
        - Calcula PPM en base a las palabras de la prueba (Escenario 1).
        - Registra evento en auditoría (Escenario 8).
        """
        # 1. Parsear y verificar alumno
        try:
            parsed_student_id = (
                student_id if isinstance(student_id, uuid.UUID) else uuid.UUID(str(student_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("El identificador del alumno no es válido", field="student_id")

        student = self.session.get(Student, parsed_student_id)
        if not student:
            raise ValidationError("El alumno especificado no existe", field="student_id")

        # 2. Validar esquema de entrada
        validated = ResultCreateSchema.validate(data)

        # 3. Comprobar existencia de la prueba (Escenario 3)
        test = self.session.get(Test, validated["test_id"])
        if not test:
            raise ValidationError("La prueba especificada no existe", field="test_id")

        # 4. Comprobar existencia de la sección (Escenario 3)
        section = self.session.get(Section, validated["section_id"])
        if not section:
            raise ValidationError("La sección especificada no existe", field="section_id")

        # 5. Comprobar permisos sobre la sección (Escenario 6)
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            # Coordinadores y administradores tienen acceso irrestricto
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = current_user.get("sections") or []
                assigned_strs = {str(s).strip() for s in assigned_sections}
                target_sec_str = str(validated["section_id"]).strip()
                if target_sec_str not in assigned_strs:
                    raise ForbiddenError(
                        "El tutor no tiene permiso sobre la sección especificada para el alumno"
                    )

        # 6. Comprobar duplicado exacto (alumno, prueba y fecha - Escenario 4)
        if self.result_repo.exists_duplicate(
            student_id=parsed_student_id,
            test_id=validated["test_id"],
            test_date=validated["test_date"],
        ):
            raise ConflictError(
                f"Ya existe un resultado registrado para la prueba con fecha {validated['test_date']}"
            )

        # 7. Persistir resultado
        result = self.result_repo.create(
            student_id=parsed_student_id,
            section_id=validated["section_id"],
            test_id=validated["test_id"],
            test_date=validated["test_date"],
            time=validated["time"],
            successes=validated["successes"],
            mistakes=validated["mistakes"],
            commit=True,
        )

        # 8. Calcular PPM (Contrato 3)
        ppm = calculate_ppm(test.words, result.time)

        # 9. Registro en auditoría (Escenario 8)
        log_audit(
            user=current_user,
            action="CREATE_RESULT",
            resource_type="results",
            resource_id=str(result.id),
            details={
                "student_id": str(parsed_student_id),
                "test_id": str(validated["test_id"]),
                "section_id": str(validated["section_id"]),
                "ppm": ppm,
            },
        )

        return ResultSchema.dump(result, ppm=ppm)

    def get_student_history(
        self,
        student_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta el histórico de resultados de un alumno ordenados por fecha ascendente (BE-19 Escenario 4).
        Cada resultado incluye su PPM y su porcentaje de aciertos (accuracy).
        """
        try:
            parsed_student_id = (
                student_id if isinstance(student_id, uuid.UUID) else uuid.UUID(str(student_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("El identificador del alumno no es válido", field="student_id")

        student = self.session.get(Student, parsed_student_id)
        if not student:
            raise NotFoundError("El alumno especificado no existe")

        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar resultados")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                result_sections = {str(r.section_id).strip() for r in student.results}
                if not (assigned_sections & student_sections or assigned_sections & result_sections):
                    raise ForbiddenError(
                        "El tutor no tiene permiso para consultar los resultados de este alumno"
                    )

        results = self.result_repo.get_by_student(parsed_student_id, order_asc=True)

        history = []
        for r in results:
            ppm = calculate_ppm(r.test.words, r.time) if r.test else 0.0
            total_q = r.successes + r.mistakes
            accuracy = round((r.successes / total_q) * 100.0, 2) if total_q > 0 else 0.0
            data = ResultSchema.dump(r, ppm=ppm)
            data["accuracy"] = accuracy
            if r.test:
                data["test_code"] = r.test.code
                data["test_name"] = r.test.name
                data["test_words"] = r.test.words
                data["words"] = r.test.words
            history.append(data)

        # Registro en auditoría (BE-44 y BE-20 Notas)
        log_audit(
            user=current_user,
            action="VIEW_STUDENT_RESULTS",
            resource_type="students",
            resource_id=str(parsed_student_id),
            details={
                "results_count": len(history),
            },
        )

        return history

    def update_result(
        self,
        result_id: Union[str, uuid.UUID],
        data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Modificación parcial de un resultado existente (BE-21 Escenario 1).
        - 200 OK si es exitoso con el PPM recalculado.
        - 422 Unprocessable Entity si los datos no son válidos (Escenario 2).
        - 404 Not Found si el resultado no existe (Escenario 4).
        - 403 Forbidden si el tutor no tiene permiso sobre el alumno (Escenario 5).
        - 409 Conflict si colisiona con otro resultado para el mismo alumno, prueba y fecha.
        - Registra el valor anterior en auditoría (Escenario 6 / T-BE21-03).
        """
        try:
            parsed_id = (
                result_id if isinstance(result_id, uuid.UUID) else uuid.UUID(str(result_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise NotFoundError("El resultado especificado no existe")

        result = self.result_repo.get_by_id(parsed_id)
        if not result:
            raise NotFoundError("El resultado especificado no existe")

        # Comprobar permisos
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para modificar resultados")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in result.student.student_sections}
                if not (assigned_sections & {str(result.section_id).strip()} or assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para modificar resultados de este alumno")

        # Validar esquema de actualización (422)
        validated = ResultUpdateSchema.validate(data)

        # Si se actualiza test_id, verificar existencia
        if "test_id" in validated:
            test = self.session.get(Test, validated["test_id"])
            if not test:
                raise ValidationError("La prueba especificada no existe", field="test_id")

        # Si se actualiza section_id, verificar existencia y permiso del tutor
        if "section_id" in validated:
            section = self.session.get(Section, validated["section_id"])
            if not section:
                raise ValidationError("La sección especificada no existe", field="section_id")
            if current_user:
                user_role = str(current_user.get("role", "")).strip().lower()
                if user_role not in ("coordinator", "coordinador", "admin"):
                    assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                    if str(validated["section_id"]).strip() not in assigned_sections:
                        raise ForbiddenError("El tutor no tiene permiso sobre la nueva sección especificada")

        # Comprobar duplicado si cambia test_id o test_date
        target_test_id = validated.get("test_id", result.test_id)
        target_test_date = validated.get("test_date", result.test_date)
        if target_test_id != result.test_id or target_test_date != result.test_date:
            if self.result_repo.exists_duplicate(
                student_id=result.student_id,
                test_id=target_test_id,
                test_date=target_test_date,
                exclude_id=result.id,
            ):
                raise ConflictError("Ya existe un resultado registrado para este alumno, prueba y fecha")

        # Capturar valores anteriores y nuevos para auditoría (T-BE21-03)
        previous_values = {}
        new_values = {}
        for field, new_val in validated.items():
            old_val = getattr(result, field)
            if old_val != new_val:
                previous_values[field] = str(old_val) if isinstance(old_val, (datetime.date, uuid.UUID)) else old_val
                new_values[field] = str(new_val) if isinstance(new_val, (datetime.date, uuid.UUID)) else new_val
                setattr(result, field, new_val)

        # Persistir
        updated_result = self.result_repo.update(result, commit=True)

        # Recalcular PPM
        ppm = (
            calculate_ppm(updated_result.test.words, updated_result.time)
            if updated_result.test
            else 0.0
        )

        # Registrar en auditoría si hubo modificaciones (Escenario 6)
        if previous_values:
            log_audit(
                user=current_user,
                action="UPDATE_RESULT",
                resource_type="results",
                resource_id=str(updated_result.id),
                details={
                    "previous_values": previous_values,
                    "new_values": new_values,
                    "ppm": ppm,
                },
            )

        return ResultSchema.dump(updated_result, ppm=ppm)

    def delete_result(
        self,
        result_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Anulación y borrado físico de un resultado (BE-21 Escenario 3).
        - 204 No Content si se elimina con éxito.
        - 404 Not Found si el resultado no existe (Escenario 4).
        - 403 Forbidden si el tutor no tiene permiso (Escenario 5).
        - Registra el valor anterior en auditoría (Escenario 6 / T-BE21-03).
        """
        try:
            parsed_id = (
                result_id if isinstance(result_id, uuid.UUID) else uuid.UUID(str(result_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise NotFoundError("El resultado especificado no existe")

        result = self.result_repo.get_by_id(parsed_id)
        if not result:
            raise NotFoundError("El resultado especificado no existe")

        # Comprobar permisos
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para anular resultados")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in result.student.student_sections}
                if not (assigned_sections & {str(result.section_id).strip()} or assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para anular resultados de este alumno")

        # Capturar valores anteriores completos para auditoría (T-BE21-03)
        previous_values = {
            "student_id": str(result.student_id),
            "section_id": str(result.section_id),
            "test_id": str(result.test_id),
            "test_date": result.test_date.isoformat() if result.test_date else None,
            "time": result.time,
            "successes": result.successes,
            "mistakes": result.mistakes,
        }

        # Borrado físico (Escenario 3 y notas)
        self.result_repo.delete(result, commit=True)

        # Registro en auditoría
        log_audit(
            user=current_user,
            action="DELETE_RESULT",
            resource_type="results",
            resource_id=str(parsed_id),
            details={
                "previous_values": previous_values,
            },
        )

    def register_batch(
        self,
        data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registra un lote de resultados de pruebas para una sección (BE-22).
        - Valida cabecera (test_id, section_id, test_date) y lista de filas.
        - Omite alumnos ausentes (sin generar registros ni ceros).
        - Comprueba permisos del tutor sobre la sección (403 Forbidden).
        - Comprueba existencia de prueba y sección (400 Bad Request).
        - Valida todas las filas antes de escribir y acumula errores (400 Bad Request con errors).
        - Garantiza atomicidad total: todo o nada (transacción atómica).
        - Calcula PPM para cada resultado y registra evento en auditoría.
        """
        if not isinstance(data, dict):
            raise ValidationError("El cuerpo de la petición debe ser un objeto JSON válido")

        # 1. Validación previa del esquema del lote (cabecera + filas individuales)
        validated = ResultBatchSchema.validate(data)

        # 2. Comprobar permisos del tutor sobre la sección (Escenario 6)
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para registrar resultados")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = current_user.get("sections") or []
                assigned_strs = {str(s).strip() for s in assigned_sections}
                target_sec_str = str(validated["section_id"]).strip()
                if target_sec_str not in assigned_strs:
                    raise ForbiddenError("El tutor no tiene permiso sobre la sección especificada")

        # 3. Comprobar existencia de la prueba
        test = self.session.get(Test, validated["test_id"])
        if not test:
            raise ValidationError("La prueba especificada no existe", field="test_id")

        # 4. Comprobar existencia de la sección
        section = self.session.get(Section, validated["section_id"])
        if not section:
            raise ValidationError("La sección especificada no existe", field="section_id")

        # 5. Validación en BD para cada fila presente (existencia de alumno y duplicados)
        errors = list(validated.get("errors", []))
        items_to_persist = []

        for item in validated.get("items", []):
            student_id = item["student_id"]
            row_err = False

            # Comprobar si el alumno existe
            student = self.session.get(Student, student_id)
            if not student:
                errors.append({
                    "index": item["index"],
                    "student_id": str(student_id),
                    "field": "student_id",
                    "error": "El alumno especificado no existe",
                })
                row_err = True

            # Comprobar duplicado en BD para este alumno, prueba y fecha (Escenario 5)
            if self.result_repo.exists_duplicate(
                student_id=student_id,
                test_id=validated["test_id"],
                test_date=validated["test_date"],
            ):
                errors.append({
                    "index": item["index"],
                    "student_id": str(student_id),
                    "field": "test_date",
                    "error": f"El alumno ya tiene un resultado registrado para la prueba con fecha {validated['test_date']}",
                })
                row_err = True

            if not row_err:
                items_to_persist.append(item)

        # Si hay cualquier error acumulado en el lote, rechazar todo antes de persistir (Atomicidad Escenarios 3, 4 y 5)
        if errors:
            raise BatchValidationError("Se encontraron errores en una o más filas del lote", errors=errors)

        # 6. Si no hay alumnos presentes (todos ausentes)
        if not items_to_persist:
            return {
                "registered_count": 0,
                "absent_count": validated["absent_count"],
                "test_id": str(validated["test_id"]),
                "section_id": str(validated["section_id"]),
                "test_date": validated["test_date"].isoformat(),
                "results": [],
            }

        # 7. Persistir lote en una sola transacción atómica (Escenario 1 y 4)
        batch_records = [
            {
                "student_id": it["student_id"],
                "section_id": validated["section_id"],
                "test_id": validated["test_id"],
                "test_date": validated["test_date"],
                "time": it["time"],
                "successes": it["successes"],
                "mistakes": it["mistakes"],
            }
            for it in items_to_persist
        ]

        created_results = self.result_repo.create_batch(batch_records, commit=True)

        # 8. Serializar resultados con PPM calculado (Escenario 1)
        serialized_results = []
        for res in created_results:
            ppm = calculate_ppm(test.words, res.time)
            serialized_results.append(ResultSchema.dump(res, ppm))

        # 9. Registro de auditoría
        log_audit(
            user=current_user,
            action="BATCH_REGISTER_RESULTS",
            resource_type="results",
            resource_id=str(validated["section_id"]),
            details={
                "test_id": str(validated["test_id"]),
                "section_id": str(validated["section_id"]),
                "test_date": validated["test_date"].isoformat(),
                "registered_count": len(created_results),
                "absent_count": validated["absent_count"],
            },
        )

        return {
            "registered_count": len(created_results),
            "absent_count": validated["absent_count"],
            "test_id": str(validated["test_id"]),
            "section_id": str(validated["section_id"]),
            "test_date": validated["test_date"].isoformat(),
            "results": serialized_results,
        }


