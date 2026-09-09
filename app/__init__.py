from flask import Flask, request
from app.config import Config, validate_config
from app.extensions import db, migrate
from app.api.health import health_bp
# Importar modelos para que SQLAlchemy los reconozca
from app import models  # noqa: F401


def create_app(config_class=Config):
    application = Flask(__name__)
    application.config.from_object(config_class)

    # Validaciones de arranque y salvaguardas de seguridad (BE-02 / BE-45)
    validate_config(config_class)

    # Inicialización de extensiones
    db.init_app(application)
    migrate.init_app(application, db)

    # Registro de blueprints
    application.register_blueprint(health_bp, url_prefix="/api")

    # Registro condicional del endpoint de autenticación dev (BE-45)
    if application.config.get("DEV_AUTH_BYPASS"):
        from app.api.dev_auth import dev_auth_bp
        application.register_blueprint(dev_auth_bp, url_prefix="/api/dev")

    # Configuración de CORS según el entorno (Escenarios 5 y 6 de BE-02)
    @application.after_request
    def handle_cors_headers(response):
        app_env = application.config.get("APP_ENV", "development")
        cors_origins = application.config.get("CORS_ORIGINS", [])

        # Escenario 5: En producción CORS NO se habilita
        if app_env == "production" or not cors_origins:
            return response

        # Escenario 6: En desarrollo lista explícita de orígenes y credenciales habilitadas (sin '*')
        origin = request.headers.get("Origin")
        if origin and origin in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Cookie"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

        return response

    return application
