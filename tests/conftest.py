import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db


@pytest.fixture
def app():
    """
    Aplicación de pruebas.

    Híbrido: SQLite persistente en desarrollo local (rápido, sin Docker),
    PostgreSQL en CI/CD (rigurosamente correcto).

    Advertencia: SQLite no aplica uuidv7() ni restricciones UNIQUE compuestas.
    Las pruebas de BE-19 y BE-25 pasan sin comprobar nada real si corren contra SQLite.
    """
    application = create_app(TestingConfig)

    with application.app_context():
        db_uri = str(application.config["SQLALCHEMY_DATABASE_URI"])
        if "sqlite" in db_uri.lower():
            print("\n⚠️  Tests contra SQLite: restricciones UNIQUE no se verifican.")
            print("   Para CI/CD usar: TEST_DATABASE_URL=postgresql://...")

        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session
