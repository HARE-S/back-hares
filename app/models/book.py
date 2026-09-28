from typing import Optional
from sqlalchemy import event, func, select, text, UniqueConstraint
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import BOOK_LEVEL_ORDER, BOOK_LEVELS, validate_book_level
from app.utils.uuidv7 import uuidv7


class ReadBook(BaseModel):
    __tablename__ = "read_books"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    student_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("tests.id", ondelete="SET NULL"),
        nullable=True,
    )
    book_title = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="0", server_default="0")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    copies_note = db.Column(db.String(255), nullable=True)
    sessions_note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "book_title", "start_date",
            name="uq_read_books_student_title_start"
        ),
        db.Index("ix_read_books_student_id", "student_id"),
        db.Index("ix_read_books_test_id", "test_id"),
    )

    # Relaciones
    student = db.relationship("Student", back_populates="read_books")
    test = db.relationship("Test", back_populates="read_books", lazy="joined")
    results = db.relationship("Result", back_populates="read_book")

    def __init__(self, **kwargs):
        if "title" in kwargs and "book_title" not in kwargs:
            kwargs["book_title"] = kwargs.pop("title")
        if "book" in kwargs and "book_title" not in kwargs:
            kwargs["book_title"] = kwargs.pop("book")
        if "book_level" in kwargs and "level" not in kwargs:
            kwargs["level"] = kwargs.pop("book_level")
        if "test" in kwargs and kwargs.get("test") and "book_title" not in kwargs:
            kwargs["book_title"] = kwargs["test"].name
            if "level" not in kwargs and kwargs["test"].test_letter in BOOK_LEVEL_ORDER:
                kwargs["level"] = kwargs["test"].test_letter
        kwargs.setdefault("book_title", "Libro de lectura")
        kwargs.setdefault("level", "0")
        super().__init__(**kwargs)

    @validates("level")
    def validate_level(self, key, value):
        return validate_book_level(value)

    # Aliases de compatibilidad
    @hybrid_property
    def title(self) -> str:
        return self.book_title or (self.test.name if self.test else "")

    @title.setter
    def title(self, value: str):
        self.book_title = value

    @title.expression
    def title(cls):
        return cls.book_title

    @hybrid_property
    def book(self) -> str:
        return self.book_title or (self.test.name if self.test else "")

    @book.setter
    def book(self, value: str):
        self.book_title = value

    @book.expression
    def book(cls):
        return cls.book_title

    @property
    def test_code(self) -> str:
        return self.test.code if self.test else ""

    @property
    def book_level(self) -> str:
        return self.level

    @property
    def level_order(self) -> int:
        return BOOK_LEVEL_ORDER.get(self.level, 99)

    @property
    def status(self) -> str:
        return "finalizada" if self.end_date else "en curso"

    @property
    def duration_days(self) -> Optional[int]:
        """
        Días transcurridos entre inicio y fin de lectura.
        Si start_date == end_date (autogenerada al evaluar), se devuelve None
        para no falsear las estadísticas pedagógicas del centro.
        """
        if self.start_date and self.end_date and self.end_date > self.start_date:
            return (self.end_date - self.start_date).days
        return None

    def to_dict(self):
        data = super().to_dict()
        data["test_id"] = str(self.test_id) if self.test_id else None
        data["test_code"] = self.test_code
        data["book_title"] = self.book_title
        data["title"] = self.title
        data["book"] = self.book
        data["book_level"] = self.level
        data["level"] = self.level
        data["status"] = self.status
        data["duration_days"] = self.duration_days
        data["copies_note"] = self.copies_note
        data["sessions_note"] = self.sessions_note
        return data

    def __repr__(self):
        return (
            f"<ReadBook id={self.id} student_id={self.student_id} "
            f"title='{self.book_title}' level='{self.level}' start={self.start_date}>"
        )


@event.listens_for(ReadBook, "before_insert")
def _read_book_before_insert(mapper, connection, target):
    if (not target.book_title or target.book_title == "Libro de lectura") and target.test_id:
        from app.models.test import Test
        if getattr(target, "test", None) is not None:
            target.book_title = target.test.name
            if (not target.level or target.level == "0") and target.test.test_letter in BOOK_LEVEL_ORDER:
                target.level = target.test.test_letter
        else:
            res = connection.execute(
                select(Test.name, Test.test_letter).where(Test.id == target.test_id)
            ).first()
            if res:
                target.book_title = res[0]
                if (not target.level or target.level == "0") and res[1] in BOOK_LEVEL_ORDER:
                    target.level = res[1]


# Alias para retrocompatibilidad
ReadedBook = ReadBook
