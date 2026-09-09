import pytest
from flask import Flask
from app import create_app
from app.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, validate_config


def test_full_config_loading_scenario_1():
    """Escenario 1: Lee la configuración del entorno correctamente."""
    app = create_app(DevelopmentConfig)
    assert app.config["APP_ENV"] == "development"
    assert app.config["DEV_AUTH_BYPASS"] is True
    assert "postgresql://" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_missing_secret_key_scenario_2():
    """Escenario 2: Dado un entorno sin SECRET_KEY definida, se niega a arrancar."""
    class InvalidConfig(Config):
        SECRET_KEY = ""

    with pytest.raises(RuntimeError) as exc_info:
        create_app(InvalidConfig)

    assert "SECRET_KEY es obligatoria" in str(exc_info.value)


def test_dangerous_combination_scenario_3():
    """Escenario 3: APP_ENV=production y DEV_AUTH_BYPASS=true -> Falla al arrancar."""
    class DangerousConfig(Config):
        APP_ENV = "production"
        DEV_AUTH_BYPASS = True
        SECRET_KEY = "a" * 32

    with pytest.raises(RuntimeError) as exc_info:
        create_app(DangerousConfig)

    assert "DEV_AUTH_BYPASS no puede estar activo en entorno de producción" in str(exc_info.value)


def test_insufficient_secret_key_scenario_4():
    """Escenario 4: Dado un SECRET_KEY de menos de 32 caracteres en producción, se niega a arrancar."""
    class ShortKeyProdConfig(Config):
        APP_ENV = "production"
        DEV_AUTH_BYPASS = False
        SECRET_KEY = "short-key-123"

    with pytest.raises(RuntimeError) as exc_info:
        create_app(ShortKeyProdConfig)

    assert "SECRET_KEY debe tener al menos 32 caracteres" in str(exc_info.value)


def test_cors_disabled_in_production_scenario_5():
    """Escenario 5: En producción CORS no se habilita."""
    class ProdConfig(ProductionConfig):
        SECRET_KEY = "a" * 32

    app = create_app(ProdConfig)
    client = app.test_client()

    response = client.get("/api/health", headers={"Origin": "http://evil-site.com"})
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_with_explicit_origins_in_dev_scenario_6():
    """Escenario 6: CORS en desarrollo habilita lista explícita de orígenes y credenciales (sin wildcard '*')."""
    class DevCorsConfig(DevelopmentConfig):
        CORS_ORIGINS = ["http://localhost:5173"]

    app = create_app(DevCorsConfig)
    client = app.test_client()

    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"
    assert response.headers.get("Access-Control-Allow-Origin") != "*"


def test_invalid_session_type_scenario_7():
    """Escenario 7: SESSION_TYPE no apuntando a servidor se niega a arrancar."""
    class BadSessionConfig(Config):
        SESSION_TYPE = "invalid_type"

    with pytest.raises(RuntimeError) as exc_info:
        create_app(BadSessionConfig)

    assert "SESSION_TYPE debe apuntar a un almacenamiento persistente" in str(exc_info.value)
