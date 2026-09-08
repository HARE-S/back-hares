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

    # Registro de blueprints
    application.register_blueprint(health_bp, url_prefix="/api")

    return application
