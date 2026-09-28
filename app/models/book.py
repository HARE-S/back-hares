from sqlalchemy import func, select, text, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import BOOK_LEVEL_ORDER, validate_book_level
from app.models.test import Test
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
        db.ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    copies_note = db.Column(db.String(255), nullable=True)
    sessions_note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "test_id", "start_date",
            name="uq_read_books_student_test_start"
        ),
        db.Index("ix_read_books_student_id", "student_id"),
        db.Index("ix_read_books_test_id", "test_id"),
    )

    # Relaciones
    student = db.relationship("Student", back_populates="read_books")
    test = db.relationship("Test", back_populates="read_books", lazy="joined")

    @hybrid_property
    def title(self) -> str:
        if self.test and self.test.name:
            return self.test.name
        return getattr(self, "_book_title", "")

    @title.setter
    def title(self, value: str):
        self._book_title = value

    @title.expression
    def title(cls):
        return select(Test.name).where(Test.id == cls.test_id).scalar_subquery()

    @hybrid_property
    def book_title(self) -> str:
        return self.title

    @book_title.setter
    def book_title(self, value: str):
        self._book_title = value

    @book_title.expression
    def book_title(cls):
        return select(Test.name).where(Test.id == cls.test_id).scalar_subquery()

    @hybrid_property
    def book(self) -> str:
        return self.title

    @hybrid_property
    def test_code(self) -> str:
        return self.test.code if self.test else ""

    @test_code.expression
    def test_code(cls):
        return select(Test.code).where(Test.id == cls.test_id).scalar_subquery()

    @hybrid_property
    def level(self) -> str:
        if self.test:
            if self.test.test_letter:
                return self.test.test_letter
            if self.test.course is not None:
                return str(self.test.course)
        return getattr(self, "_level", "0")

    @level.setter
    def level(self, value: str):
        self._level = validate_book_level(value)

    @level.expression
    def level(cls):
        return func.coalesce(
            select(Test.test_letter).where(Test.id == cls.test_id).scalar_subquery(),
            func.cast(select(Test.course).where(Test.id == cls.test_id).scalar_subquery(), db.String),
            "0",
        )

    @property
    def level_order(self) -> int:
        return BOOK_LEVEL_ORDER.get(self.level, 99)

    @property
    def status(self) -> str:
        return "finalizada" if self.end_date else "en_curso"

    def to_dict(self):
        data = super().to_dict()
        data["test_id"] = str(self.test_id) if self.test_id else None
        data["test_code"] = self.test_code
        data["title"] = self.title
        data["book"] = self.title
        data["book_title"] = self.title
        data["book_level"] = self.level
        data["level"] = self.level
        data["status"] = self.status
        data["copies_note"] = self.copies_note
        data["sessions_note"] = self.sessions_note
        return data

    def __repr__(self):
        return (
            f"<ReadBook id={self.id} student_id={self.student_id} "
            f"test_id={self.test_id} title='{self.title}' start={self.start_date}>"
        )


# Alias para retrocompatibilidad
ReadedBook = ReadBook
