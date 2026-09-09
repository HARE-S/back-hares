import pytest
from flask import Flask, jsonify
from app import create_app
from app.auth import get_current_user, require_role
from app.config import Config


class DevAuthConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionBypassConfig(Config):
    TESTING = True
    APP_ENV = "production"
    DEV_AUTH_BYPASS = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class NormalConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_dev_auth_disabled_by_default_scenario_2():
    """
    Escenario 2: Sin DEV_AUTH_BYPASS activo, el endpoint /api/dev/session no existe (404).
    """
    app = create_app(NormalConfig)
    client = app.test_client()

    response = client.post("/api/dev/session", json={"role": "tutor"})
    assert response.status_code == 404


def test_dev_auth_incompatible_with_production_scenario_3():
    """
    Escenario 3: Dado un entorno con APP_ENV=production y DEV_AUTH_BYPASS=true,
    la aplicación se niega a arrancar lanzando RuntimeError.
    """
    with pytest.raises(RuntimeError) as exc_info:
        create_app(ProductionBypassConfig)

    assert "FATAL: DEV_AUTH_BYPASS no puede estar activo en entorno de producción" in str(
        exc_info.value
    )


def test_dev_auth_session_simulation_scenario_1():
    """
    Escenario 1: Con DEV_AUTH_BYPASS activo, se crea sesión simulada y se puede cambiar el rol.
    """
    app = create_app(DevAuthConfig)
    client = app.test_client()

    # Cambiar rol a coordinador
    response = client.post("/api/dev/session", json={"role": "coordinador"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["role"] == "coordinador"
    assert data["user"]["is_dev"] is True


def test_require_role_decorator_authorization():
    """
    Pruebas del decorador @require_role (*allowed_roles) (Contrato 2).
    """
    app = create_app(DevAuthConfig)

    # Crear una ruta de prueba temporal protegida con @require_role
    @app.route("/api/test-protected")
    @require_role("tutor", "coordinador")
    def protected_endpoint():
        user = get_current_user()
        return jsonify({"message": "OK", "user": user}), 200

    client = app.test_client()

    # 1. Por defecto en dev bypass es 'tutor' -> Acceso concedido (200 OK)
    res_tutor = client.get("/api/test-protected")
    assert res_tutor.status_code == 200
    assert res_tutor.get_json()["message"] == "OK"

    # 2. Cambiar rol a 'pendiente' -> Acceso denegado (403 Forbidden)
    client.post("/api/dev/session", json={"role": "pendiente"})
    res_forbidden = client.get("/api/test-protected")
    assert res_forbidden.status_code == 403
    assert "Acceso denegado" in res_forbidden.get_json()["message"]

    # 3. Sin bypass y sin sesión -> 401 Unauthorized
    app_no_auth = create_app(NormalConfig)

    @app_no_auth.route("/api/test-protected")
    @require_role("tutor")
    def protected_endpoint_no_auth():
        return jsonify({"message": "OK"}), 200

    client_no_auth = app_no_auth.test_client()
    res_unauth = client_no_auth.get("/api/test-protected")
    assert res_unauth.status_code == 401
    assert res_unauth.get_json()["error"] == "UNAUTHORIZED"
