from flask import Flask
from app.config import Config
from app.extensions import db, migrate, openapi_api
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
    migrate.init_app(application, db)
    openapi_api.init_app(application)

    # Registro de blueprints
    application.register_blueprint(health_bp, url_prefix="/api")

    # Registro de blueprints de API v1
    from app.api.v1.auth import auth_bp
    openapi_api.register_blueprint(auth_bp, url_prefix="/api/v1")

    # Registro condicional del endpoint de autenticación dev (BE-45)
    if application.config.get("DEV_AUTH_BYPASS"):
        from app.api.dev_auth import dev_auth_bp
        application.register_blueprint(dev_auth_bp, url_prefix="/api/dev")

    return application

