"""
Módulo de analítica y métricas derivadas.

Implementa la Batería de Lectura Eficaz (Bruño):
- VE (velocidad espontánea): palabras/minuto
- CL (comprensión lectora): % con penalización de errores
- Vef (velocidad eficaz): palabras leídas Y comprendidas/minuto
- Evolución individual: series temporales y análisis de progresión (BE-31)

Contiene funciones puras para el cálculo de métricas de comprensión lectora y evolución individual.
"""

from app.analytics.metrics import (
    calculate_accuracy,
    calculate_effective_speed,
    calculate_metrics_from_result,
    calculate_ppm,
    calculate_reading_comprehension,
)
from app.analytics.pairs import (
    TEST_LETTER_ORDER,
    build_pair_series,
    calculate_pair,
    calculate_progress,
    summarize_group_progress,
)

try:
    from app.analytics.evolution import calculate_individual_evolution

    __all__ = [
        "calculate_ppm",
        "calculate_accuracy",
        "calculate_reading_comprehension",
        "calculate_effective_speed",
        "calculate_metrics_from_result",
        "calculate_individual_evolution",
        "TEST_LETTER_ORDER",
        "calculate_pair",
        "build_pair_series",
        "calculate_progress",
        "summarize_group_progress",
    ]
except ImportError:
    __all__ = [
        "calculate_ppm",
        "calculate_accuracy",
        "calculate_reading_comprehension",
        "calculate_effective_speed",
        "calculate_metrics_from_result",
        "TEST_LETTER_ORDER",
        "calculate_pair",
        "build_pair_series",
        "calculate_progress",
        "summarize_group_progress",
    ]

