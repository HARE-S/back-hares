"""Tests para BE-44: Revocación y auditoría."""

import pytest
from app.models.audit import AuditLog, AuditAction
from app.services.audit_service import AuditService


class TestAuditService:
    """Tests para AuditService."""

    def test_log_event(self, app, db_session):
        """Registrar un evento de auditoría."""
        service = AuditService(db_session)
        result = service.log_event(
            action=AuditAction.LOGIN.value,
            user_email="user@grupopenascal.com",
            user_id="test-user-123",
            status="success",
        )

        assert result["action"] == "login"
        assert result["user_email"] == "user@grupopenascal.com"
        assert "timestamp" in result

    def test_log_event_permission_denied(self, app, db_session):
        """Registrar intento de acceso denegado."""
        service = AuditService(db_session)
        service.log_event(
            action=AuditAction.PERMISSION_DENIED.value,
            user_email="user@grupopenascal.com",
            resource_type="users",
            resource_id="other-user-id",
            details="Intentó acceder a usuario sin permisos",
            status="denied",
        )

        # Verificar que se registró
        logs = db_session.query(AuditLog).all()
        assert len(logs) == 1
        assert logs[0].action == "permission_denied"
        assert logs[0].status == "denied"

    def test_get_logs(self, app, db_session):
        """Consultar logs de auditoría."""
        service = AuditService(db_session)

        # Crear varios logs
        for i in range(5):
            service.log_event(
                action=AuditAction.LOGIN.value,
                user_email=f"user{i}@grupopenascal.com",
            )

        # Consultar
        result = service.get_logs(limit=10)
        assert result["total"] == 5
        assert len(result["logs"]) == 5

    def test_get_logs_filter_by_user(self, app, db_session):
        """Filtrar logs por usuario."""
        service = AuditService(db_session)

        service.log_event(
            action=AuditAction.LOGIN.value,
            user_email="alice@grupopenascal.com",
        )
        service.log_event(
            action=AuditAction.LOGIN.value,
            user_email="bob@grupopenascal.com",
        )

        result = service.get_logs(user_email="alice@grupopenascal.com")
        assert result["total"] == 1
        assert result["logs"][0]["user_email"] == "alice@grupopenascal.com"

    def test_get_logs_filter_by_action(self, app, db_session):
        """Filtrar logs por acción."""
        service = AuditService(db_session)

        service.log_event(
            action=AuditAction.LOGIN.value,
            user_email="user@grupopenascal.com",
        )
        service.log_event(
            action=AuditAction.LOGOUT.value,
            user_email="user@grupopenascal.com",
        )

        result = service.get_logs(action=AuditAction.LOGIN.value)
        assert result["total"] == 1
        assert result["logs"][0]["action"] == "login"

    def test_get_user_logs(self, app, db_session):
        """Obtener todos los logs de un usuario."""
        service = AuditService(db_session)

        # Crear logs del usuario
        for action in ["login", "logout", "login"]:
            service.log_event(
                action=action,
                user_email="user@grupopenascal.com",
            )

        # Crear logs de otro usuario
        service.log_event(
            action="login",
            user_email="other@grupopenascal.com",
        )

        # Consultar logs del usuario
        logs = service.get_user_logs("user@grupopenascal.com", limit=100)
        assert len(logs) == 3
        assert all(log["user_email"] == "user@grupopenascal.com" for log in logs)

    def test_log_entry_fields(self, app, db_session):
        """Verificar que todos los campos se guardan correctamente."""
        service = AuditService(db_session)
        service.log_event(
            action=AuditAction.ROLE_CHANGED.value,
            user_email="admin@grupopenascal.com",
            user_id="admin-123",
            resource_type="user",
            resource_id="user-456",
            details="Changed role from tutor to coordinator",
            status="success",
        )

        log = db_session.query(AuditLog).first()
        assert log.action == "role_changed"
        assert log.resource_type == "user"
        assert log.resource_id == "user-456"
        assert log.details == "Changed role from tutor to coordinator"
        assert log.status == "success"
