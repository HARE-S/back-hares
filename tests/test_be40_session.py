"""Tests para BE-40: Sesión de servidor."""

import pytest
from datetime import datetime, timedelta
from app.models.user import User, UserRole
from app.models.session import Session
from app.services.session_service import SessionService
from app.core.exceptions import NotFoundError


class TestSessionService:
    """Tests para SessionService."""

    def test_create_session(self, app, db_session):
        """Crear una sesión para un usuario."""
        # Crear usuario
        user = User(
            email="session@grupopenascal.com",
            name="Session",
            lastname="Test",
            area="Fontanería",
            role=UserRole.TUTOR.value,
        )
        user.set_password("pass123")
        db_session.add(user)
        db_session.flush()

        # Crear sesión
        service = SessionService(db_session)
        result = service.create_session(
            user_id=str(user.id),
            session_id="test-session-123",
        )

        assert result["email"] == "session@grupopenascal.com"
        assert result["role"] == "tutor"
        assert result["area"] == "Fontanería"

    def test_get_active_session(self, app, db_session):
        """Obtener una sesión activa."""
        # Crear usuario y sesión
        user = User(
            email="session2@grupopenascal.com",
            name="Session2",
            lastname="Test",
            area="Electricidad",
            role=UserRole.TUTOR.value,
        )
        user.set_password("pass123")
        db_session.add(user)
        db_session.flush()

        service = SessionService(db_session)
        service.create_session(
            user_id=str(user.id),
            session_id="test-session-456",
        )

        # Recuperar sesión
        result = service.get_session("test-session-456")
        assert result["email"] == "session2@grupopenascal.com"

    def test_get_expired_session_fails(self, app, db_session):
        """Una sesión expirada no se puede recuperar."""
        user = User(
            email="expired@grupopenascal.com",
            name="Expired",
            lastname="Test",
            area="Informatica",
            role=UserRole.TUTOR.value,
        )
        user.set_password("pass123")
        db_session.add(user)
        db_session.flush()

        # Crear sesión con expiración inmediata
        expired_session = Session(
            id="expired-session",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            user_area=user.area,
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_active=True,
        )
        db_session.add(expired_session)
        db_session.commit()

        # Intentar recuperar
        service = SessionService(db_session)
        with pytest.raises(NotFoundError):
            service.get_session("expired-session")

    def test_invalidate_session(self, app, db_session):
        """Invalidar una sesión."""
        user = User(
            email="invalidate@grupopenascal.com",
            name="Invalidate",
            lastname="Test",
            area="Hosteleria",
            role=UserRole.TUTOR.value,
        )
        user.set_password("pass123")
        db_session.add(user)
        db_session.flush()

        service = SessionService(db_session)
        service.create_session(
            user_id=str(user.id),
            session_id="test-session-789",
        )

        # Invalidar
        service.invalidate_session("test-session-789")

        # Intentar recuperar
        with pytest.raises(NotFoundError):
            service.get_session("test-session-789")

    def test_invalidate_user_sessions(self, app, db_session):
        """Invalidar todas las sesiones de un usuario."""
        user = User(
            email="multi@grupopenascal.com",
            name="Multi",
            lastname="Test",
            area="Carpinteria",
            role=UserRole.TUTOR.value,
        )
        user.set_password("pass123")
        db_session.add(user)
        db_session.flush()

        service = SessionService(db_session)
        service.create_session(str(user.id), "session-1")
        service.create_session(str(user.id), "session-2")

        # Invalidar todas
        count = service.invalidate_user_sessions(str(user.id))
        assert count == 2

        # Ninguna debe ser recuperable
        with pytest.raises(NotFoundError):
            service.get_session("session-1")
