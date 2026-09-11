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

try:
    from app.analytics.evolution import calculate_individual_evolution

    __all__ = [
        "calculate_ppm",
        "calculate_accuracy",
        "calculate_reading_comprehension",
        "calculate_effective_speed",
        "calculate_metrics_from_result",
        "calculate_individual_evolution",
    ]
except ImportError:
    __all__ = [
        "calculate_ppm",
        "calculate_accuracy",
        "calculate_reading_comprehension",
        "calculate_effective_speed",
        "calculate_metrics_from_result",
    ]

