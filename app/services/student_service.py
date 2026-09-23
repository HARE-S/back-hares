import datetime
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.analytics.evolution import calculate_individual_evolution
from app.analytics.metrics import calculate_ppm, calculate_reading_comprehension
from app.analytics.progress_detection import classify_students_progress
from app.core.audit import log_audit
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.student import Student, StudentSection
from app.repositories.student_repository import StudentRepository, MISSING_VALUE
from app.models.test import Result
from app.schemas.progress_schema import ProgressDetectionSchema
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

    # ------------------------------------------------------------------ scope

    @staticmethod
    def _resolve_scope(
        current_user: Optional[Dict[str, Any]],
        requested_section_id: Optional[uuid.UUID] = None,
    ) -> Optional[List[uuid.UUID]]:
        """
        Resuelve el ámbito de secciones por rol (compartido BE-27 / BE-29).

        - ``pendiente`` → ``ForbiddenError``.
        - Tutor → lista de secciones asignadas; ``ForbiddenError`` si vacía.
          Si ``requested_section_id`` se proporciona, verifica que pertenece al ámbito.
        - Coordinator / admin → acceso total (``None``).

        Returns la lista de secciones del tutor o ``None`` para coordinador/admin.
        """
        user_role = str((current_user or {}).get("role", "")).strip().lower()
        if user_role == "pendiente":
            raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar el alumnado")

        if current_user and user_role not in ("coordinator", "coordinador", "admin"):
            assigned = {
                uuid.UUID(str(s).strip())
                for s in (current_user.get("sections") or [])
                if str(s).strip()
            }
            if not assigned:
                raise ForbiddenError("El tutor no tiene secciones asignadas")
            if requested_section_id is not None:
                if requested_section_id not in assigned:
                    raise ForbiddenError("El tutor no tiene permiso sobre la sección especificada")
                return [requested_section_id]
            return list(assigned)
        if requested_section_id is not None:
            return [requested_section_id]
        return None

    # ------------------------------------------------------------------ list (BE-27)

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

    def get_students_without_progress(
        self,
        current_user: Optional[Dict[str, Any]] = None,
        n_tests: int = 3,
        threshold: float = 0.0,
        metric: str = "ppm",
        section_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Detecta y lista los alumnos que no muestran progreso en las últimas N pruebas (BE-34).
        - Evalúa tendencia negativa (empeoran) y plana (por debajo de threshold) (Escenarios 1 y 2).
        - Separa estrictamente la categoría 'insufficient_data' sin mezclarla con 'no_progress' (Escenario 3).
        - Permite configurar parámetros n_tests, threshold y metric (Escenario 4).
        - Filtra estrictamente por el ámbito del tutor (solo alumnos de sus secciones asignadas) (Escenario 5).
        - Registra evento de auditoría DETECT_NO_PROGRESS_STUDENTS.
        """
        # 1. Comprobación de roles y permisos
        target_section_ids: Optional[List[uuid.UUID]] = None
        parsed_sec_id: Optional[uuid.UUID] = None

        if current_user:
            user_role = str(current_user.get("role", "")).strip().lower()
            if user_role == "pendiente":
                raise ForbiddenError("El usuario con rol pendiente no tiene permisos para consultar alumnos")

            if user_role not in ("coordinator", "coordinador", "admin"):
                # Tutor: ámbito restringido
                assigned_raw = current_user.get("sections") or []
                assigned_sections = {str(s).strip() for s in assigned_raw if str(s).strip()}

                if section_id:
                    try:
                        parsed_sec_id = (
                            section_id
                            if isinstance(section_id, uuid.UUID)
                            else uuid.UUID(str(section_id).strip())
                        )
                    except (ValueError, TypeError, AttributeError):
                        raise ValidationError(
                            "El identificador de la sección no es válido", field="section_id"
                        )

                    if str(parsed_sec_id) not in assigned_sections:
                        raise ForbiddenError("El tutor no tiene permiso sobre la sección especificada")
                    target_section_ids = [parsed_sec_id]
                else:
                    target_section_ids = []
                    for s in assigned_sections:
                        try:
                            target_section_ids.append(uuid.UUID(s))
                        except (ValueError, TypeError):
                            pass
            else:
                # Coordinador / Admin
                if section_id:
                    try:
                        parsed_sec_id = (
                            section_id
                            if isinstance(section_id, uuid.UUID)
                            else uuid.UUID(str(section_id).strip())
                        )
                        target_section_ids = [parsed_sec_id]
                    except (ValueError, TypeError, AttributeError):
                        raise ValidationError(
                            "El identificador de la sección no es válido", field="section_id"
                        )

        # 2. Consulta de alumnos según el ámbito
        query = (
            self.session.query(Student)
            .options(
                joinedload(Student.student_sections).joinedload(StudentSection.section),
                joinedload(Student.results).joinedload(Result.test),
            )
            .filter(Student.disabled_at.is_(None))
        )

        if target_section_ids is not None:
            if not target_section_ids:
                # Tutor sin secciones asignadas -> 0 alumnos
                empty_classification = classify_students_progress(
                    [], n_tests=n_tests, threshold=threshold, metric=metric
                )
                return ProgressDetectionSchema.dump(empty_classification)

            query = query.join(Student.student_sections).filter(
                StudentSection.section_id.in_(target_section_ids)
            ).distinct()

        students = query.order_by(Student.name.asc()).all()

        # 3. Construir conjunto de datos de alumnos con sus resultados
        students_data = []
        for student in students:
            # Obtener sección actual o primera asignada
            current_sec = None
            for ss in student.student_sections:
                if ss.section and ss.section.disabled_at is None:
                    current_sec = ss.section
                    break
            if not current_sec and student.student_sections:
                current_sec = student.student_sections[0].section

            # Resultados de pruebas con métricas
            formatted_results = []
            for r in student.results:
                if parsed_sec_id and str(r.section_id) != str(parsed_sec_id):
                    continue

                ppm = calculate_ppm(r.test.words, r.time) if r.test and r.time > 0 else 0.0
                acc = calculate_reading_comprehension(r.successes, r.mistakes)
                formatted_results.append(
                    {
                        "test_date": r.test_date.isoformat() if r.test_date else None,
                        "ppm": ppm,
                        "accuracy": acc,
                        "test_name": r.test.name if r.test else "",
                    }
                )

            formatted_results.sort(key=lambda x: str(x.get("test_date") or ""))

            students_data.append(
                {
                    "student": {
                        "id": str(student.id),
                        "name": student.name,
                        "external_id": student.external_id,
                    },
                    "section": {
                        "id": str(current_sec.id) if current_sec else "",
                        "name": current_sec.name if current_sec else "Sin sección",
                    },
                    "results": formatted_results,
                }
            )

        # 4. Clasificar alumnos
        classification = classify_students_progress(
            students_data=students_data,
            n_tests=n_tests,
            threshold=threshold,
            metric=metric,
        )

        # 5. Registrar evento de auditoría
        log_audit(
            user=current_user,
            action="DETECT_NO_PROGRESS_STUDENTS",
            resource_type="students",
            resource_id=str(section_id) if section_id else "all",
            details={
                "n_tests": n_tests,
                "threshold": threshold,
                "metric": metric,
                "section_id": str(section_id) if section_id else None,
                "total_students": classification["total_students"],
                "no_progress_count": classification["no_progress_count"],
                "insufficient_data_count": classification["insufficient_data_count"],
            },
        )


        # 6. Serializar y devolver
        return ProgressDetectionSchema.dump(classification)

    # ------------------------------------------------------------------ BE-27

    def list_students(
        self,
        filters: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Listado paginado del alumnado con filtros combinables (BE-27).

        - Rol ``pendiente`` siempre rechazado.
        - Tutor: ámbito forzado a sus secciones; 403 si no tiene ninguna o
          si solicita una sección fuera de su ámbito (Escenario 6).
        - Registro de auditoría ``FILTER_STUDENTS`` cuando se filtra por
          ``academic_status`` por contener datos sensibles del menor.
        - ``missing_data`` indica cuántos alumnos del ámbito no tenían
          informado cada campo filtrado (Escenario 5).
        """
        # 1. Resolución del ámbito por rol (Escenario 6)
        repo_filters = dict(filters)
        section_id = repo_filters.pop("section_id", None)
        page = repo_filters.pop("page", 1)
        limit = repo_filters.pop("limit", 10)

        parsed_section = uuid.UUID(str(section_id)) if section_id is not None else None
        section_ids = self._resolve_scope(current_user, parsed_section)
        if section_ids is not None:
            repo_filters["section_ids"] = section_ids

        # 3. Consulta al repositorio
        repo = StudentRepository(self.session)
        students, total = repo.filter_students(
            repo_filters, page=page, limit=limit
        )

        # 4. Último resultado por alumno (PPM y comprensión lectora)
        last_results_map: Dict[uuid.UUID, Result] = {}
        if students:
            student_ids = [s.id for s in students]
            stmt = (
                select(Result)
                .where(Result.student_id.in_(student_ids))
                .join(Result.test)
                .order_by(Result.student_id, Result.test_date.desc())
            )
            seen: set = set()
            for r in self.session.scalars(stmt).all():
                if r.student_id not in seen:
                    last_results_map[r.student_id] = r
                    seen.add(r.student_id)

        # 5. Construcción de la respuesta paginada
        items: List[Dict[str, Any]] = []
        for s in students:
            lr = last_results_map.get(s.id)
            current_section_names = [
                ss.section.name
                for ss in (s.student_sections or [])
                if ss.section and ss.section.disabled_at is None
            ] or ["Sin sección"]
            ppm = calculate_ppm(lr.test.words, lr.time) if lr and lr.test and lr.time > 0 else None
            acc = calculate_reading_comprehension(lr.successes, lr.mistakes) if lr else None
            items.append({
                "id": s.id,
                "name": s.name,
                "external_id": s.external_id,
                "sections": current_section_names,
                "test_date": lr.test_date if lr else None,
                "ppm": ppm,
                "reading_comprehension": acc,
            })

        # 6. Conteo de alumnos sin datos (Escenario 5)
        missing_data: Dict[str, int] = {}
        for field in ("academic_status", "sector"):
            value = repo_filters.get(field)
            if value is not None and value != MISSING_VALUE:
                missing_data[field] = repo.count_students_missing_field(field, repo_filters)

        # 7. Auditoría sobre datos sensibles del menor
        sensitive = any(
            repo_filters.get(f) not in (None, MISSING_VALUE)
            for f in ("academic_status",)
        )
        if sensitive:
            log_audit(
                user=current_user,
                action="FILTER_STUDENTS",
                resource_type="students",
                resource_id="list",
                details={k: str(v) for k, v in repo_filters.items() if k not in ("page", "limit", "section_ids")},
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 1,
            "missing_data": missing_data,
        }

    # ------------------------------------------------------------------ search (BE-29)

    def search_students(
        self,
        term: str,
        page: int,
        limit: int,
        current_user: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Búsqueda de alumnos por fragmento de nombre (BE-29).

        - Normalización de acentos y mayúsculas en la consulta (T-BE29-01).
        - Respuesta incluye secciones activas con su centro (T-BE29-02).
        - Tutor: ámbito restringido a sus secciones (T-BE29-03 / Esc. 5).
        """
        section_ids = self._resolve_scope(current_user)
        repo = StudentRepository(self.session)
        students, total = repo.search_students(
            term, section_ids=section_ids, page=page, limit=limit,
        )

        items: List[Dict[str, Any]] = []
        for s in students:
            active_sections = [
                {
                    "id": ss.section.id,
                    "name": ss.section.name,
                    "center": ss.section.center.name if ss.section.center else None,
                    "center_id": ss.section.center_id,
                }
                for ss in (s.student_sections or [])
                if ss.section and ss.section.disabled_at is None
            ]
            items.append({
                "id": s.id,
                "name": s.name,
                "external_id": s.external_id,
                "sections": active_sections,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 1,
        }


