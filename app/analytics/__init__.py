"""
Módulo de analítica y métricas derivadas.
Contiene funciones puras para el cálculo de métricas de comprensión lectora y evolución individual.
"""

from app.analytics.evolution import calculate_individual_evolution
from app.analytics.metrics import calculate_accuracy, calculate_ppm

__all__ = ["calculate_ppm", "calculate_accuracy", "calculate_individual_evolution"]
