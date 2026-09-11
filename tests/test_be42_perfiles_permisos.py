"""Tests para BE-42: Perfiles de permisos."""

import pytest
from app.models.user import User, UserRole


def test_user_role_enum():
    """Verificar que los roles válidos están definidos."""
    assert UserRole.PENDING.value == "pendiente"
    assert UserRole.TUTOR.value == "tutor"
    assert UserRole.COORDINATOR.value == "coordinador"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.DIRECTOR.value == "director"


def test_user_creation(app, db_session):
    """Crear un usuario con rol."""
    user = User(
        email="test@example.com",
        name="Test User",
        role=UserRole.TUTOR.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter(User.email == "test@example.com").first()
    assert retrieved is not None
    assert retrieved.name == "Test User"
    assert retrieved.role == "tutor"
    assert retrieved.is_active is True


def test_user_email_unique(app, db_session):
    """Email debe ser único."""
    user1 = User(email="unique@test.com", name="User 1", role="tutor")
    user2 = User(email="unique@test.com", name="User 2", role="admin")

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(Exception):  # Unique constraint violation
        db_session.commit()


def test_user_has_role():
    """Verificar método has_role."""
    user = User(email="test@example.com", name="Test", role="tutor")
    assert user.has_role("tutor") is True
    assert user.has_role("tutor", "admin") is True
    assert user.has_role("admin") is False


def test_user_role_enum_property():
    """Verificar propiedad role_enum."""
    user = User(email="test@example.com", name="Test", role="coordinador")
    assert user.role_enum == UserRole.COORDINATOR
    assert isinstance(user.role_enum, UserRole)
