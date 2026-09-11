import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy.orm import Session
from app.core.audit import log_audit
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.models.book import Book, ReadBook
from app.models.student import Student
from app.repositories.reading_repository import ReadingRepository
from app.schemas.reading_schema import ReadingCreateSchema, ReadingSchema, ReadingUpdateSchema


class ReadingService:
    """
    Servicio de lógica de negocio para la gestión de lecturas de libros (Bloque B).
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
        Asigna un libro a un alumno registrando el inicio de su lectura (BE-23).
        - Valida identificadores y existencia de alumno y libro.
        - Si el libro no existe -> 400 Bad Request (Escenario 3).
        - Si el libro tiene disabled_at -> 400 Bad Request explicando que no está disponible (Escenario 4).
        - Si no se envía end_date -> lectura registrada en curso con 201 Created (Escenario 2).
        - Si el tutor no tiene asignada la sección del alumno -> 403 Forbidden (Escenario 5).
        - Si ya existe una lectura para ese mismo alumno, libro y fecha de inicio -> 409 Conflict.
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
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para asignar libros a este alumno")

        # 3. Validar esquema de entrada
        validated = ReadingCreateSchema.validate(data)

        # 4. Comprobar existencia del libro (Escenario 3)
        book = self.session.get(Book, validated["book_id"])
        if not book:
            raise ValidationError("El libro especificado no existe", field="book_id")

        # 5. Comprobar si el libro está deshabilitado (Escenario 4)
        if book.disabled_at is not None:
            raise ValidationError("El libro ya no está disponible en el catálogo activo", field="book_id")

        # 6. Comprobar duplicado exacto (Escenario 2 de BE-25)
        if self.reading_repo.exists_duplicate(
            student_id=parsed_student_id,
            book_id=validated["book_id"],
            start_date=validated["start_date"],
        ):
            raise ConflictError(
                f"Ya existe una lectura registrada para este libro con fecha de inicio {validated['start_date']}"
            )

        # 7. Persistir la lectura
        reading = self.reading_repo.create(
            student_id=parsed_student_id,
            book_id=validated["book_id"],
            start_date=validated["start_date"],
            end_date=validated["end_date"],
            commit=True,
        )

        # 8. Registro en auditoría
        log_audit(
            user=current_user,
            action="ASSIGN_BOOK",
            resource_type="read_books",
            resource_id=str(reading.id),
            details={
                "student_id": str(parsed_student_id),
                "book_id": str(validated["book_id"]),
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
        # 1. Parsear ID de lectura
        try:
            parsed_reading_id = (
                reading_id if isinstance(reading_id, uuid.UUID) else uuid.UUID(str(reading_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise NotFoundError("La lectura especificada no existe")

        reading = self.reading_repo.get_by_id(parsed_reading_id)
        if not reading:
            raise NotFoundError("La lectura especificada no existe")

        # 2. Validar permisos del tutor sobre el alumno dueño de la lectura
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para modificar lecturas")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student = reading.student
                student_sections = {
                    str(ss.section_id).strip()
                    for ss in (student.student_sections if student else [])
                }
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para modificar lecturas de este alumno")

        # 3. Validar esquema con coherencia temporal (end_date >= start_date)
        validated = ReadingUpdateSchema.validate(data, start_date=reading.start_date)

        # 4. Actualizar campos
        was_previously_closed = reading.end_date is not None
        if "end_date" in validated:
            reading.end_date = validated["end_date"]

        self.reading_repo.update(reading, commit=True)

        # 5. Registro en auditoría
        if reading.end_date is not None:
            action = "CLOSE_READING"
        else:
            action = "REOPEN_READING" if was_previously_closed else "UPDATE_READING"

        log_audit(
            user=current_user,
            action=action,
            resource_type="read_books",
            resource_id=str(reading.id),
            details={
                "student_id": str(reading.student_id),
                "book_id": str(reading.book_id),
                "start_date": reading.start_date.isoformat(),
                "end_date": reading.end_date.isoformat() if reading.end_date else None,
            },
        )

        return ReadingSchema.dump(reading)

    def get_student_readings(
        self,
        student_id: Union[str, uuid.UUID],
        status: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta las lecturas de un alumno distinguiendo estados (BE-24 Escenario 3 y BE-26 Escenario 1).
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
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar lecturas")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError("El tutor no tiene permiso para consultar lecturas de este alumno")

        readings = self.reading_repo.get_by_student(parsed_student_id, status=status)
        return [ReadingSchema.dump(r) for r in readings]

    def get_book_students(
        self,
        book_id: Union[str, uuid.UUID],
        status: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta la lista de alumnos que han leído un libro con sus fechas de lectura (BE-26 Escenario 2).
        - 200 OK con la lista de alumnos y sus fechas de lectura.
        - Soporta filtro opcional ?status=en curso o ?status=finalizada (BE-26 Escenario 3).
        - 404 Not Found si el libro no existe.
        - 403 Forbidden si el usuario tiene rol pendiente.
        """
        try:
            parsed_book_id = (
                book_id if isinstance(book_id, uuid.UUID) else uuid.UUID(str(book_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise NotFoundError("El libro especificado no existe")

        book = self.session.get(Book, parsed_book_id)
        if not book:
            raise NotFoundError("El libro especificado no existe")

        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar lecturas")

        readings = self.reading_repo.get_by_book(parsed_book_id, status=status)
        results = []
        for r in readings:
            student_name = r.student.name if r.student else None
            results.append({
                "id": str(r.id),
                "reading_id": str(r.id),
                "student_id": str(r.student_id),
                "student_name": student_name,
                "name": student_name,
                "book_id": str(r.book_id),
                "book_title": book.title,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "status": "finalizada" if r.end_date else "en curso",
            })
        return results
