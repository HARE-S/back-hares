import pytest
from app.analytics.metrics import (
    calculate_accuracy,
    calculate_effective_speed,
    calculate_ppm,
    calculate_reading_comprehension,
)


# ============================================================================
# BE-30 Escenario 1: Cálculo del PPM
# ============================================================================


def test_calculate_ppm_scenario_1():
    """
    Escenario 1: Cálculo del PPM.
    Dado una prueba de 835 palabras y un resultado con 300 segundos de tiempo,
    cuando se calcula el PPM, entonces el valor devuelto es 167 palabras por minuto.
    """
    ppm = calculate_ppm(word_count=835, time_seconds=300)
    assert ppm == 167.0


# ============================================================================
# BE-30 Escenario 2: Porcentaje de comprensión con penalización
# ============================================================================


def test_calculate_reading_comprehension_scenario_2_simple():
    """
    Escenario 2a: Caso simple sin penalización.
    Dado un resultado con 15 aciertos y 0 fallos (20 preguntas totales, 5 en blanco),
    cuando se calcula CL, entonces el valor devuelto es 75% (15/20×100).
    """
    cl = calculate_reading_comprehension(correct_answers=15, mistakes=0, unanswered=5)
    assert cl == 75.0


def test_calculate_reading_comprehension_scenario_2_with_penalty():
    """
    Escenario 2b: Con penalización de falsos positivos.
    Dado un resultado con 15 aciertos y 3 fallos (20 preguntas totales, 2 en blanco),
    cuando se calcula CL con penalización (P = 15 − 3/2 = 13.5),
    entonces el valor devuelto es 67.5% (13.5/20×100).

    Este es el caso que diferencia la Batería Bruño: penaliza los errores.
    """
    cl = calculate_reading_comprehension(correct_answers=15, mistakes=3, unanswered=2)
    assert cl == 67.5


def test_calculate_reading_comprehension_perfect():
    """
    Perfección: 20 aciertos, 0 fallos.
    Cuando se calcula CL, entonces devuelve 100%.
    """
    cl = calculate_reading_comprehension(correct_answers=20, mistakes=0)
    assert cl == 100.0


def test_calculate_reading_comprehension_zero():
    """
    Cero aciertos: 0 aciertos, cualquier número de fallos.
    Cuando se calcula CL, entonces devuelve 0%.
    """
    cl = calculate_reading_comprehension(correct_answers=0, mistakes=10)
    assert cl == 0.0


def test_calculate_reading_comprehension_high_penalty():
    """
    Alta penalización: 10 aciertos, 10 fallos (P = 10 − 5 = 5, CL = 25%).
    Cuando se calcula CL, entonces devuelve 25%.
    """
    cl = calculate_reading_comprehension(correct_answers=10, mistakes=10)
    assert cl == 25.0


# ============================================================================
# BE-30 Escenario 3: Tiempo cero
# ============================================================================


def test_calculate_ppm_scenario_3_zero_time():
    """
    Escenario 3: Tiempo cero.
    Dado un resultado cuyo tiempo es cero,
    cuando se calcula el PPM, entonces la función no lanza ninguna excepción
    y devuelve 0.0.
    """
    assert calculate_ppm(word_count=835, time_seconds=0) == 0.0


def test_calculate_ppm_scenario_3_negative_time():
    """
    Escenario 3 (extensión): Tiempo negativo.
    Dado un resultado cuyo tiempo es negativo,
    cuando se calcula el PPM, entonces la función no lanza ninguna excepción
    y devuelve 0.0.
    """
    assert calculate_ppm(word_count=835, time_seconds=-10) == 0.0


# ============================================================================
# BE-30 Escenario 4: Sin aciertos ni errores
# ============================================================================


def test_calculate_reading_comprehension_scenario_4_zero_input():
    """
    Escenario 4: Sin aciertos ni errores (0 aciertos, 0 fallos).
    Dado un resultado con cero aciertos y cero errores,
    cuando se calcula el porcentaje de comprensión,
    entonces la función no lanza ninguna excepción y devuelve 0.0.
    """
    cl = calculate_reading_comprehension(correct_answers=0, mistakes=0)
    assert cl == 0.0


# ============================================================================
# BE-30 Escenario 5 (extendido): Vef - Velocidad Eficaz
# ============================================================================


def test_calculate_effective_speed_scenario_5a():
    """
    Escenario 5a: Cálculo de velocidad eficaz.
    Dado PPM=174.4 y CL=67.5%,
    cuando se calcula Vef = (174.4 × 67.5) / 100,
    entonces devuelve 117.72 palabras leídas y comprendidas por minuto.

    Este es el escenario real del documento: la métrica que importa es Vef, no PPM.
    Con Vef=117.72, el alumno está por debajo del nivel medio (125-150 para 2º ESO).
    """
    vef = calculate_effective_speed(ppm=174.4, comprehension=67.5)
    assert vef == 117.72


def test_calculate_effective_speed_perfect():
    """
    Escenario 5b: Velocidad eficaz perfecta (lector excelente).
    Dado PPM=200 y CL=100%,
    cuando se calcula Vef,
    entonces devuelve 200.0 (mismo PPM, porque la comprensión es perfecta).
    """
    vef = calculate_effective_speed(ppm=200.0, comprehension=100.0)
    assert vef == 200.0


def test_calculate_effective_speed_low_comprehension():
    """
    Escenario 5c: Lector rápido pero que no entiende.
    Dado PPM=300 pero CL=20% (apenas comprende lo que lee),
    cuando se calcula Vef,
    entonces devuelve 60.0 (mucho menos que el PPM bruto).
    """
    vef = calculate_effective_speed(ppm=300.0, comprehension=20.0)
    assert vef == 60.0


def test_calculate_effective_speed_zero():
    """
    Escenario 5d: Sin velocidad ni comprensión.
    Dado PPM=0 o CL=0,
    cuando se calcula Vef,
    entonces devuelve 0.0.
    """
    assert calculate_effective_speed(ppm=0.0, comprehension=50.0) == 0.0
    assert calculate_effective_speed(ppm=100.0, comprehension=0.0) == 0.0


# ============================================================================
# Casos límite y robustez
# ============================================================================


def test_calculate_ppm_edge_cases():
    """Casos límite adicionales para PPM."""
    assert calculate_ppm(word_count=0, time_seconds=60) == 0.0
    assert calculate_ppm(word_count=-100, time_seconds=60) == 0.0


def test_calculate_reading_comprehension_edge_cases():
    """Casos límite adicionales para CL."""
    # Negativos en aciertos (no debería ocurrir, pero manejamos)
    assert calculate_reading_comprehension(correct_answers=-1, mistakes=0) == 0.0
    # Negativos en fallos (no debería ocurrir)
    cl = calculate_reading_comprehension(correct_answers=10, mistakes=-5)
    # P = 10 − (−5/2) = 10 + 2.5 = 12.5 → CL = 62.5% (se suma la penalización negativa)
    assert cl == 62.5
    # Clamp a máximo 100%: 25 aciertos (imposible con 20 ítems)
    # P = 25 − 0 = 25 → (25/20)×100 = 125% → clamped a 100%
    cl = calculate_reading_comprehension(correct_answers=25, mistakes=0)
    assert cl == 100.0


def test_backward_compatibility_calculate_accuracy():
    """
    Compatibilidad: calculate_accuracy() ahora implementa CL, no el porcentaje simple.
    Dado 15 aciertos y 3 errores,
    cuando se llama a calculate_accuracy() (nombre antiguo),
    entonces devuelve 67.5% (CL con penalización, NO 83.3%).
    """
    # Firma antigua: calculate_accuracy(correct_answers, mistakes)
    # Devuelve CL de la Batería
    result = calculate_accuracy(correct_answers=15, mistakes=3, unanswered=2)
    assert result == 67.5  # CL, no simple percentage
