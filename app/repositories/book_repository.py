import datetime
from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.book import Book
from app.models.enums import book_level_order_case, validate_book_level


class BookRepository:
    """
    Repositorio para el catálogo de libros.
    Proporciona consultas de ordenación pedagógica, filtrado por nivel y borrado lógico.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        book: str,
        level: str,
        copies_note: Optional[str] = None,
        sessions_note: Optional[str] = None,
        disabled_at=None,
    ) -> Book:
        """Crea y persiste un nuevo libro validando su nivel."""
        validated_level = validate_book_level(level)
        new_book = Book(
            book=book,
            level=validated_level,
            copies_note=copies_note,
            sessions_note=sessions_note,
            disabled_at=disabled_at,
        )
        self.session.add(new_book)
        self.session.commit()
        return new_book

    def get_by_title(self, title: str) -> Optional[Book]:
        """Obtiene un libro por su título exacto (insensible a mayúsculas)."""
        clean_title = str(title).strip()
        stmt = select(Book).where(func.lower(Book.book) == clean_title.lower())
        return self.session.scalars(stmt).first()

    def exists_by_title(self, title: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
        """Comprueba si ya existe un libro con ese título (opcionalmente excluyendo un ID)."""
        clean_title = str(title).strip()
        stmt = select(Book).where(func.lower(Book.book) == clean_title.lower())
        if exclude_id is not None:
            stmt = stmt.where(Book.id != exclude_id)
        return self.session.scalars(stmt).first() is not None

    def update(self, book: Book, commit: bool = True, **fields) -> Book:
        """Actualiza los campos de un libro y persiste los cambios."""
        for key, value in fields.items():
            if key in ("title", "book"):
                book.book = value
            elif key == "level" and value is not None:
                book.level = validate_book_level(value)
            elif hasattr(book, key):
                setattr(book, key, value)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return book


    def get_by_id(self, book_id) -> Optional[Book]:
        """Obtiene un libro por su ID."""
        return self.session.get(Book, book_id)

    def get_all(
        self,
        level: Optional[str] = None,
        order_by_level: bool = False,
        include_disabled: bool = False,
    ) -> List[Book]:
        """
        Consulta libros con soporte para:
        - Filtrado por nivel exacto (Escenario 4 de BE-15)
        - Ordenación según el orden pedagógico: 0 -> 0-I -> I -> I/II -> II (Escenario 3 de BE-15)
        - Exclusión por defecto de libros deshabilitados (BE-04)
        """
        stmt = select(Book)

        if level is not None:
            # Validamos el nivel solicitado antes de filtrar
            valid_level = validate_book_level(level)
            stmt = stmt.where(Book.level == valid_level)

        if not include_disabled:
            stmt = stmt.where(Book.disabled_at.is_(None))

        if order_by_level:
            # Ordenación pedagógica, seguida por título alfabéticamente
            stmt = stmt.order_by(book_level_order_case(Book.level), Book.book.asc())
        else:
            stmt = stmt.order_by(Book.book.asc())

        return list(self.session.scalars(stmt).all())

    def soft_delete(self, book_id) -> bool:
        """
        Da de baja lógica un libro estableciendo disabled_at con la fecha actual.
        No elimina la fila de la base de datos.
        Devuelve True si se deshabilitó, False si el libro no existe.
        """
        book = self.get_by_id(book_id)
        if not book:
            return False
        book.disabled_at = datetime.date.today()
        self.session.commit()
        return True
