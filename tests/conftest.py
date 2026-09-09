import pytest
from sqlalchemy import event
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.utils.uuidv7 import uuidv7


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        # Para compatibilidad con SQLite en tests, registramos la función uuidv7 si aplica
        if db.engine.dialect.name == "sqlite":
            @event.listens_for(db.engine, "connect")
            def set_sqlite_functions(dbapi_connection, connection_record):
                if hasattr(dbapi_connection, "create_function"):
                    dbapi_connection.create_function("uuidv7", 0, lambda: str(uuidv7()))

        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session
