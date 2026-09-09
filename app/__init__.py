from flask import Flask
from app.config import Config
from app.extensions import db, migrate
from app.api.health import health_bp
# Importar modelos para que SQLAlchemy los reconozca
from app import models  # noqa: F401


def create_app(config_class=Config):
    application = Flask(__name__)
    application.config.from_object(config_class)

    # Inicialización de extensiones
    db.init_app(application)
    migrate.init_app(application, db)

    # Registro de funciones de compatibilidad para dialecto SQLite
    with application.app_context():
        if db.engine.dialect.name == "sqlite":
            from sqlalchemy import event
            @event.listens_for(db.engine, "connect")
            def set_sqlite_functions(dbapi_connection, connection_record):
                if hasattr(dbapi_connection, "create_function"):
                    from app.utils.uuidv7 import uuidv7
                    dbapi_connection.create_function("uuidv7", 0, lambda: str(uuidv7()))
                    dbapi_connection.create_function(
                        "translate",
                        3,
                        lambda text, from_chars, to_chars: str(text).translate(str.maketrans(from_chars, to_chars)) if text is not None else None,
                    )


    # Registro de blueprints
    application.register_blueprint(health_bp, url_prefix="/api")

    from app.api.v1.tests import tests_bp
    from app.api.v1.books import books_bp

    application.register_blueprint(tests_bp, url_prefix="/api/v1/tests")
    application.register_blueprint(books_bp, url_prefix="/api/v1/books")
    application.register_blueprint(books_bp, url_prefix="/api/books", name="books_direct")

    return application
