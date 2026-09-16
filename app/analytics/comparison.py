"""
Módulo analítico puro para la comparativa de evolución por grupos (BE-32).

Agrupa resultados por sección, centro o perfil (sector) y monta la respuesta de
comparativa reutilizando los agregados de grupo de BE-37
(``calculate_group_aggregates``). Este módulo es independiente y no importa
dependencias de base de datos ni de Flask.
"""

from typing import Any, Dict, List, Optional

from app.analytics.group_report import calculate_group_aggregates


def build_group_comparison(
    groups_data: List[Dict[str, Any]],
    min_sample: int,
) -> List[Dict[str, Any]]:
    """
    Construye los items de una comparativa a partir de los resultados agrupados.

    :param groups_data: Lista de grupos en la forma::

        {
            "id": str,
            "name": str,
            "group_by": "section" | "center" | "profile",
            "center_id": Optional[str],
            "center_name": Optional[str],
            "results": [{"student_id", "ppm", "accuracy", "vef"}, ...],
        }

    :param min_sample: Mínimo de alumnos con datos para considerar representativo
        a un grupo (configurable, BE-32 Notas).
    :return: Lista de items de comparativa con medias, tamaños de muestra,
        representatividad y advertencia si corresponde.
    """
    items: List[Dict[str, Any]] = []

    for group in groups_data:
        aggregates = calculate_group_aggregates(group.get("results") or [])
        has_data = bool(aggregates.get("has_data"))
        students_count = int(aggregates.get("participants_count", 0))
        results_count = int(aggregates.get("results_count", 0))

        # Representatividad: con datos y al menos el mínimo de alumnos (Escenario 3).
        # El umbral aplica sobre la muestra medida, no sobre el censo del grupo.
        is_representative = has_data and students_count >= min_sample

        if not has_data:
            # Escenario 5: sin datos se indica ausencia, nunca una media de cero.
            warning = "Grupo sin resultados registrados"
        elif not is_representative:
            warning = (
                f"Grupo poco representativo: menos de {min_sample} alumnos "
                "con resultados"
            )
        else:
            warning = None

        items.append(
            {
                "id": group.get("id"),
                "name": group.get("name"),
                "group_by": group.get("group_by"),
                "center_id": group.get("center_id"),
                "center_name": group.get("center_name"),
                "has_data": has_data,
                "students_count": students_count,
                "results_count": results_count,
                "mean_ppm": aggregates.get("mean_ppm"),
                "mean_accuracy": aggregates.get("mean_accuracy"),
                "mean_vef": aggregates.get("mean_vef"),
                "is_representative": is_representative,
                "warning": warning,
            }
        )

    return items


def empty_group(
    group_id: Optional[str],
    name: str,
    group_by: str,
    min_sample: int,
    center_id: Optional[str] = None,
    center_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Item de comparativa para un grupo sin resultados (Escenario 5)."""
    return build_group_comparison(
        [
            {
                "id": group_id,
                "name": name,
                "group_by": group_by,
                "center_id": center_id,
                "center_name": center_name,
                "results": [],
            }
        ],
        min_sample,
    )[0]