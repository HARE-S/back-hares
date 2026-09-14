"""Tests para autenticación local (BE-XX)."""

import pytest
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.core.exceptions import ValidationError, UnauthorizedError, ConflictError


def test_user_password_hashing(app, db_session):
    """Verificar que las contraseñas se hashean correctamente."""
    user = User(
        email="test@grupopenascal.com",
        name="Test",
        lastname="User",
        area="Fontanería",
    )
    user.set_password("mysecurepass123")
    assert user.password_hash != "mysecurepass123"
    assert user.verify_password("mysecurepass123")
    assert not user.verify_password("wrongpassword")


def test_register_user(app, db_session):
    """Registrar un nuevo usuario."""
    service = AuthService(db_session)
    result = service.register(
        email="newuser@grupopenascal.com",
        name="John",
        lastname="Doe",
        password="securepass123",
        area="Electricidad",
    )

    assert result["email"] == "newuser@grupopenascal.com"
    assert result["name"] == "John"
    assert result["lastname"] == "Doe"
    assert result["area"] == "Electricidad"
    assert result["role"] == "tutor"
    assert "password_hash" not in result


def test_register_invalid_domain(app, db_session):
    """No se puede registrar con dominio incorrecto."""
    service = AuthService(db_session)
    with pytest.raises(ValidationError) as exc_info:
        service.register(
            email="user@example.com",
            name="Test",
            lastname="User",
            password="securepass123",
            area="Fontanería",
        )
    assert "@grupopenascal.com" in str(exc_info.value)


def test_register_duplicate_email(app, db_session):
    """No se puede registrar con email duplicado."""
    service = AuthService(db_session)
    service.register(
        email="duplicate@grupopenascal.com",
        name="First",
        lastname="User",
        password="pass123",
        area="Fontanería",
    )

    with pytest.raises(ConflictError):
        service.register(
            email="duplicate@grupopenascal.com",
            name="Second",
            lastname="User",
            password="pass456",
            area="Fontanería",
        )


def test_register_short_password(app, db_session):
    """Contraseña demasiado corta no se acepta."""
    service = AuthService(db_session)
    with pytest.raises(ValidationError):
        service.register(
            email="test@grupopenascal.com",
            name="Test",
            lastname="User",
            password="short",
            area="Fontanería",
        )


def test_login_success(app, db_session):
    """Login exitoso retorna token JWT."""
    service = AuthService(db_session)
    service.register(
        email="login@grupopenascal.com",
        name="Login",
        lastname="User",
        password="validpass123",
        area="Informática",
    )

    result = service.login(
        email="login@grupopenascal.com",
        password="validpass123",
    )

    assert "access_token" in result
    assert result["token_type"] == "Bearer"
    assert result["user"]["email"] == "login@grupopenascal.com"
    assert result["user"]["area"] == "Informática"


def test_login_wrong_password(app, db_session):
    """Login con contraseña incorrecta falla."""
    service = AuthService(db_session)
    service.register(
        email="login@grupopenascal.com",
        name="Login",
        lastname="User",
        password="validpass123",
        area="Informática",
    )

    with pytest.raises(UnauthorizedError):
        service.login(
            email="login@grupopenascal.com",
            password="wrongpass",
        )


def test_login_nonexistent_user(app, db_session):
    """Login con usuario inexistente falla."""
    service = AuthService(db_session)
    with pytest.raises(UnauthorizedError):
        service.login(
            email="nonexistent@grupopenascal.com",
            password="anypass",
        )


def test_login_inactive_user(app, db_session):
    """Usuario inactivo no puede loguearse."""
    service = AuthService(db_session)
    result = service.register(
        email="inactive@grupopenascal.com",
        name="Inactive",
        lastname="User",
        password="validpass123",
        area="Fontanería",
    )

    # Desactivar usuario manualmente
    user = db_session.query(User).filter(User.email == "inactive@grupopenascal.com").first()
    user.is_active = False
    db_session.commit()

    with pytest.raises(UnauthorizedError):
        service.login(
            email="inactive@grupopenascal.com",
            password="validpass123",
        )


def test_token_verification(app, db_session):
    """Verificar token JWT."""
    service = AuthService(db_session)
    service.register(
        email="token@grupopenascal.com",
        name="Token",
        lastname="User",
        password="validpass123",
        area="Hostelería",
    )

    login_result = service.login(
        email="token@grupopenascal.com",
        password="validpass123",
    )

    token = login_result["access_token"]
    payload = service.verify_token(token)

    assert payload["email"] == "token@grupopenascal.com"
    assert payload["role"] == "tutor"
    assert payload["area"] == "Hostelería"
