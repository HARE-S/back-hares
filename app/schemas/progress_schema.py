import datetime
from typing import Any, Dict, Optional


class ProgressDetectionSchema:
    """
    Serializador para la respuesta de detección de alumnos sin progreso (BE-34).
    Garantiza la separación estricta entre 'no_progress' y 'insufficient_data'.
    """

    @classmethod
    def dump(
        cls,
        classification_result: Dict[str, Any],
        generated_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        if generated_at is None:
            generated_at = datetime.datetime.now(datetime.timezone.utc)

        return {
            "parameters": classification_result.get("parameters", {}),
            "total_students": classification_result.get("total_students", 0),
            "no_progress_count": classification_result.get("no_progress_count", 0),
            "insufficient_data_count": classification_result.get(
                "insufficient_data_count", 0
            ),
            "improving_count": classification_result.get("improving_count", 0),
            "no_progress": classification_result.get("no_progress", []),
            "insufficient_data": classification_result.get("insufficient_data", []),
            "improving": classification_result.get("improving", []),
            "generated_at": generated_at.isoformat(),
        }
