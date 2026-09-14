"""Servicio de consulta de centros, secciones y alumnado (BE-10).

Recursos de solo lectura: su origen es Alexia. El servicio centraliza
la localización de recursos activos (excluyendo deshabilitados) y el
filtrado por secciones asignadas del tutor (Escenario 6).
"""
import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.repositories.student_repository import StudentRepository
from app.schemas.center_schema import CenterSchema, SectionSchema, StudentSummarySchema


class DirectoryService:
    """Lógica de negocio para la navegación por centros, secciones y alumnado."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = StudentRepository(session)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _parse_uuid(value: Union[str, uuid.UUID], field: str) -> uuid.UUID:
        """Convierte el identificador de ruta a UUID o lanza 400 si es inválido."""
        try:
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value).strip())
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("El identificador no es válido", field=field)

    # ------------------------------------------------------------------- centers
    def list_centers(self, current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Devuelve los centros activos ordenados por nombre (Escenario 1)."""
        centers = self.repo.get_all_active_centers()
        return CenterSchema(many=True).dump(centers)

    def get_center_sections(
        self,
        center_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Devuelve las secciones activas de un centro (Escenario 2)."""
        parsed = self._parse_uuid(center_id, "center_id")
        center = self.repo.get_active_center(parsed)
        if center is None:
            raise NotFoundError("El centro especificado no existe")
        sections = self.repo.get_sections_by_center(parsed)
        return SectionSchema(many=True).dump(sections)

    # ------------------------------------------------------------------ students
    def get_section_students(
        self,
        section_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Devuelve el alumnado activo matriculado en una sección (Escenario 3).

        El tutor solo puede consultar las secciones que tiene asignadas
        (Escenario 6) y el rol 'pendiente' queda excluido.
        """
        parsed = self._parse_uuid(section_id, "section_id")
        section = self.repo.get_active_section(parsed)
        if section is None:
            raise NotFoundError("La sección especificada no existe")

        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar alumnado")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                if str(parsed) not in assigned_sections:
                    raise ForbiddenError(
                        "El tutor no tiene permiso para consultar el alumnado de esta sección"
                    )

        students = self.repo.get_students_by_section(parsed)
        return StudentSummarySchema(many=True).dump(students)