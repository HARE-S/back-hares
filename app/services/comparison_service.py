"""
Servicio de comparativa de evolución por grupos (BE-32).

Agrupa resultados por sección, centro o perfil (sector) y devuelve las medias
de PPM, comprensión y Vef de cada grupo acompañadas del tamaño de la muestra:

- Media siempre junto a nº de alumnos y nº de pruebas (Escenario 2).
- Umbral de representatividad configurable con marca en la respuesta (Escenario 3).
- Grupos sin datos con tamaño cero y sin media (Escenario 5).
- Restricción por rol: comparativas entre centros solo coordinador/responsable
  pedagógico (Escenario 6); tutores limitados a sus secciones.
- Registro del evento en auditoría.
"""

from typing import Any, Dict, List, Optional
import uuid

from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.analytics.comparison import build_group_comparison
from app.analytics.metrics import (
    calculate_effective_speed,
    calculate_ppm,
    calculate_reading_comprehension,
)
from app.core.audit import log_audit
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Result

_PROFILE_UNKNOWN = "Sin perfil"


def _as_uuid(val: Any, field_name: str = "id") -> uuid.UUID:
    try:
        return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val).strip())
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(
            f"El identificador '{field_name}' no es válido", field=field_name
        )


class ComparisonService:
    """Lógica de negocio de la comparativa de evolución por grupos."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------ helpers

    def _min_sample(self, min_sample: Optional[int]) -> int:
        if min_sample is not None:
            return int(min_sample)
        return int(current_app.config.get("COMPARE_MIN_SAMPLE_SIZE", 5))

    def _resolve_scope(
        self, current_user: Optional[Dict[str, Any]], group_by: str
    ) -> Optional[set]:
        """
        Control de rol según el modo de la comparativa (BE-32 Escenario 6).

        - Rol ``pendiente`` → 403.
        - Modo ``center`` → solo coordinator/coordinador/admin.
        - Modos ``section`` y ``profile`` → tutores limitados a sus secciones.

        Devuelve el conjunto de secciones permitidas para el tutor/profesor o
        ``None`` para coordinador/admin (acceso total).
        """
        user_role = str((current_user or {}).get("role", "")).strip().lower()

        if user_role == "pendiente":
            raise ForbiddenError(
                "El usuario con rol pendiente no tiene permisos para consultar comparativas"
            )

        if group_by == "center":
            if user_role not in ("coordinator", "coordinador", "admin", "superadmin"):
                raise ForbiddenError(
                    "Las comparativas entre centros solo están disponibles para el "
                    "coordinador o responsable pedagógico"
                )
            return None

        if user_role in ("coordinator", "coordinador", "admin", "superadmin"):
            return None

        assigned = {
            str(s).strip()
            for s in (current_user or {}).get("sections") or []
            if str(s).strip()
        }
        if not assigned:
            raise ForbiddenError("El tutor no tiene secciones asignadas")
        return assigned

    def _resolve_sections(
        self,
        scope: Optional[set],
        section_ids: Optional[List[Any]],
        center_id: Optional[uuid.UUID],
    ) -> List[Section]:
        """
        Resuelve las secciones a comparar en modo section/profile.

        - Tutor: intersectadas con su ámbito (403 si pide otras).
        - Coordinador/admin: todas o las especificadas en ``section_ids``.
        - Secciones inexistentes solicitadas → 404.
        """
        query = (
            select(Section)
            .options(joinedload(Section.center))
            .order_by(Section.name.asc())
        )

        effective_ids: Optional[List[uuid.UUID]] = None
        if section_ids:
            effective_ids = [_as_uuid(s, "section_id") for s in section_ids]
        elif scope is not None:
            effective_ids = [uuid.UUID(str(s).strip()) for s in scope]

        if effective_ids:
            if scope is not None and section_ids:
                allowed = {uuid.UUID(str(s).strip()) for s in scope}
                if any(sid not in allowed for sid in effective_ids):
                    raise ForbiddenError(
                        "El tutor no tiene permiso sobre alguna de las secciones indicadas"
                    )
            query = query.where(Section.id.in_(effective_ids))

        if center_id is not None:
            query = query.where(Section.center_id == center_id)

        sections = list(self.session.scalars(query).all())

        if section_ids:
            found = {str(s.id) for s in sections}
            for sid in effective_ids or []:
                if str(sid) not in found:
                    raise NotFoundError("Alguna de las secciones especificadas no existe")

        return sections

    def _resolve_center(self, center_id: Optional[uuid.UUID]) -> Optional[Center]:
        center = (
            self.session.get(Center, center_id)
            if center_id is not None
            else None
        )
        if center_id is not None and center is None:
            raise NotFoundError("El centro especificado no existe")
        return center

    def _fetch_results(
        self,
        section_ids: Optional[List[uuid.UUID]],
        center_id: Optional[uuid.UUID],
        start_date,
        end_date,
    ) -> List[Result]:
        """Consulta de resultados con relaciones cargadas y acotaciones opcionales."""
        stmt = (
            select(Result)
            .options(
                joinedload(Result.test),
                joinedload(Result.student),
                joinedload(Result.section).joinedload(Section.center),
            )
            .order_by(Result.test_date.asc())
        )
        if section_ids:
            stmt = stmt.where(Result.section_id.in_(section_ids))
        if center_id is not None:
            stmt = stmt.where(Result.section.has(Section.center_id == center_id))
        if start_date is not None:
            stmt = stmt.where(Result.test_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(Result.test_date <= end_date)
        return list(self.session.scalars(stmt).all())

    @staticmethod
    def _score_item(result: Result) -> Dict[str, Any]:
        """Extrae métricas de un resultado en el formato de agregación de grupo."""
        ppm = (
            calculate_ppm(result.test.words, result.time)
            if result.test and result.time and result.time > 0 and result.test.words
            else 0.0
        )
        accuracy = calculate_reading_comprehension(result.successes, result.mistakes)
        vef = calculate_effective_speed(ppm, accuracy)
        return {
            "student_id": str(result.student_id),
            "ppm": ppm,
            "accuracy": accuracy,
            "vef": vef,
        }

    # ------------------------------------------------------------------ consulta

    def get_group_comparison(
        self,
        group_by: str,
        current_user: Optional[Dict[str, Any]] = None,
        section_ids: Optional[List[Any]] = None,
        center_id: Optional[uuid.UUID] = None,
        min_sample: Optional[int] = None,
        start_date=None,
        end_date=None,
    ) -> Dict[str, Any]:
        """
        Genera la comparativa de evolución media entre grupos.

        :param group_by: ``section``, ``center`` o ``profile`` (sector).
        """
        normalized_by = str(group_by or "").strip().lower()
        if normalized_by not in ("section", "center", "profile"):
            raise ValidationError(
                "El parámetro 'group_by' debe ser 'section', 'center' o 'profile'",
                field="group_by",
            )

        min_sample = self._min_sample(min_sample)
        scope = self._resolve_scope(current_user, normalized_by)
        self._resolve_center(center_id)

        if normalized_by == "center":
            groups_data = self._groups_by_center(
                center_id, start_date, end_date
            )
        elif normalized_by == "profile":
            profile_sections = self._resolve_sections(scope, section_ids, center_id)
            groups_data = self._groups_by_profile(
                profile_sections, start_date, end_date
            )
        else:
            sections = self._resolve_sections(scope, section_ids, center_id)
            groups_data = self._groups_by_section(
                sections, start_date, end_date
            )

        groups = build_group_comparison(groups_data, min_sample)

        # Auditoría (BE-44 / BE-32 notas)
        log_audit(
            user=current_user,
            action="GENERATE_GROUP_COMPARISON",
            resource_type="comparison",
            resource_id=normalized_by,
            details={
                "group_by": normalized_by,
                "groups_count": len(groups),
                "results_count": sum(int(g["results_count"]) for g in groups),
                "min_sample": min_sample,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        )

        return {
            "group_by": normalized_by,
            "min_sample": min_sample,
            "groups": groups,
        }

    # ------------------------------------------------------------------ modos

    def _groups_by_section(
        self, sections: List[Section], start_date=None, end_date=None
    ) -> List[Dict[str, Any]]:
        results = self._fetch_results(
            [s.id for s in sections], None, start_date, end_date
        )
        mapping = {
            str(sec.id): {
                "id": str(sec.id),
                "name": sec.name,
                "group_by": "section",
                "center_id": str(sec.center_id),
                "center_name": sec.center.name if sec.center else None,
                "results": [],
            }
            for sec in sections
        }
        for result in results:
            group = mapping.get(str(result.section_id))
            if group is not None:
                group["results"].append(self._score_item(result))
        return list(mapping.values())

    def _groups_by_center(
        self, center_id: Optional[uuid.UUID], start_date=None, end_date=None
    ) -> List[Dict[str, Any]]:
        center_query = select(Center).order_by(Center.name.asc())
        if center_id is not None:
            center_query = center_query.where(Center.id == center_id)
        centers = list(self.session.scalars(center_query).all())

        results = self._fetch_results(None, center_id, start_date, end_date)
        mapping = {
            str(center.id): {
                "id": str(center.id),
                "name": center.name,
                "group_by": "center",
                "center_id": str(center.id),
                "center_name": center.name,
                "results": [],
            }
            for center in centers
        }
        for result in results:
            center_assoc = result.section.center if result.section else None
            group = mapping.get(str(center_assoc.id)) if center_assoc else None
            if group is not None:
                group["results"].append(self._score_item(result))
        return list(mapping.values())

    def _groups_by_profile(
        self, sections: List[Section], start_date=None, end_date=None
    ) -> List[Dict[str, Any]]:
        section_ids = [s.id for s in sections]
        if not sections:
            return []

        # Perfiles presentes en la matrícula de las secciones acotadas (incluye
        # perfiles sin resultados = grupos vacíos, Escenario 5).
        enrollment_stmt = (
            select(Student)
            .join(StudentSection)
            .where(StudentSection.section_id.in_(section_ids))
            .distinct()
        )
        enrolled_students = list(self.session.scalars(enrollment_stmt).all())

        profile_names: List[str] = []
        for student in enrolled_students:
            label = (student.sector or _PROFILE_UNKNOWN).strip() or _PROFILE_UNKNOWN
            if label not in profile_names:
                profile_names.append(label)
        profile_names.sort()
        if "Sin perfil" in profile_names:
            profile_names.remove("Sin perfil")
            profile_names.append("Sin perfil")

        mapping = {
            label: {
                "id": label,
                "name": label,
                "group_by": "profile",
                "center_id": None,
                "center_name": None,
                "results": [],
            }
            for label in profile_names
        }

        results = self._fetch_results(section_ids, None, start_date, end_date)
        for result in results:
            label = "Sin perfil"
            if result.student and result.student.sector:
                cleaned = str(result.student.sector).strip()
                if cleaned:
                    label = cleaned
            group = mapping.get(label)
            if group is not None:
                group["results"].append(self._score_item(result))

        return list(mapping.values())