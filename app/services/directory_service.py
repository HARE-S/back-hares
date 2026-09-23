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

    @staticmethod
    def _restricted_sections(current_user: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """Devuelve las secciones asignadas si el usuario es un tutor restringido.

        - Rol 'pendiente': lanza 403.
        - Rol privilegiado (coordinator/coordinador/admin): devuelve None
          (sin restricción).
        - Tutor: conjunto de secciones asignadas.
        """
        if not current_user:
            return None
        user_role = str(current_user.get("role", "")).strip().lower()
        if user_role == "pendiente":
            raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar el directorio")
        if user_role in ("coordinator", "coordinador", "admin"):
            return None
        return {str(s).strip() for s in (current_user.get("sections") or [])}

    # ------------------------------------------------------------------- centers
    def list_centers(self, current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Devuelve los centros activos ordenados por nombre (Escenario 1).

        - Rol privilegiado: todos los centros activos, con el número de
          secciones activas de cada uno (sections_count, FE-25).
        - Tutor: solo los centros que contienen alguna de sus secciones
          asignadas (Escenario 4), con el número de secciones asignadas.
        """
        restricted = self._restricted_sections(current_user)
        centers = self.repo.get_all_active_centers()
        center_ids = [c.id for c in centers]

        if restricted is None:
            counts = self.repo.count_active_sections_by_center(center_ids)
        else:
            sections = self.repo.get_sections_by_centers(center_ids)
            allowed = [s for s in sections if str(s.id) in restricted]
            allowed_center_ids = {s.center_id for s in allowed}
            centers = [c for c in centers if c.id in allowed_center_ids]
            counts = {}
            for s in allowed:
                counts[s.center_id] = counts.get(s.center_id, 0) + 1

        data = CenterSchema(many=True).dump(centers)
        for item, center in zip(data, centers):
            item["sections_count"] = counts.get(center.id, 0)
        return data

    def get_center_sections(
        self,
        center_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Devuelve las secciones activas de un centro (Escenario 2).

        - Tutor: solo sus secciones asignadas dentro de ese centro, con el
          número de alumnos matriculados de cada una (students_count, FE-25);
          403 si no tiene ninguna asignada allí (Escenario 4).
        """
        parsed = self._parse_uuid(center_id, "center_id")
        center = self.repo.get_active_center(parsed)
        if center is None:
            raise NotFoundError("El centro especificado no existe")
        restricted = self._restricted_sections(current_user)
        sections = self.repo.get_sections_by_center(parsed)
        if restricted is not None:
            sections = [s for s in sections if str(s.id) in restricted]
            if not sections:
                raise ForbiddenError("El tutor no tiene permiso para consultar las secciones de este centro")

        counts = self.repo.count_enrolled_students_by_section([s.id for s in sections])
        data = SectionSchema(many=True).dump(sections)
        for item, section in zip(data, sections):
            item["students_count"] = counts.get(section.id, 0)
        return data

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

        restricted = self._restricted_sections(current_user)
        if restricted is not None and str(parsed) not in restricted:
            raise ForbiddenError(
                "El tutor no tiene permiso para consultar el alumnado de esta sección"
            )

        students = self.repo.get_students_by_section(parsed)
        return StudentSummarySchema(many=True).dump(students)