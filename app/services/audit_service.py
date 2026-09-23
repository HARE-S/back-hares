"""Servicio de auditoría (BE-44)."""

from typing import Optional, Dict, Any
from uuid import UUID
from flask import request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog, AuditAction


class AuditService:
    """Registra y consulta eventos de auditoría."""

    def __init__(self, session: Session):
        self.session = session

    def log_event(
        self,
        action: str,
        user_email: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        status: str = "success",
    ) -> dict:
        """Registra un evento de auditoría."""
        ip_address = self._get_client_ip()

        log = AuditLog(
            user_id=self._normalize_user_id(user_id),
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            status=status,
        )
        self.session.add(log)
        self.session.commit()

        return {
            "id": str(log.id),
            "action": log.action,
            "user_email": log.user_email,
            "timestamp": log.created_at.isoformat(),
        }

    def get_logs(
        self,
        user_email: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Consulta logs de auditoría con filtros."""
        query = self.session.query(AuditLog)

        if user_email:
            query = query.filter(AuditLog.user_email == user_email)
        if action:
            query = query.filter(AuditLog.action == action)

        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        return {
            "total": total,
            "logs": [self._log_to_dict(log) for log in logs],
        }

    def get_user_logs(self, user_email: str, limit: int = 100) -> list:
        """Obtiene todos los logs de un usuario."""
        logs = self.session.query(AuditLog).filter(
            AuditLog.user_email == user_email
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

        return [self._log_to_dict(log) for log in logs]

    def _log_to_dict(self, log: AuditLog) -> dict:
        """Convierte un log a diccionario."""
        return {
            "id": str(log.id),
            "user_email": log.user_email,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "status": log.status,
            "timestamp": log.created_at.isoformat(),
        }

    @staticmethod
    def _normalize_user_id(user_id: Optional[str]) -> Optional[UUID]:
        """Solo guarda IDs de usuario válidos (UUID); el resto se omite."""
        if not user_id:
            return None
        try:
            return UUID(user_id)
        except (ValueError, AttributeError, TypeError):
            return None

    @staticmethod
    def _get_client_ip() -> Optional[str]:
        """Obtiene la IP del cliente."""
        try:
            if request.headers.get("X-Forwarded-For"):
                return request.headers.get("X-Forwarded-For").split(",")[0].strip()
            return request.remote_addr
        except Exception:
            return None
