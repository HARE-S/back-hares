from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class Test(BaseModel):
    __tablename__ = "tests"
    __test__ = False  # Evitar que pytest intente recopilar este modelo como clase de test

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    code = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    words = db.Column(db.Integer, nullable=False, default=0)
    disabled_at = db.Column(db.Date, nullable=True)

    # Relaciones
    results = db.relationship(
        "Result",
        back_populates="test",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Test id={self.id} code='{self.code}' name='{self.name}'>"


class Result(BaseModel):
    __tablename__ = "results"

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
    section_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Integer, nullable=False, default=0)
    successes = db.Column(db.Integer, nullable=False, default=0)
    mistakes = db.Column(db.Integer, nullable=False, default=0)

    # Relaciones
    student = db.relationship("Student", back_populates="results")
    section = db.relationship("Section", back_populates="results")
    test = db.relationship("Test", back_populates="results")

    # Índice opcional para búsquedas y ordenación de progresión
    __table_args__ = (
        db.Index("ix_results_student_test_date", "student_id", "test_date"),
    )

    def __repr__(self):
        return (
            f"<Result id={self.id} student_id={self.student_id} "
            f"test_id={self.test_id} date={self.test_date}>"
        )
