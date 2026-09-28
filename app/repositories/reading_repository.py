import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import ConflictError
from app.models.book import ReadBook
from app.models.test import Test


class ReadingRepository:
    """
    Repositorio para persistencia y consulta de asignaciones y lecturas de libros (Bloque B).
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        student_id: uuid.UUID,
        test_id: Optional[uuid.UUID] = None,
        book_title: Optional[str] = None,
        level: Optional[str] = None,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        copies_note: Optional[str] = None,
        sessions_note: Optional[str] = None,
        commit: bool = True,
    ) -> ReadBook:
        """
        Crea y persiste una nueva lectura vinculada a una prueba/libro (BE-23).
        Soporta resolución automática de test_id a partir de book_title y nivel.
        Controla colisión de clave única (student_id, test_id, start_date) y lanza ConflictError.
        """
        if test_id is None and book_title:
            title_clean = book_title.strip()
            test = self.session.scalars(
                select(Test).where(
                    (func.lower(Test.name) == title_clean.lower()) |
                    (func.lower(Test.code) == title_clean.lower())
                )
            ).first()
            if not test:
                test = Test(
                    code=f"BOOK-{uuid.uuid4().hex[:8].upper()}",
                    name=title_clean,
                    test_letter=level if level else "0",
                    words=100,
                    course=1,
                    type="Lectura",
                )
                self.session.add(test)
                self.session.flush()
            elif level and not test.test_letter:
                test.test_letter = level
            test_id = test.id

        if start_date is None:
            start_date = datetime.date.today()

        reading = ReadBook(
            student_id=student_id,
            test_id=test_id,
            start_date=start_date,
            end_date=end_date,
            copies_note=copies_note,
            sessions_note=sessions_note,
        )
        if level:
            reading.level = level
        try:
            self.session.add(reading)
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_read_books_student_test_start" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe una lectura registrada para este alumno, libro y fecha de inicio")
            raise
        return reading

    def exists_duplicate(
        self,
        student_id: uuid.UUID,
        test_id: uuid.UUID,
        start_date: datetime.date,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Comprueba si ya existe una lectura para el mismo alumno, prueba y fecha de inicio exacta.
        """
        stmt = select(ReadBook).where(
            ReadBook.student_id == student_id,
            ReadBook.test_id == test_id,
            ReadBook.start_date == start_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(ReadBook.id != exclude_id)
        return self.session.scalars(stmt).first() is not None

    def get_by_id(self, reading_id: uuid.UUID) -> Optional[ReadBook]:
        """
        Obtiene una lectura por su ID con carga ansiosa de relación student y test.
        """
        from app.models.student import Student
        stmt = (
            select(ReadBook)
            .where(ReadBook.id == reading_id)
            .options(
                joinedload(ReadBook.student).joinedload(Student.student_sections),
                joinedload(ReadBook.test),
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
        Obtiene el historial de lecturas de un alumno.
        Soporta filtro por estado ('en curso' o 'finalizada').
        """
        stmt = (
            select(ReadBook)
            .where(ReadBook.student_id == student_id)
            .options(joinedload(ReadBook.test))
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

    def get_by_test(
        self,
        test_id: uuid.UUID,
        status: Optional[str] = None,
        order_asc: bool = True,
    ) -> List[ReadBook]:
        """
        Obtiene las lecturas de una prueba específica por su ID.
        """
        stmt = (
            select(ReadBook)
            .where(ReadBook.test_id == test_id)
            .options(joinedload(ReadBook.student), joinedload(ReadBook.test))
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
        book_identifier: Union[str, uuid.UUID],
        status: Optional[str] = None,
        order_asc: bool = True,
    ) -> List[ReadBook]:
        """
        Obtiene las lecturas de un libro por su título, código o UUID de prueba.
        """
        stmt = (
            select(ReadBook)
            .join(ReadBook.test)
            .options(joinedload(ReadBook.student), joinedload(ReadBook.test))
        )

        parsed_uuid = None
        if isinstance(book_identifier, uuid.UUID):
            parsed_uuid = book_identifier
        else:
            try:
                parsed_uuid = uuid.UUID(str(book_identifier).strip())
            except (ValueError, TypeError, AttributeError):
                parsed_uuid = None

        if parsed_uuid:
            stmt = stmt.where(ReadBook.test_id == parsed_uuid)
        else:
            term = str(book_identifier).strip().lower()
            stmt = stmt.where(
                (func.lower(Test.name) == term) | (func.lower(Test.code) == term)
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
            if "uq_read_books_student_test_start" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe una lectura registrada para este alumno, libro y fecha de inicio")
            raise
        return reading
