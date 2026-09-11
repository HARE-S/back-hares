import os
import pytest
from sqlalchemy import text
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.utils.uuidv7 import SQL_CREATE_UUIDV7_FUNCTION

KEEP_DATA = os.getenv("KEEP_TEST_DATA", "").lower() in ("1", "true", "yes")


@pytest.fixture
def app():
    """
    Aplicación de pruebas sobre PostgreSQL.

    Con KEEP_TEST_DATA=1 las tablas no se destruyen al terminar, para poder
    inspeccionar el estado con pgAdmin después de un fallo.
    """
    application = create_app(TestingConfig)

    with application.app_context():
        db_uri = str(application.config.get("SQLALCHEMY_DATABASE_URI", ""))
        if "postgresql" in db_uri.lower():
            # uuidv7() no es nativa en PostgreSQL 15: la registra el proyecto.
            db.session.execute(text(SQL_CREATE_UUIDV7_FUNCTION))
            db.session.commit()
        elif "sqlite" in db_uri.lower():
            print("\n⚠️  Tests contra SQLite: restricciones UNIQUE no se verifican.")
            print("   Para CI/CD usar: TEST_DATABASE_URL=postgresql://...")

        db.create_all()
        yield application
        db.session.remove()
        if not KEEP_DATA:
            db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session
