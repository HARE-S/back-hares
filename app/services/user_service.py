"""Servicio de gestión de usuarios (BE-42, BE-43)."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserSection, UserRole
from app.models.center import Section
from app.core.exceptions import NotFoundError, ValidationError, ConflictError


class UserService:
    """Gestiona usuarios, roles y permisos."""

    def __init__(self, session: Session):
        self.session = session

    def create_user(self, email: str, name: str, role: str) -> Dict[str, Any]:
        """Crea un nuevo usuario con rol asignado."""
        # Verificar que el rol es válido
        try:
            UserRole(role)
        except ValueError:
            raise ValidationError(f"Rol '{role}' no válido")

        # Verificar unicidad de email
        existing = self.session.query(User).filter(User.email == email).first()
        if existing:
            raise ConflictError(f"El email '{email}' ya está registrado")

        user = User(
            email=email,
            name=name,
            role=role,
            is_active=True,
        )
        self.session.add(user)
        self.session.commit()

        return self._user_to_dict(user)

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Obtiene un usuario por ID."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado")
        return self._user_to_dict(user)

    def list_users(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Lista usuarios con paginación."""
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit

        total = self.session.query(User).count()
        users = self.session.query(User).offset(offset).limit(limit).all()

        return {
            "items": [self._user_to_dict(u) for u in users],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    def update_user_role(self, user_id: str, new_role: str) -> Dict[str, Any]:
        """Cambia el rol de un usuario."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado")

        # Verificar validez del nuevo rol
        try:
            UserRole(new_role)
        except ValueError:
            raise ValidationError(f"Rol '{new_role}' no válido")

        user.role = new_role
        self.session.commit()

        return self._user_to_dict(user)

    def assign_section(self, user_id: str, section_id: str) -> Dict[str, Any]:
        """Asigna un usuario a una sección."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado")

        section = self.session.query(Section).filter(Section.id == section_id).first()
        if not section:
            raise NotFoundError(f"Sección {section_id} no encontrada")

        # Verificar que no esté ya asignado
        existing = self.session.query(UserSection).filter(
            UserSection.user_id == user_id,
            UserSection.section_id == section_id,
        ).first()
        if existing:
            raise ConflictError(f"Usuario ya asignado a esta sección")

        assignment = UserSection(user_id=user_id, section_id=section_id)
        self.session.add(assignment)
        self.session.commit()

        return self._user_to_dict(user)

    def remove_section(self, user_id: str, section_id: str) -> Dict[str, Any]:
        """Remueve un usuario de una sección."""
        assignment = self.session.query(UserSection).filter(
            UserSection.user_id == user_id,
            UserSection.section_id == section_id,
        ).first()
        if not assignment:
            raise NotFoundError("Asignación no encontrada")

        self.session.delete(assignment)
        self.session.commit()

        user = self.session.query(User).filter(User.id == user_id).first()
        return self._user_to_dict(user)

    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Desactiva un usuario (revoca acceso)."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado")

        user.is_active = False
        self.session.commit()

        return self._user_to_dict(user)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email."""
        return self.session.query(User).filter(User.email == email).first()

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convierte un usuario a diccionario."""
        section_ids = [str(s.id) for s in user.sections] if user.sections else []
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "sections": section_ids,
        }
