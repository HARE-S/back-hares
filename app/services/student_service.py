import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
from sqlalchemy.orm import Session

from app.analytics.evolution import calculate_individual_evolution
from app.core.audit import log_audit
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.student import Student
from app.schemas.report_schema import StudentReportSchema
from app.schemas.student_schema import StudentDetailSchema
from app.services.reading_service import ReadingService
from app.services.result_service import ResultService


class StudentService:
    """
    Servicio de lógica de negocio para la ficha del alumno (BE-28).
    Compone en una única llamada:
    - Datos personales y demográficos.
    - Secciones actuales e históricas clasificadas.
    - Resultados de pruebas con métricas (PPM, eficacia/aciertos).
    - Historial de libros leídos con su estado.
    """

    def __init__(self, session: Session):
        self.session = session
        self.result_service = ResultService(session)
        self.reading_service = ReadingService(session)

    def _classify_sections(
        self, student: Student
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Distingue las secciones actuales de las históricas a partir de student_sections (T-BE28-03).
        - Secciones deshabilitadas (disabled_at no nulo) se consideran siempre históricas.
        - Para las secciones activas, el año académico más reciente (o en su defecto
          la fecha de matrícula más reciente) determina las secciones actuales.
        - Matrículas en cursos anteriores se clasifican como históricas.
        """
        current_sections: List[Dict[str, Any]] = []
        historical_sections: List[Dict[str, Any]] = []

        if not student.student_sections:
            return current_sections, historical_sections

        # Filtrar secciones deshabilitadas vs activas
        active_enrollments = []
        for ss in student.student_sections:
            if not ss.section:
                continue
            if ss.section.disabled_at is not None:
                sec_dict = ss.section.to_dict()
                sec_dict["enrollment_date"] = ss.created_on.isoformat() if ss.created_on else None
                historical_sections.append(sec_dict)
            else:
                active_enrollments.append(ss)

        if not active_enrollments:
            return current_sections, historical_sections

        # Determinar el criterio del periodo actual (año académico o fecha de creación)
        years = [ss.section.academic_year for ss in active_enrollments if ss.section.academic_year]
        if years:
            latest_year = max(years)
            for ss in active_enrollments:
                sec_dict = ss.section.to_dict()
                sec_dict["enrollment_date"] = ss.created_on.isoformat() if ss.created_on else None
                if ss.section.academic_year == latest_year:
                    current_sections.append(sec_dict)
                else:
                    historical_sections.append(sec_dict)
        else:
            dates = [ss.created_on for ss in active_enrollments if ss.created_on]
            if dates:
                latest_date = max(dates)
                for ss in active_enrollments:
                    sec_dict = ss.section.to_dict()
                    sec_dict["enrollment_date"] = ss.created_on.isoformat() if ss.created_on else None
                    if ss.created_on == latest_date:
                        current_sections.append(sec_dict)
                    else:
                        historical_sections.append(sec_dict)
            else:
                for ss in active_enrollments:
                    sec_dict = ss.section.to_dict()
                    sec_dict["enrollment_date"] = ss.created_on.isoformat() if ss.created_on else None
                    current_sections.append(sec_dict)

        return current_sections, historical_sections

    def get_student_detail(
        self,
        student_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene la ficha agregada del alumno en una sola llamada (BE-28).
        - 200 OK con datos personales, secciones, resultados y lecturas.
        - 404 Not Found si el alumno no existe.
        - 403 Forbidden si el tutor no tiene asignada ninguna sección del alumno
          o si el usuario tiene rol 'pendiente'.
        - Registra evento de visualización en auditoría.
        """
        # 1. Parsear UUID del alumno
        try:
            parsed_student_id = (
                student_id if isinstance(student_id, uuid.UUID) else uuid.UUID(str(student_id).strip())
            )
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("El identificador del alumno no es válido", field="student_id")

        # 2. Recuperar alumno
        student = self.session.get(Student, parsed_student_id)
        if not student:
            raise NotFoundError("El alumno especificado no existe")

        # 3. Control de acceso y permisos (Escenario 5b)
        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar la ficha del alumno")
            if user_role not in ("coordinator", "coordinador", "admin"):
                assigned_sections = {str(s).strip() for s in (current_user.get("sections") or [])}
                student_sections = {str(ss.section_id).strip() for ss in student.student_sections}
                if not (assigned_sections & student_sections):
                    raise ForbiddenError(
                        "El tutor no tiene permiso para consultar la ficha de este alumno"
                    )

        # 4. Clasificar secciones en actuales e históricas (T-BE28-03)
        current_sections, historical_sections = self._classify_sections(student)

        # 5. Componer resultados y lecturas reutilizando servicios existentes (T-BE28-02)
        results = self.result_service.get_student_history(parsed_student_id, current_user=current_user)
        readings = self.reading_service.get_student_readings(parsed_student_id, current_user=current_user)

        # 6. Registrar en auditoría
        log_audit(
            user=current_user,
            action="VIEW_STUDENT_CARD",
            resource_type="students",
            resource_id=str(parsed_student_id),
            details={
                "student_name": student.name,
                "current_sections_count": len(current_sections),
                "historical_sections_count": len(historical_sections),
                "results_count": len(results),
                "readings_count": len(readings),
            },
        )

        # 7. Serializar y devolver ficha completa
        return StudentDetailSchema.dump(
            student=student,
            current_sections=current_sections,
            historical_sections=historical_sections,
            results=results,
            readings=readings,
        )

    def get_student_report(
        self,
        student_id: Union[str, uuid.UUID],
        current_user: Optional[Dict[str, Any]] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene los datos estructurados para el informe individual de un alumno (BE-36).
        - Reutiliza la composición de la ficha de alumno de BE-28 (T-BE36-02).
        - Calcula la serie temporal de evolución y variaciones de BE-31.
        - Incluye fecha y hora de generación ISO UTC (Escenario 2).
        - Distingue indicador de evolución insuficiente sin proyecciones (Escenario 3).
        - Registra evento de auditoría GENERATE_STUDENT_REPORT (Escenario 5).
        """
        # 1. Obtener la ficha del alumno (comprueba existencia, parseo UUID y permisos de sección)
        student_card = self.get_student_detail(student_id=student_id, current_user=current_user)

        # 2. Calcular serie de evolución temporal reutilizando BE-31
        evolution = calculate_individual_evolution(
            results=student_card.get("results", []),
            start_date=start_date,
            end_date=end_date,
        )

        # 3. Fecha y hora de generación
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # 4. Registrar en auditoría (T-BE36-04 / Escenario 5)
        log_audit(
            user=current_user,
            action="GENERATE_STUDENT_REPORT",
            resource_type="students",
            resource_id=str(student_card["id"]),
            details={
                "student_name": student_card.get("name"),
                "results_count": len(student_card.get("results", [])),
                "readings_count": len(student_card.get("readings", [])),
                "has_insufficient_data": evolution.get("has_insufficient_data", False),
            },
        )

        # 5. Serializar y devolver informe individual estructurado (T-BE36-01)
        return StudentReportSchema.dump(
            student_card=student_card,
            evolution=evolution,
            generated_at=now_utc,
        )

