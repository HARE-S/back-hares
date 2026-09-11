"""Servicios de métricas de par para análisis de progreso."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.test import Result
from app.models.student import Student
from app.analytics.pairs import (
    build_pair_series,
    calculate_progress,
    summarize_group_progress,
)
from app.repositories.result_repository import ResultRepository


class PairMetricsService:
    """Calcula y expone métricas de par (funcional/literario) por alumno y grupo."""

    def __init__(self, session: Session):
        self.session = session
        self.result_repo = ResultRepository(session)

    def get_student_pair_series(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Serie de pares por letra de prueba para un alumno.

        Agrupa resultados por test_letter (I, A, B, C, D, E), toma el más reciente
        de cada tipo (F/L), y devuelve mean, difference, is_complete por par.

        :param student_id: UUID del alumno
        :return: Lista de pares ordenados pedagógicamente, con media y diferencia
        """
        stmt = self.session.query(Result).filter(Result.student_id == student_id)
        results = stmt.all()

        # Construir dicts con los campos que build_pair_series espera
        result_dicts = [
            {
                "test_letter": r.test.test_letter,
                "type": r.test.type,
                "vef": self._calculate_vef(r),
                "test_date": r.test_date,
            }
            for r in results
            if r.test.test_letter and r.test.type
        ]

        return build_pair_series(result_dicts)

    def get_student_progress(self, student_id: str) -> Dict[str, Any]:
        """
        Progresión individual: transiciones y global.

        :param student_id: UUID del alumno
        :return: Transiciones (I-A, A-B, etc.), global_progress, measured_span, tests_with_data
        """
        series = self.get_student_pair_series(student_id)
        return calculate_progress(series)

    def get_group_progress(self, section_id: str) -> Dict[str, Any]:
        """
        Progresión de un grupo: porcentaje de alumnos que mejoran.

        :param section_id: UUID de la sección
        :return: Transiciones con improved (count, measurable, percentage) y global
        """
        # Obtener todos los alumnos de la sección
        stmt = (
            self.session.query(Student)
            .join(Student.sections)
            .filter(Student.sections.any(id=section_id))
        )
        students = stmt.all()

        # Serie de pares para cada alumno
        students_series = [self.get_student_pair_series(str(s.id)) for s in students]

        return summarize_group_progress(students_series)

    def _calculate_vef(self, result: Result) -> Optional[float]:
        """Calcula Vef (velocidad eficaz) a partir de un resultado."""
        if not result.time or result.time <= 0:
            return None

        # PPM = palabras / minutos
        minutes = result.time / 60.0
        ppm = result.test.words / minutes if minutes > 0 else 0

        # Comprensión = (aciertos - errores/2) / 20 * 100
        correct_minus_half_errors = result.successes - (result.mistakes / 2.0)
        comprehension = (correct_minus_half_errors / 20.0) * 100.0

        # Vef = PPM * (comprehension / 100)
        vef = ppm * (comprehension / 100.0)
        return round(vef, 2) if vef >= 0 else None
