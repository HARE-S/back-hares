"""
Servicio para la generación de informes agregados de grupo y centro (BE-37).

Coordina:
- Validación de parámetros y existencia de sección / centro.
- Control estricto de roles (tutores restringidos a sus secciones y 403 en centros).
- Extracción de resultados con cálculo de métricas (PPM, comprensión, Vef).
- Invocación de agregaciones y distribuciones (app.analytics.group_report).
- Generación de Excel descargable (.xlsx) o estructura JSON.
- Registro en el log de auditoría.
"""

import io
from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy.orm import Session, joinedload

from app.analytics.group_report import calculate_group_aggregates
from app.analytics.metrics import (
    calculate_effective_speed,
    calculate_ppm,
    calculate_reading_comprehension,
)
from app.core.audit import log_audit
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.exports.group_excel import generate_group_report_excel
from app.models.center import Center, Section
from app.models.test import Result
from app.schemas.report_schema import CenterReportSchema, GroupReportSchema


class GroupReportService:
    def __init__(self, session: Session):
        self.session = session

    def get_section_report(
        self,
        section_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
        academic_year: Optional[str] = None,
        format: Optional[str] = None,
    ) -> Union[Dict[str, Any], io.BytesIO]:
        """
        Genera el informe agregado para una sección (grupo).

        - Valida identificador UUID y existencia de sección (400 / 404).
        - Verifica que el tutor tenga asignada la sección (403 si no asignada o rol pendiente).
        - Calcula medias de PPM, precisión, pruebas y participantes (Escenario 1).
        - Incluye distribución de resultados por tramos y estadísticos (Escenario 2).
        - Indica ausencia de datos si no hay resultados (Escenario 4).
        - Genera exportación Excel si format == 'excel' (Escenario 5).
        - Registra evento de auditoría GENERATE_SECTION_REPORT.
        """
        try:
            parsed_section_id = (
                section_id
                if isinstance(section_id, uuid.UUID)
                else uuid.UUID(str(section_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError(
                "El identificador de la sección no es válido", field="section_id"
            )

        section = self.session.get(Section, parsed_section_id)
        if not section:
            raise NotFoundError("La sección especificada no existe")

        # Control de permisos por rol
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError(
                    "El usuario con rol pendiente no tiene permisos para consultar informes"
                )
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {
                    str(s).strip() for s in (current_user.get("sections") or [])
                }
                if str(parsed_section_id).strip() not in assigned_sections:
                    raise ForbiddenError(
                        "El tutor no tiene permiso para consultar informes de esta sección"
                    )

        # Consulta de resultados para la sección
        query = (
            self.session.query(Result)
            .options(
                joinedload(Result.test),
                joinedload(Result.student),
            )
            .filter(Result.section_id == parsed_section_id)
        )

        results = query.order_by(Result.test_date.asc()).all()

        results_data = []
        for r in results:
            ppm = (
                calculate_ppm(r.test.words, r.time)
                if r.test and r.time > 0
                else 0.0
            )
            accuracy = calculate_reading_comprehension(r.successes, r.mistakes)
            vef = calculate_effective_speed(ppm, accuracy)
            results_data.append(
                {
                    "student_id": str(r.student_id),
                    "ppm": ppm,
                    "accuracy": accuracy,
                    "vef": vef,
                    "test_date": r.test_date.isoformat() if r.test_date else None,
                }
            )

        aggregates = calculate_group_aggregates(results_data)

        # Registro de auditoría
        log_audit(
            user=current_user,
            action="GENERATE_SECTION_REPORT",
            resource_type="sections",
            resource_id=str(section.id),
            details={
                "section_id": str(section.id),
                "section_name": section.name,
                "results_count": aggregates["results_count"],
                "participants_count": aggregates["participants_count"],
                "format": format or "json",
            },
        )

        serialized = GroupReportSchema.dump(section, aggregates)

        if str(format).strip().lower() in ("excel", "xlsx"):
            return generate_group_report_excel(serialized, is_center=False)

        return serialized

    def get_center_report(
        self,
        center_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
        academic_year: Optional[str] = None,
        format: Optional[str] = None,
    ) -> Union[Dict[str, Any], io.BytesIO]:
        """
        Genera el informe agregado para un centro completo.

        - Valida identificador UUID y existencia de centro (400 / 404).
        - Restringe acceso: solo coordinadores y administradores; tutores reciben 403 (Escenario 6).
        - Agrega datos del conjunto del centro y desglose por sección (Escenario 3).
        - Maneja centros sin datos o con secciones sin datos (Escenario 4).
        - Genera exportación Excel si format == 'excel' (Escenario 5).
        - Registra evento de auditoría GENERATE_CENTER_REPORT.
        """
        try:
            parsed_center_id = (
                center_id
                if isinstance(center_id, uuid.UUID)
                else uuid.UUID(str(center_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError(
                "El identificador del centro no es válido", field="center_id"
            )

        center = self.session.get(Center, parsed_center_id)
        if not center:
            raise NotFoundError("El centro especificado no existe")

        # Control de permisos por rol (Escenario 6: Dado un tutor -> 403 Forbidden)
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role in ("tutor", "profesor"):
                raise ForbiddenError(
                    "Los tutores no tienen acceso al informe completo de centro"
                )
            if user_role == "pendiente":
                raise ForbiddenError(
                    "El usuario con rol pendiente no tiene permisos para consultar informes"
                )
            if user_role not in ("coordinator", "coordinador", "admin"):
                raise ForbiddenError(
                    "Se requiere rol de coordinador o administrador para consultar el informe de centro"
                )

        # Consultar todas las secciones del centro
        sections = (
            self.session.query(Section)
            .filter(Section.center_id == parsed_center_id)
            .order_by(Section.name.asc())
            .all()
        )

        sections_breakdown = []
        all_center_results_data = []

        for sec in sections:
            sec_query = (
                self.session.query(Result)
                .options(
                    joinedload(Result.test),
                    joinedload(Result.student),
                )
                .filter(Result.section_id == sec.id)
            )

            sec_results = sec_query.order_by(Result.test_date.asc()).all()

            sec_results_data = []
            for r in sec_results:
                ppm = (
                    calculate_ppm(r.test.words, r.time)
                    if r.test and r.time > 0
                    else 0.0
                )
                accuracy = calculate_reading_comprehension(r.successes, r.mistakes)
                vef = calculate_effective_speed(ppm, accuracy)
                item = {
                    "student_id": str(r.student_id),
                    "ppm": ppm,
                    "accuracy": accuracy,
                    "vef": vef,
                    "test_date": r.test_date.isoformat() if r.test_date else None,
                }
                sec_results_data.append(item)
                all_center_results_data.append(item)

            sec_aggregates = calculate_group_aggregates(sec_results_data)
            sections_breakdown.append(
                GroupReportSchema.dump(sec, sec_aggregates)
            )

        # Agregados globales de todo el centro
        center_aggregates = calculate_group_aggregates(all_center_results_data)

        # Registro de auditoría
        log_audit(
            user=current_user,
            action="GENERATE_CENTER_REPORT",
            resource_type="centers",
            resource_id=str(center.id),
            details={
                "center_id": str(center.id),
                "center_name": center.name,
                "sections_count": len(sections),
                "results_count": center_aggregates["results_count"],
                "participants_count": center_aggregates["participants_count"],
                "format": format or "json",
            },
        )

        serialized = CenterReportSchema.dump(
            center, center_aggregates, sections_breakdown
        )

        if str(format).strip().lower() in ("excel", "xlsx"):
            return generate_group_report_excel(serialized, is_center=True)

        return serialized
