"""Servicio de gestión de sesiones (BE-40)."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.user import User
from app.core.exceptions import NotFoundError


class SessionService:
    """Gestiona sesiones de usuario."""

    def __init__(self, session: Session):
        self.session = session

    def create_session(self, user_id: str, session_id: str, expire_hours: int = 24) -> dict:
        """Crea una nueva sesión para el usuario."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado")

        expires_at = datetime.utcnow() + timedelta(hours=expire_hours)

        session_record = SessionModel(
            id=session_id,
            user_id=user_id,
            user_email=user.email,
            user_role=user.role,
            user_area=user.area or "Sin área",
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(session_record)
        self.session.commit()

        return {
            "session_id": session_id,
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "area": user.area or "Sin área",
            "expires_at": expires_at.isoformat(),
        }

    def get_session(self, session_id: str) -> dict:
        """Obtiene una sesión activa."""
        session_record = self.session.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.is_active == True,
        ).first()

        if not session_record:
            raise NotFoundError("Sesión no encontrada o inactiva")

        # Verificar si ha expirado
        if session_record.expires_at < datetime.utcnow():
            session_record.is_active = False
            self.session.commit()
            raise NotFoundError("Sesión expirada")

        return {
            "session_id": session_record.id,
            "user_id": str(session_record.user_id),
            "email": session_record.user_email,
            "role": session_record.user_role,
            "area": session_record.user_area,
        }

    def invalidate_session(self, session_id: str) -> None:
        """Invalida (cierra) una sesión."""
        session_record = self.session.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()

        if session_record:
            session_record.is_active = False
            self.session.commit()

    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalida todas las sesiones de un usuario."""
        count = self.session.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.is_active == True,
        ).update({"is_active": False})
        self.session.commit()
        return count
