import datetime
from typing import Any, Dict, Optional


class StudentReportSchema:
    """
    Serializador para el informe individual de un alumno (BE-36).
    Compone:
    - Datos personales del alumno y secciones (BE-28).
    - Historial de pruebas con métricas (PPM, comprensión, aciertos) y lecturas.
    - Serie de evolución temporal y variaciones calculadas (BE-31).
    - Indicador de datos suficientes/insuficientes (Escenario 3).
    - Fecha y hora de generación (Escenario 2).
    """

    @classmethod
    def dump(
        cls,
        student_card: Dict[str, Any],
        evolution: Dict[str, Any],
        generated_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        if generated_at is None:
            generated_at = datetime.datetime.now(datetime.timezone.utc)

        student_info = {
            "id": student_card["id"],
            "external_id": student_card.get("external_id"),
            "name": student_card.get("name"),
            "birth_date": student_card.get("birth_date"),
            "age": student_card.get("age"),
            "gender": student_card.get("gender"),
            "academic_status": student_card.get("academic_status"),
            "sector": student_card.get("sector"),
            "disabled_at": student_card.get("disabled_at"),
        }

        has_insufficient_data = bool(evolution.get("has_insufficient_data", False))

        return {
            "id": student_card["id"],
            "name": student_card.get("name"),
            "birth_date": student_card.get("birth_date"),
            "age": student_card.get("age"),
            "gender": student_card.get("gender"),
            "academic_status": student_card.get("academic_status"),
            "sector": student_card.get("sector"),
            "student": student_info,
            "sections": student_card.get("sections", {}),
            "current_sections": student_card.get("current_sections", []),
            "historical_sections": student_card.get("historical_sections", []),
            "results": student_card.get("results", []),
            "readings": student_card.get("readings", []),
            "evolution": evolution,
            "has_insufficient_data": has_insufficient_data,
            "projection": None,
            "generated_at": generated_at.isoformat(),
        }


class GroupReportSchema:
    """
    Serializador para el informe agregado de una sección/grupo (BE-37).
    """

    @classmethod
    def dump(
        cls,
        section: Any,
        aggregates: Dict[str, Any],
        generated_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        if generated_at is None:
            generated_at = datetime.datetime.now(datetime.timezone.utc)

        return {
            "section_id": str(section.id),
            "name": section.name,
            "external_id": getattr(section, "external_id", None),
            "academic_year": getattr(section, "academic_year", None),
            "center_id": str(section.center_id) if getattr(section, "center_id", None) else None,
            "has_data": aggregates.get("has_data", False),
            "participants_count": aggregates.get("participants_count", 0),
            "results_count": aggregates.get("results_count", 0),
            "mean_ppm": aggregates.get("mean_ppm"),
            "mean_accuracy": aggregates.get("mean_accuracy"),
            "mean_vef": aggregates.get("mean_vef"),
            "distribution": aggregates.get("distribution"),
            "generated_at": generated_at.isoformat(),
        }


class CenterReportSchema:
    """
    Serializador para el informe agregado de un centro completo (BE-37).
    Incluye datos del conjunto y desglose por sección (Escenario 3).
    """

    @classmethod
    def dump(
        cls,
        center: Any,
        aggregates: Dict[str, Any],
        sections_breakdown: Any,
        generated_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        if generated_at is None:
            generated_at = datetime.datetime.now(datetime.timezone.utc)

        return {
            "center_id": str(center.id),
            "name": center.name,
            "external_id": getattr(center, "external_id", None),
            "has_data": aggregates.get("has_data", False),
            "participants_count": aggregates.get("participants_count", 0),
            "results_count": aggregates.get("results_count", 0),
            "mean_ppm": aggregates.get("mean_ppm"),
            "mean_accuracy": aggregates.get("mean_accuracy"),
            "mean_vef": aggregates.get("mean_vef"),
            "distribution": aggregates.get("distribution"),
            "sections": sections_breakdown,
            "generated_at": generated_at.isoformat(),
        }

