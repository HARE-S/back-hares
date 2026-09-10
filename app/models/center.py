from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class Center(BaseModel):
    __tablename__ = "centers"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    external_id = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    disabled_at = db.Column(db.Date, nullable=True)

    # Relaciones
    sections = db.relationship(
        "Section",
        back_populates="center",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Center id={self.id} name='{self.name}'>"


class Section(BaseModel):
    __tablename__ = "sections"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    center_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("centers.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_id = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    academic_year = db.Column(db.String(20), nullable=True)
    disabled_at = db.Column(db.Date, nullable=True)

    # Relaciones
    center = db.relationship("Center", back_populates="sections")
    student_sections = db.relationship(
        "StudentSection",
        back_populates="section",
        cascade="all, delete-orphan",
        lazy="select",
    )
    results = db.relationship(
        "Result",
        back_populates="section",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Section id={self.id} name='{self.name}' center_id={self.center_id}>"
