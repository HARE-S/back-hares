import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db


@pytest.fixture
def app():
    """
    Aplicación de pruebas contra PostgreSQL.

    Cada prueba recibe un esquema limpio. La base de test vive en tmpfs, así que
    crear y destruir tablas es rápido y nada persiste entre ejecuciones.
    """
    application = create_app(TestingConfig)

    with application.app_context():
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
