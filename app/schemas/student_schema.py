from typing import Any, Dict, List, Optional
from app.models.student import Student


class StudentDetailSchema:
    """
    Serializador agregado para la ficha completa del alumno (BE-28).
    Compone en un único payload:
    - Datos personales del alumno.
    - Secciones actuales e históricas distinguidas claramente.
    - Resultados de pruebas con métricas derivadas (PPM, eficacia/aciertos).
    - Historial de lecturas con estado y datos del libro.
    """

    @classmethod
    def dump(
        cls,
        student: Student,
        current_sections: List[Dict[str, Any]],
        historical_sections: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        readings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "id": str(student.id),
            "external_id": student.external_id,
            "name": student.name,
            "birth_date": student.birth_date.isoformat() if student.birth_date else None,
            "age": student.age,
            "gender": student.gender,
            "academic_status": student.academic_status,
            "sector": student.sector,
            "disabled_at": student.disabled_at.isoformat() if student.disabled_at else None,
            "sections": {
                "current": current_sections,
                "historical": historical_sections,
            },
            "current_sections": current_sections,
            "historical_sections": historical_sections,
            "results": results,
            "readings": readings,
            "total_results": len(results),
            "total_readings": len(readings),
        }
