"""
Módulo analítico puro para la detección de alumnos sin progreso (BE-34).

Implementa:
- Clasificación de alumnos según su tendencia en las últimas N pruebas.
- Distinción estricta de "sin datos suficientes" (< N pruebas) frente a "sin progreso" (Escenario 3).
- Identificación de tendencia negativa (empeora) y tendencia plana (debajo de umbral) (Escenarios 1 y 2).
- Parámetros totalmente configurables (n_tests, threshold, metric) (Escenario 4).
- Función pura, desacoplada de base de datos y de Flask.
"""

from typing import Any, Dict, List, Optional
from app.analytics.projection import _linear_regression


def classify_student_trend(
    results: List[Dict[str, Any]],
    n_tests: int = 3,
    threshold: float = 0.0,
    metric: str = "ppm",
) -> Dict[str, Any]:
    """
    Clasifica la tendencia de un alumno a partir de su serie de resultados.

    :param results: Lista de resultados del alumno ordenados cronológicamente.
    :param n_tests: Número de pruebas recientes a evaluar (mínimo 2, default 3).
    :param threshold: Umbral de pendiente/variación para considerar tendencia plana (default 0.0).
    :param metric: Métrica evaluada ('ppm' o 'accuracy' / 'comprehension').
    :return: Diccionario con clasificación ('no_progress', 'insufficient_data', 'progress'),
             tipo de tendencia ('negative', 'flat', 'positive') y valores numéricos.
    """
    effective_n = max(2, int(n_tests))
    total_tests = len(results)

    # Escenario 3: Si tiene menos pruebas que las requeridas, es estrictamente "sin datos suficientes"
    if total_tests < effective_n:
        return {
            "classification": "insufficient_data",
            "has_sufficient_data": False,
            "trend_type": None,
            "total_tests": total_tests,
            "required_tests": effective_n,
            "slope": None,
            "variation": None,
            "first_value": None,
            "last_value": None,
            "recent_results": results,
            "reason": (
                f"El alumno tiene {total_tests} prueba(s) registrada(s), "
                f"se requieren al menos {effective_n} para evaluar progreso."
            ),
        }

    # Evaluar la ventana de las últimas N pruebas
    eval_results = results[-effective_n:]

    # Extraer valores numéricos de la métrica objetivo
    metric_key = metric.strip().lower()
    if metric_key in ("accuracy", "comprehension", "precision"):
        values = [
            float(r.get("accuracy", r.get("comprehension", 0.0)) or 0.0)
            for r in eval_results
        ]
    else:
        values = [float(r.get("ppm", 0.0) or 0.0) for r in eval_results]

    # Regresión lineal sobre los índices temporales [0, 1, ..., N-1]
    x_indices = list(range(len(values)))
    slope, intercept = _linear_regression(x_indices, values)
    slope = round(float(slope), 4)

    first_val = round(float(values[0]), 2)
    last_val = round(float(values[-1]), 2)
    variation = round(float(last_val - first_val), 2)

    # Clasificación pedagógica:
    # 1. Pendiente negativa -> Empeora (Escenario 1)
    if slope < 0.0 or variation < 0.0:
        trend_type = "negative"
        classification = "no_progress"
    # 2. Pendiente o variación en o por debajo del umbral -> Plana / Sin mejora (Escenario 2)
    elif slope <= float(threshold) or variation <= float(threshold):
        trend_type = "flat"
        classification = "no_progress"
    # 3. Supera el umbral -> Mejora / Con progreso
    else:
        trend_type = "positive"
        classification = "progress"

    return {
        "classification": classification,
        "has_sufficient_data": True,
        "trend_type": trend_type,
        "total_tests": total_tests,
        "evaluated_tests": effective_n,
        "slope": slope,
        "variation": variation,
        "first_value": first_val,
        "last_value": last_val,
        "recent_results": eval_results,
    }


def classify_students_progress(
    students_data: List[Dict[str, Any]],
    n_tests: int = 3,
    threshold: float = 0.0,
    metric: str = "ppm",
) -> Dict[str, Any]:
    """
    Clasifica a un grupo de alumnos separando rigurosamente a quienes no progresan
    de quienes no tienen datos suficientes.

    :param students_data: Lista de diccionarios, cada uno con 'student' (o id/nombre) y 'results'.
    :param n_tests: Parámetro N de pruebas recientes a considerar.
    :param threshold: Umbral de pendiente/variación.
    :param metric: Métrica objetivo ('ppm' o 'accuracy').
    :return: Diccionario estructurado con listas separadas: no_progress, insufficient_data, improving.
    """
    no_progress_list = []
    insufficient_data_list = []
    improving_list = []

    for item in students_data:
        student_info = item.get("student") or {
            "id": item.get("id"),
            "name": item.get("name"),
            "external_id": item.get("external_id"),
        }
        section_info = item.get("section") or {
            "id": item.get("section_id"),
            "name": item.get("section_name"),
        }
        results = item.get("results", [])

        # Asegurar orden cronológico si traen fechas
        def _get_date(r):
            d = r.get("test_date") or r.get("date") or ""
            return str(d)

        sorted_results = sorted(results, key=_get_date)

        trend_result = classify_student_trend(
            results=sorted_results,
            n_tests=n_tests,
            threshold=threshold,
            metric=metric,
        )

        entry = {
            "student_id": str(student_info.get("id", "")),
            "student_name": student_info.get("name", "N/A"),
            "external_id": student_info.get("external_id"),
            "section_id": str(section_info.get("id", "") or ""),
            "section_name": section_info.get("name", "N/A"),
            "total_tests": trend_result["total_tests"],
            "classification": trend_result["classification"],
            "trend_type": trend_result["trend_type"],
            "slope": trend_result["slope"],
            "variation": trend_result["variation"],
            "first_value": trend_result["first_value"],
            "last_value": trend_result["last_value"],
            "metric": metric,
            "has_sufficient_data": trend_result["has_sufficient_data"],
            "reason": trend_result.get("reason"),
        }

        classification = trend_result["classification"]
        if classification == "no_progress":
            no_progress_list.append(entry)
        elif classification == "insufficient_data":
            insufficient_data_list.append(entry)
        else:
            improving_list.append(entry)

    return {
        "parameters": {
            "n_tests": max(2, int(n_tests)),
            "threshold": float(threshold),
            "metric": metric.strip().lower(),
        },
        "total_students": len(students_data),
        "no_progress_count": len(no_progress_list),
        "insufficient_data_count": len(insufficient_data_list),
        "improving_count": len(improving_list),
        "no_progress": no_progress_list,
        "insufficient_data": insufficient_data_list,
        "improving": improving_list,
    }
