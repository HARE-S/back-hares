from flask import Flask, request
from app.config import Config, validate_config
from app.extensions import db, api as openapi_api
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
    openapi_api.init_app(application)

    # Registro de blueprints
    application.register_blueprint(health_bp, url_prefix="/api")

    from app.api.v1.tests import tests_bp
    from app.api.v1.books import books_bp
    from app.api.v1.results import results_bp, single_results_bp
    from app.api.v1.sections import sections_bp
    from app.api.v1.readings import readings_bp, single_readings_bp
    from app.api.v1.imports import import_bp
    from app.api.v1.students import students_bp
    from app.api.v1.exports import exports_bp

    openapi_api.register_blueprint(tests_bp, url_prefix="/api/v1/tests")
    openapi_api.register_blueprint(books_bp, url_prefix="/api/v1/books")
    application.register_blueprint(books_bp, url_prefix="/api/books", name="books_direct")
    application.register_blueprint(students_bp, url_prefix="/api/v1/students", name="students_v1")
    application.register_blueprint(students_bp, url_prefix="/api/students", name="students_direct")
    application.register_blueprint(results_bp, url_prefix="/api/v1/students")
    application.register_blueprint(results_bp, url_prefix="/api/students", name="results_direct")
    application.register_blueprint(readings_bp, url_prefix="/api/v1/students", name="readings_v1")
    application.register_blueprint(readings_bp, url_prefix="/api/students", name="readings_direct")
    application.register_blueprint(single_readings_bp, url_prefix="/api/v1/readings", name="single_readings_v1")
    application.register_blueprint(single_readings_bp, url_prefix="/api/readings", name="single_readings_direct")
    application.register_blueprint(single_results_bp, url_prefix="/api/v1/results")
    application.register_blueprint(single_results_bp, url_prefix="/api/results", name="single_results_direct")
    application.register_blueprint(sections_bp, url_prefix="/api/v1/sections")
    application.register_blueprint(sections_bp, url_prefix="/api/sections", name="sections_direct")
    application.register_blueprint(import_bp, url_prefix="/api/v1/import")
    application.register_blueprint(exports_bp, url_prefix="/api/v1")
    application.register_blueprint(exports_bp, url_prefix="/api", name="exports_direct")


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
