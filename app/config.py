import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_bool_env(var_name: str, default: bool = False) -> bool:
    val = os.getenv(var_name)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


class Config:
    """Configuración base de la aplicación (BE-02)."""
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-hares-penascal-2026-min-32-chars")
    DEV_AUTH_BYPASS = _get_bool_env("DEV_AUTH_BYPASS", False)

    # Base de datos PostgreSQL
    DB_USER = os.getenv("POSTGRES_USER", "hares_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "hares_pass")
    DB_HOST = os.getenv("POSTGRES_HOST", "db")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "hares_db")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    CORS_SUPPORTS_CREDENTIALS = True

    # Persistencia de Sesión en Servidor (US-45 / BE-02)
    SESSION_TYPE = os.getenv("SESSION_TYPE", "sqlalchemy").lower()

    # OpenAPI / flask-smorest (BE-48)
    API_TITLE = "Hares API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo."""
    DEBUG = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = _get_bool_env("DEV_AUTH_BYPASS", True)


class TestingConfig(Config):
    """
    Configuración de pruebas.

    Las pruebas corren SIEMPRE contra PostgreSQL. El esquema usa uuidv7() y
    restricciones UNIQUE compuestas que SQLite no aplica igual: contra SQLite,
    las pruebas de BE-19 y BE-25 pasan sin comprobar nada.
    """
    TESTING = True
    APP_ENV = "testing"
    DEV_AUTH_BYPASS = _get_bool_env("DEV_AUTH_BYPASS", True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_password@db-test:5432/hares_test",
    )


class ProductionConfig(Config):
    """Configuración para entorno de producción en Google Cloud / Docker."""
    DEBUG = False
    APP_ENV = "production"
    DEV_AUTH_BYPASS = False
    # En producción CORS se deshabilita porque el proxy sirve interfaz y API en el mismo origen
    CORS_ORIGINS = []
    # OpenAPI: desactivar interfaz navegable en producción (BE-48, Escenario 2)
    OPENAPI_URL_PREFIX = None


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def validate_config(app_config) -> None:
    """
    Valida la configuración de la aplicación al arrancar (BE-02).
    Lanza RuntimeError con mensaje claro ante cualquier fallo o salvaguarda violada.
    """
    app_env = getattr(app_config, "APP_ENV", "development") or "development"
    app_env = str(app_env).lower()
    secret_key = getattr(app_config, "SECRET_KEY", None)
    dev_bypass = getattr(app_config, "DEV_AUTH_BYPASS", False)
    session_type = getattr(app_config, "SESSION_TYPE", "sqlalchemy")

    # Escenario 2: Falta SECRET_KEY obligatoria
    if not secret_key:
        raise RuntimeError("FATAL: La variable de entorno SECRET_KEY es obligatoria y no está definida.")

    # Escenario 3: Combinación peligrosa (production + DEV_AUTH_BYPASS=true)
    if app_env == "production" and dev_bypass:
        raise RuntimeError("FATAL: DEV_AUTH_BYPASS no puede estar activo en entorno de producción (APP_ENV=production).")

    # Escenario 4: Secreto de sesión insuficiente en producción (< 32 caracteres)
    if app_env == "production" and len(str(secret_key)) < 32:
        raise RuntimeError("FATAL: La variable SECRET_KEY debe tener al menos 32 caracteres en entorno de producción.")

    # Escenario 7: Almacenamiento de sesión debe estar en servidor
    valid_session_types = ("sqlalchemy", "redis", "filesystem", "server")
    if str(session_type).lower() not in valid_session_types:
        raise RuntimeError("FATAL: SESSION_TYPE debe apuntar a un almacenamiento persistente en servidor (ej. sqlalchemy).")

    # Salvaguarda del entorno de pruebas.
    if app_env == "testing":
        db_uri = str(getattr(app_config, "SQLALCHEMY_DATABASE_URI", ""))
        if "sqlite" in db_uri.lower():
            raise RuntimeError(
                "FATAL: las pruebas no pueden ejecutarse contra SQLite. "
                "Levanta db-test: docker compose --profile test up -d db-test"
            )
        if "test" not in db_uri.lower():
            raise RuntimeError(
                f"FATAL: la base de pruebas debe contener 'test' en su URL. Recibida: {db_uri}"
            )
