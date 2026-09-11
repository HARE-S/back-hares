import datetime

from sqlalchemy import text

from app.extensions import db
from app.models.base import BaseModel
from app.utils.uuidv7 import uuidv7


class ImportReport(BaseModel):
    """Informe de errores de una importación de alumnado (BE-08).

    Persiste el resultado de cada importación de fichero: recuentos globales
    y la lista de filas rechazadas con línea, columna y motivo, de forma que
    el administrador pueda descargarla desde el API aunque la importación
    se ejecutara desde el contenedor `import`.
    """

    __tablename__ = "import_reports"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    total = db.Column(db.Integer, nullable=False, default=0)
    processed = db.Column(db.Integer, nullable=False, default=0)
    errors = db.Column(db.Integer, nullable=False, default=0)
    error_details = db.Column(db.JSON, nullable=False, default=list)

    def __repr__(self):
        return f"<ImportReport id={self.id} total={self.total} errors={self.errors}>"