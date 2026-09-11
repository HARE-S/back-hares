import datetime
import io
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.analytics.metrics import calculate_metrics_from_result
from app.core.audit import log_audit
from app.core.exceptions import ForbiddenError, ValidationError
from app.exports.excel import generate_results_excel
from app.models.center import Section
from app.models.student import Student
from app.models.test import Result, Test


class ExportService:
    """
    Servicio de exportación de datos a hojas de cálculo Excel (BE-35).
    """

    def __init__(self, session: Session):
        self.session = session

    def export_results_to_excel(
        self,
        filters: Optional[Dict[str, Any]] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> io.BytesIO:
        """
        Genera el libro Excel (.xlsx) con los resultados de pruebas aplicando los filtros especificados.
        - Filtros opcionales: section_id, student_id, test_id, start_date, end_date, academic_year.
        - Control de acceso por rol:
          - 403 si el rol es 'pendiente'.
          - Si el usuario es tutor, comprueba que la sección pertenezca a sus secciones asignadas
            o restringe la consulta a sus secciones (T-BE35-04).
        - Registra la exportación en auditoría con usuario y filtros aplicados (T-BE35-05).
        - Devuelve un buffer BytesIO listo para descarga binaria.
        """
        filters = filters or {}

        # 1. Control de permisos
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para exportar datos")

            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                target_sec = filters.get("section_id")

                if target_sec is not None:
                    if str(target_sec).strip() not in assigned_sections:
                        raise ForbiddenError("El tutor no tiene permiso sobre la sección especificada")
                else:
                    # Restringir automáticamente a las secciones asignadas al tutor
                    filters["_allowed_sections"] = list(assigned_sections)

        # 2. Construir consulta con eager loading de relaciones
        query = (
            select(Result)
            .options(
                joinedload(Result.student),
                joinedload(Result.section),
                joinedload(Result.test),
            )
            .join(Result.section)
        )

        # Aplicar filtro por sección
        if "section_id" in filters and filters["section_id"]:
            try:
                sec_id = (
                    filters["section_id"]
                    if isinstance(filters["section_id"], uuid.UUID)
                    else uuid.UUID(str(filters["section_id"]).strip())
                )
                query = query.filter(Result.section_id == sec_id)
            except (ValueError, TypeError, AttributeError):
                raise ValidationError("El identificador de sección no es válido", field="section_id")
        elif "_allowed_sections" in filters:
            allowed_uuids = []
            for s in filters["_allowed_sections"]:
                try:
                    allowed_uuids.append(uuid.UUID(str(s).strip()))
                except (ValueError, TypeError, AttributeError):
                    pass
            query = query.filter(Result.section_id.in_(allowed_uuids))

        # Aplicar filtro por alumno
        if "student_id" in filters and filters["student_id"]:
            try:
                st_id = (
                    filters["student_id"]
                    if isinstance(filters["student_id"], uuid.UUID)
                    else uuid.UUID(str(filters["student_id"]).strip())
                )
                query = query.filter(Result.student_id == st_id)
            except (ValueError, TypeError, AttributeError):
                raise ValidationError("El identificador del alumno no es válido", field="student_id")

        # Aplicar filtro por prueba
        if "test_id" in filters and filters["test_id"]:
            try:
                t_id = (
                    filters["test_id"]
                    if isinstance(filters["test_id"], uuid.UUID)
                    else uuid.UUID(str(filters["test_id"]).strip())
                )
                query = query.filter(Result.test_id == t_id)
            except (ValueError, TypeError, AttributeError):
                raise ValidationError("El identificador de la prueba no es válido", field="test_id")

        # Aplicar filtro por rango de fechas
        start_date = filters.get("start_date") or filters.get("from_date")
        if start_date:
            parsed_start = (
                start_date
                if isinstance(start_date, datetime.date)
                else datetime.date.fromisoformat(str(start_date).strip())
            )
            query = query.filter(Result.test_date >= parsed_start)

        end_date = filters.get("end_date") or filters.get("to_date")
        if end_date:
            parsed_end = (
                end_date
                if isinstance(end_date, datetime.date)
                else datetime.date.fromisoformat(str(end_date).strip())
            )
            query = query.filter(Result.test_date <= parsed_end)

        # Aplicar filtro por curso académico
        if "academic_year" in filters and filters["academic_year"]:
            query = query.filter(Section.academic_year == str(filters["academic_year"]).strip())

        # Ordenar cronológicamente
        query = query.order_by(Result.test_date.asc(), Result.id.asc())

        results = self.session.execute(query).scalars().all()

        # 3. Transformar resultados inyectando métricas calculadas (T-BE35-03)
        rows: List[Dict[str, Any]] = []
        for r in results:
            metrics = calculate_metrics_from_result(r)
            row_data = {
                "test_date": r.test_date,
                "student_name": r.student.name if r.student else "",
                "student_external_id": r.student.external_id if r.student else "",
                "student_id": str(r.student_id),
                "section_name": r.section.name if r.section else "",
                "test_name": r.test.name if r.test else "",
                "test_code": r.test.code if r.test else "",
                "words": r.test.words if r.test else 0,
                "time": r.time,
                "successes": r.successes,
                "mistakes": r.mistakes,
                "ppm": metrics.get("ppm", 0.0),
                "comprehension": metrics.get("comprehension", 0.0),
                "vef": metrics.get("vef", 0.0),
            }
            rows.append(row_data)

        # 4. Generar archivo Excel binario
        excel_buffer = generate_results_excel(rows)

        # 5. Registro en auditoría (T-BE35-05)
        audit_details = {k: str(v) for k, v in filters.items() if not k.startswith("_")}
        audit_details["rows_exported"] = len(rows)

        log_audit(
            user=current_user,
            action="EXPORT_EXCEL",
            resource_type="results",
            resource_id="bulk",
            details=audit_details,
        )

        return excel_buffer
