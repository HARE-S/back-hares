from sqlalchemy import text, UniqueConstraint
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class Book(BaseModel):
    __tablename__ = "books"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    book = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="0")
    disabled_at = db.Column(db.Date, nullable=True)

    # Relaciones
    read_books = db.relationship(
        "ReadBook",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Book id={self.id} book='{self.book}' level={self.level}>"


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
    book_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "book_id", "start_date",
                         name="uq_read_books_student_book_start"),
        db.Index("ix_read_books_student_id", "student_id"),
    )

    # Relaciones
    student = db.relationship("Student", back_populates="read_books")
    book = db.relationship("Book", back_populates="read_books")

    def __repr__(self):
        return (
            f"<ReadBook id={self.id} student_id={self.student_id} "
            f"book_id={self.book_id} start={self.start_date}>"
        )
