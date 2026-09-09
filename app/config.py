import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-hares-key")
    
    # Entorno y autenticación en desarrollo
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    DEV_AUTH_BYPASS = os.getenv("DEV_AUTH_BYPASS", "false").lower() in ("true", "1", "yes")
    
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


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )

