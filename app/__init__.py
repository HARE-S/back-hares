from flask import Flask
from app.config import Config
from app.extensions import db
from app.api.health import health_bp
# Importar modelos para que SQLAlchemy los reconozca
from app import models  # noqa: F401


def create_app(config_class=Config):
    application = Flask(__name__)
    application.config.from_object(config_class)

    # Salvaguarda de seguridad para BE-45: no permitir DEV_AUTH_BYPASS en producción
    if application.config.get("APP_ENV") == "production" and application.config.get("DEV_AUTH_BYPASS"):
        raise RuntimeError("FATAL: DEV_AUTH_BYPASS no puede estar activo en entorno de producción (APP_ENV=production).")

    # Inicialización de extensiones
    db.init_app(application)

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

    # Registro condicional del endpoint de autenticación dev (BE-45)
    if application.config.get("DEV_AUTH_BYPASS"):
        from app.api.dev_auth import dev_auth_bp
        application.register_blueprint(dev_auth_bp, url_prefix="/api/dev")

    return application

