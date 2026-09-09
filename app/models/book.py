from sqlalchemy import text
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
    level = db.Column(db.Integer, nullable=False)
    disabled_at = db.Column(db.Date, nullable=True)

    # Relaciones
    readed_books = db.relationship(
        "ReadedBook",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Book id={self.id} book='{self.book}' level={self.level}>"


class ReadedBook(BaseModel):
    __tablename__ = "readed_books"

    student_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    book_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    # Relaciones
    student = db.relationship("Student", back_populates="readed_books")
    book = db.relationship("Book", back_populates="readed_books")

    def __repr__(self):
        return (
            f"<ReadedBook student_id={self.student_id} "
            f"book_id={self.book_id} start={self.start_date}>"
        )
