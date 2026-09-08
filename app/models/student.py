import datetime
from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class Student(BaseModel):
    __tablename__ = "students"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    name = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    academic_status = db.Column(db.String(100), nullable=True)
    sector = db.Column(db.String(100), nullable=True)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = datetime.date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def to_dict(self):
        data = super().to_dict()
        data["age"] = self.age
        return data

    # Relaciones
    student_sections = db.relationship(
        "StudentSection",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    results = db.relationship(
        "Result",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    readed_books = db.relationship(
        "ReadedBook",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Student id={self.id} name='{self.name}'>"


class StudentSection(BaseModel):
    __tablename__ = "student_sections"

    student_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    section_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("sections.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    created_on = db.Column(
        db.Date,
        nullable=False,
        default=datetime.date.today,
        server_default=text("CURRENT_DATE"),
    )

    # Relaciones
    student = db.relationship("Student", back_populates="student_sections")
    section = db.relationship("Section", back_populates="student_sections")

    def __repr__(self):
        return f"<StudentSection student_id={self.student_id} section_id={self.section_id}>"
