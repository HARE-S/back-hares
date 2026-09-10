"""
Módulo de proyección de evolución individual (BE-33).

Calcula tendencias y proyecciones a partir de series históricas de resultados.
Función pura, sin dependencias de base de datos ni Flask.
"""

from typing import Any, Dict, List, Optional
from app.analytics.evolution import calculate_individual_evolution


def calculate_evolution_projection(
    results: List[Dict[str, Any]],
    min_tests: int = 3,
) -> Dict[str, Any]:
    """
    Calcula proyección de evolución a partir de una serie de resultados.

    Implementa regresión lineal simple (mínimos cuadrados) sobre PPM y comprensión,
    marcando explícitamente los valores proyectados como estimaciones.

    :param results: Lista de resultados con datos de pruebas.
    :param min_tests: Mínimo de pruebas requeridas para proyectar (default 3).
    :return: Diccionario con serie temporal, proyección (si es posible) y mensajes.
    """
    # Construir serie temporal
    evolution = calculate_individual_evolution(results)

    if evolution["has_insufficient_data"]:
        return {
            "has_projection": False,
            "message": f"Se necesitan al menos {min_tests} pruebas para calcular proyección. "
                       f"Datos actuales: {evolution['total_tests']}.",
            "based_on_tests": evolution["total_tests"],
            "time_series": evolution["time_series"],
            "trend": None,
        }

    time_series = evolution["time_series"]
    if len(time_series) < min_tests:
        return {
            "has_projection": False,
            "message": f"Se necesitan al menos {min_tests} pruebas. Datos actuales: {len(time_series)}.",
            "based_on_tests": len(time_series),
            "time_series": time_series,
            "trend": None,
        }

    # Regresión lineal simple: índice de prueba (0, 1, 2, ...) vs métrica
    n = len(time_series)
    x_indices = list(range(n))  # 0, 1, 2, ..., n-1

    # Extraer PPM y comprensión
    ppm_values = [item["ppm"] for item in time_series]
    comprehension_values = [item["accuracy"] for item in time_series]

    # Regresión para PPM
    ppm_slope, ppm_intercept = _linear_regression(x_indices, ppm_values)

    # Regresión para comprensión
    comprehension_slope, comprehension_intercept = _linear_regression(
        x_indices, comprehension_values
    )

    return {
        "has_projection": True,
        "message": f"Proyección calculada sobre {n} pruebas.",
        "based_on_tests": n,
        "time_series": time_series,
        "trend": {
            "ppm": {
                "slope": round(ppm_slope, 4),
                "intercept": round(ppm_intercept, 2),
                "is_estimation": True,
            },
            "comprehension": {
                "slope": round(comprehension_slope, 4),
                "intercept": round(comprehension_intercept, 2),
                "is_estimation": True,
            },
        },
    }


def _linear_regression(x: List[float], y: List[float]) -> tuple:
    """
    Calcula regresión lineal simple (mínimos cuadrados).

    Devuelve (pendiente, intercepto) de y = pendiente*x + intercepto.

    :param x: Lista de valores x (índices de tiempo).
    :param y: Lista de valores y (métrica).
    :return: Tupla (pendiente, intercepto).
    """
    if len(x) < 2:
        return (0.0, y[0] if y else 0.0)

    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)

    # Fórmula: pendiente = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x^2)
    denominator = n * sum_x2 - sum_x**2

    if denominator == 0:
        # Todos los x tienen el mismo valor (tendencia plana)
        return (0.0, sum_y / n)

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    return (slope, intercept)
