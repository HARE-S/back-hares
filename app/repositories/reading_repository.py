import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import ConflictError
from app.models.book import ReadBook


class ReadingRepository:
    """
    Repositorio para persistencia y consulta de asignaciones y lecturas de libros (Bloque B).
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        student_id: uuid.UUID,
        book_id: uuid.UUID,
        start_date: datetime.date,
        end_date: Optional[datetime.date] = None,
        commit: bool = True,
    ) -> ReadBook:
        """
        Crea y persiste una nueva lectura de libro para un alumno (BE-23).
        Controla colisión de clave única (student_id, book_id, start_date) y lanza ConflictError (BE-25 Escenario 2).
        """
        reading = ReadBook(
            student_id=student_id,
            book_id=book_id,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            self.session.add(reading)
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_read_books_student_book_start" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe una lectura registrada para este alumno, libro y fecha de inicio")
            raise
        return reading

    def exists_duplicate(
        self,
        student_id: uuid.UUID,
        book_id: uuid.UUID,
        start_date: datetime.date,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Comprueba si ya existe una lectura para el mismo alumno, libro y fecha de inicio exacta.
        """
        stmt = select(ReadBook).where(
            ReadBook.student_id == student_id,
            ReadBook.book_id == book_id,
            ReadBook.start_date == start_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(ReadBook.id != exclude_id)
        return self.session.scalars(stmt).first() is not None

    def get_by_id(self, reading_id: uuid.UUID) -> Optional[ReadBook]:
        """
        Obtiene una lectura por su ID con carga ansiosa de relaciones book, student y secciones.
        """
        from app.models.student import Student
        stmt = (
            select(ReadBook)
            .where(ReadBook.id == reading_id)
            .options(
                joinedload(ReadBook.book),
                joinedload(ReadBook.student).joinedload(Student.student_sections),
            )
        )
        return self.session.scalars(stmt).first()

    def get_by_student(
        self,
        student_id: uuid.UUID,
        status: Optional[str] = None,
        order_asc: bool = True,
    ) -> List[ReadBook]:
        """
        Obtiene el historial de lecturas de un alumno, con precarga de libro (BE-26 Escenario 1).
        Soporta filtro por estado ('en curso' o 'finalizada' - BE-26 Escenario 3).
        """
        stmt = (
            select(ReadBook)
            .where(ReadBook.student_id == student_id)
            .options(joinedload(ReadBook.book))
        )
        if status:
            st = status.strip().lower()
            if st in ("en curso", "in_progress", "active"):
                stmt = stmt.where(ReadBook.end_date.is_(None))
            elif st in ("finalizada", "cerrada", "finished", "completed"):
                stmt = stmt.where(ReadBook.end_date.isnot(None))

        if order_asc:
            stmt = stmt.order_by(ReadBook.start_date.asc(), ReadBook.id.asc())
        else:
            stmt = stmt.order_by(ReadBook.start_date.desc(), ReadBook.id.desc())

        return list(self.session.scalars(stmt).all())

    def get_by_book(
        self,
        book_id: uuid.UUID,
        status: Optional[str] = None,
        order_asc: bool = True,
    ) -> List[ReadBook]:
        """
        Obtiene las lecturas de un libro con precarga del alumno (BE-26 Escenario 2).
        Soporta filtro por estado ('en curso' o 'finalizada' - BE-26 Escenario 3).
        """
        stmt = (
            select(ReadBook)
            .where(ReadBook.book_id == book_id)
            .options(joinedload(ReadBook.student), joinedload(ReadBook.book))
        )
        if status:
            st = status.strip().lower()
            if st in ("en curso", "in_progress", "active"):
                stmt = stmt.where(ReadBook.end_date.is_(None))
            elif st in ("finalizada", "cerrada", "finished", "completed"):
                stmt = stmt.where(ReadBook.end_date.isnot(None))

        if order_asc:
            stmt = stmt.order_by(ReadBook.start_date.asc(), ReadBook.id.asc())
        else:
            stmt = stmt.order_by(ReadBook.start_date.desc(), ReadBook.id.desc())

        return list(self.session.scalars(stmt).all())

    def update(self, reading: ReadBook, commit: bool = True) -> ReadBook:
        """
        Guarda las modificaciones sobre una lectura existente.
        """
        try:
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_read_books_student_book_start" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe una lectura registrada para este alumno, libro y fecha de inicio")
            raise
        return reading
