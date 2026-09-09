import pytest
from app.analytics.metrics import calculate_accuracy, calculate_ppm


def test_calculate_ppm_scenario_1():
    """
    Escenario 1: Dado una prueba de 835 palabras y un tiempo de 300 segundos,
    se devuelven 167 palabras por minuto.
    """
    ppm = calculate_ppm(word_count=835, time_seconds=300)
    assert ppm == 167.0


def test_calculate_accuracy_scenario_2():
    """
    Escenario 2: Dado un resultado con 8 aciertos y 2 errores (total 10),
    el porcentaje devuelto es 80%.
    """
    # 8 aciertos de 10 preguntas totales
    accuracy = calculate_accuracy(correct_answers=8, total_questions=10)
    assert accuracy == 80.0


def test_calculate_ppm_zero_or_negative_time_scenario_3():
    """
    Escenario 3: Dado un resultado cuyo tiempo es cero o negativo,
    no se lanza excepción y devuelve 0.0.
    """
    assert calculate_ppm(word_count=835, time_seconds=0) == 0.0
    assert calculate_ppm(word_count=835, time_seconds=-10) == 0.0


def test_calculate_accuracy_zero_questions_scenario_4():
    """
    Escenario 4: Dado un resultado con 0 aciertos y 0 total de preguntas,
    no se lanza excepción y devuelve 0.0.
    """
    assert calculate_accuracy(correct_answers=0, total_questions=0) == 0.0


def test_calculate_ppm_edge_cases():
    """Casos límite adicionales para PPM."""
    assert calculate_ppm(word_count=0, time_seconds=60) == 0.0
    assert calculate_ppm(word_count=-100, time_seconds=60) == 0.0


def test_calculate_accuracy_edge_cases():
    """Casos límite adicionales para porcentaje de aciertos."""
    # Aciertos negativos
    assert calculate_accuracy(correct_answers=-1, total_questions=10) == 0.0
    # Total de preguntas negativo
    assert calculate_accuracy(correct_answers=5, total_questions=-5) == 0.0
    # Aciertos superiores al total (datos anómalos, clamp a 100%)
    assert calculate_accuracy(correct_answers=15, total_questions=10) == 100.0
