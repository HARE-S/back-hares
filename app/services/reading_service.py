import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.audit import log_audit
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.models.book import ReadBook
from app.models.student import Student
from app.models.test import Test
from app.repositories.reading_repository import ReadingRepository
from app.schemas.reading_schema import ReadingCreateSchema, ReadingSchema, ReadingUpdateSchema


class ReadingService:
    """
    Servicio de lógica de negocio para la gestión de lecturas de libros vinculadas a pruebas (Bloque B).
    """

    def __init__(self, session: Session):
        self.session = session
        self.reading_repo = ReadingRepository(session)

    def assign_book(
        self,
        student_id: Union[str, uuid.UUID],
        data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Asigna un libro del catálogo de pruebas a un alumno registrando el inicio de su lectura (BE-23).
        - Valida identificadores y existencia de alumno y prueba.
        - Si no se envía end_date -> lectura registrada en curso con 201 Created (Escenario 2).
        - Si el tutor no tiene asignada la sección del alumno -> 403 Forbidden (Escenario 5).
        - Si ya existe una lectura para ese mismo alumno, prueba y fecha de inicio -> 409 Conflict.
        - Registra evento de auditoría 'ASSIGN_BOOK'.
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
            raise NotFoundError("El alumno especificado no existe")

        # 2. Validar permisos del tutor sobre el alumno (Escenario 5)
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para asignar libros")
            if user_role not in ("coordinator", "coordinador", "admin", "superadmin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para asignar libros a este alumno")

        # 3. Validar esquema de entrada
        validated = ReadingCreateSchema.validate(data)

        # 4. Resolver y verificar la prueba (Test)
        test: Optional[Test] = None
        if validated.get("test_id"):
            test = self.session.get(Test, validated["test_id"])
        elif validated.get("test_identifier"):
            ident = validated["test_identifier"].strip()
            # Probar si es UUID en string
            try:
                test_uuid = uuid.UUID(ident)
                test = self.session.get(Test, test_uuid)
            except (ValueError, TypeError):
                pass

            if not test:
                test = self.session.scalars(
                    select(Test).where(
                        (func.lower(Test.code) == ident.lower()) |
                        (func.lower(Test.name) == ident.lower())
                    )
                ).first()

        if not test:
            raise NotFoundError("La prueba o libro especificado no existe en el catálogo")

        if test.disabled_at is not None:
            raise ConflictError("La prueba o libro especificado está dado de baja")

        # 5. Comprobar duplicado exacto
        if self.reading_repo.exists_duplicate(
            student_id=parsed_student_id,
            test_id=test.id,
            start_date=validated["start_date"],
        ):
            raise ConflictError(
                f"Ya existe una lectura registrada para '{test.name}' con fecha de inicio {validated['start_date']}"
            )

        # 6. Persistir la lectura
        reading = self.reading_repo.create(
            student_id=parsed_student_id,
            test_id=test.id,
            start_date=validated["start_date"],
            end_date=validated["end_date"],
            copies_note=validated.get("copies_note"),
            sessions_note=validated.get("sessions_note"),
            commit=True,
        )

        # Asegurar carga de relaciones
        self.session.refresh(reading)

        # 7. Registro en auditoría
        log_audit(
            user=current_user,
            action="ASSIGN_BOOK",
            resource_type="read_books",
            resource_id=str(reading.id),
            details={
                "student_id": str(parsed_student_id),
                "test_id": str(test.id),
                "test_code": test.code,
                "book_title": test.name,
                "start_date": validated["start_date"].isoformat(),
                "end_date": validated["end_date"].isoformat() if validated["end_date"] else None,
            },
        )

        return ReadingSchema.dump(reading)

    def close_or_update_reading(
        self,
        reading_id: Union[str, uuid.UUID],
        data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cierra o reabre una lectura de libro fijando o limpiando 'end_date' (BE-24).
        - Escenario 1: end_date >= start_date -> 200 OK con status: 'finalizada'
        - Escenario 2: end_date < start_date -> 422 Unprocessable Entity
        - Escenario 4: end_date is None -> 200 OK con status: 'en curso' (reapertura)
        - Escenario 5: reading_id no encontrado -> 404 Not Found
        - Control de permisos: tutor sobre sección del alumno o coordinador/admin.
        - Auditoría: CLOSE_READING si se cierra, REOPEN_READING si se reabre.
        """
        try:
            parsed_reading_id = (
                reading_id if isinstance(reading_id, uuid.UUID) else uuid.UUID(str(reading_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("El identificador de la lectura no es válido", field="reading_id")

        reading = self.reading_repo.get_by_id(parsed_reading_id)
        if not reading:
            raise NotFoundError("La lectura especificada no existe")

        student = reading.student
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para modificar lecturas")
            if user_role not in ("coordinator", "coordinador", "admin", "superadmin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para modificar lecturas de este alumno")

        validated = ReadingUpdateSchema.validate(data, start_date=reading.start_date)

        was_open = reading.end_date is None
        action_name = "UPDATE_READING"
        if "end_date" in validated:
            new_end = validated["end_date"]
            if new_end is not None and was_open:
                action_name = "CLOSE_READING"
            elif new_end is None and not was_open:
                action_name = "REOPEN_READING"
            reading.end_date = new_end

        if "copies_note" in validated:
            reading.copies_note = validated["copies_note"]
        if "sessions_note" in validated:
            reading.sessions_note = validated["sessions_note"]

        updated = self.reading_repo.update(reading, commit=True)
        self.session.refresh(updated)

        log_audit(
            user=current_user,
            action=action_name,
            resource_type="read_books",
            resource_id=str(updated.id),
            details={
                "student_id": str(updated.student_id),
                "test_id": str(updated.test_id),
                "end_date": updated.end_date.isoformat() if updated.end_date else None,
                "status": updated.status,
            },
        )

        return ReadingSchema.dump(updated)

    def get_student_readings(
        self,
        student_id: Union[str, uuid.UUID],
        status: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de lecturas de un alumno (BE-26 Escenario 1 y 3).
        - Escenario 1: lista completa de libros con título, fechas y estado.
        - Escenario 3: filtro por status 'en curso' o 'finalizada'.
        - Escenario 4: alumno sin lecturas -> lista vacía [].
        - Escenario 5: tutor sin permiso sobre el alumno -> 403 Forbidden.
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
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para ver lecturas")
            if user_role not in ("coordinator", "coordinador", "admin", "superadmin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para consultar las lecturas de este alumno")

        readings = self.reading_repo.get_by_student(parsed_student_id, status=status)
        return [ReadingSchema.dump(r) for r in readings]

    def get_book_students(
        self,
        book_identifier: Union[str, uuid.UUID],
        status: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de alumnos que han leído o están leyendo un libro/prueba específico (BE-26 Escenario 2).
        """
        readings = self.reading_repo.get_by_book(book_identifier, status=status)

        result: List[Dict[str, Any]] = []
        for r in readings:
            if current_user:
                user_role = str(current_user.get("role", "")).strip().lower()
                if user_role not in ("coordinator", "coordinador", "admin", "superadmin") and user_role != "pendiente":
                    assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                    student_sections = {str(ss.section_id).strip() for ss in r.student.student_sections}
                    if not (assigned_sections & student_sections):
                        continue
            dumped = ReadingSchema.dump(r)
            result.append(dumped)

        return result
