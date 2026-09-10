import pytest
from app.analytics.projection import calculate_evolution_projection


@pytest.fixture
def sample_results_with_trend():
    """Fixture con 5 resultados mostrando tendencia clara (PPM y comprensión crecientes)."""
    return [
        {
            "test_date": "2026-03-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 7,
            "mistakes": 3,
            "test_name": "Prueba Marzo",
        },
        {
            "test_date": "2026-03-20",
            "word_count": 660,
            "time_seconds": 330,
            "successes": 7,
            "mistakes": 3,
            "test_name": "Prueba Marzo Final",
        },
        {
            "test_date": "2026-04-10",
            "word_count": 750,
            "time_seconds": 300,
            "successes": 8,
            "mistakes": 2,
            "test_name": "Prueba Abril",
        },
        {
            "test_date": "2026-05-15",
            "word_count": 800,
            "time_seconds": 300,
            "successes": 9,
            "mistakes": 1,
            "test_name": "Prueba Mayo",
        },
        {
            "test_date": "2026-06-20",
            "word_count": 900,
            "time_seconds": 270,
            "successes": 10,
            "mistakes": 0,
            "test_name": "Prueba Junio",
        },
    ]


def test_projection_with_sufficient_data_scenario_1(sample_results_with_trend):
    """
    Escenario 1: Proyección con datos suficientes (≥3 pruebas).
    Dado un alumno con 5 resultados en evolución clara,
    cuando se solicita proyección, entonces devuelve tendencia calculada.
    """
    res = calculate_evolution_projection(sample_results_with_trend)

    assert res["has_projection"] is True
    assert res["based_on_tests"] == 5
    assert res["trend"] is not None
    assert "ppm" in res["trend"]
    assert "comprehension" in res["trend"]
    assert res["time_series"] is not None
    assert len(res["time_series"]) == 5


def test_projection_requires_minimum_three_tests_scenario_2():
    """
    Escenario 2: Datos insuficientes (< 3 pruebas).
    Dado un alumno con 2 resultados,
    cuando se solicita proyección, entonces no devuelve proyección
    y explica cuántas pruebas hacen falta.
    """
    results = [
        {
            "test_date": "2026-03-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 7,
            "mistakes": 3,
        },
        {
            "test_date": "2026-04-01",
            "word_count": 700,
            "time_seconds": 300,
            "successes": 8,
            "mistakes": 2,
        },
    ]

    res = calculate_evolution_projection(results)

    assert res["has_projection"] is False
    assert "al menos 3" in res["message"].lower()
    assert res["trend"] is None
    assert res["based_on_tests"] == 2


def test_projection_marks_estimation_explicitly_scenario_3(sample_results_with_trend):
    """
    Escenario 3: Marcado explícito de valores como estimación.
    Dado una proyección calculada, cuando se consulta el diccionario,
    entonces los valores proyectados tienen is_estimation=True
    para distinguirse de valores medidos.
    """
    res = calculate_evolution_projection(sample_results_with_trend)

    assert res["trend"]["ppm"]["is_estimation"] is True
    assert res["trend"]["comprehension"]["is_estimation"] is True

    # Los valores medidos en time_series no deben tener is_estimation
    for item in res["time_series"]:
        assert "is_estimation" not in item or item.get("is_estimation") is not True


def test_projection_flat_trend_scenario_4():
    """
    Escenario 4: Tendencia plana (todos los valores iguales).
    Dado un alumno con resultados sin variación,
    cuando se calcula proyección, entonces devuelve pendiente 0.0
    sin forzar una pendiente inexistente.
    """
    flat_results = [
        {
            "test_date": "2026-03-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 8,
            "mistakes": 2,
        },
        {
            "test_date": "2026-04-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 8,
            "mistakes": 2,
        },
        {
            "test_date": "2026-05-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 8,
            "mistakes": 2,
        },
    ]

    res = calculate_evolution_projection(flat_results)

    assert res["has_projection"] is True
    # Con valores constantes, la pendiente debe ser muy cercana a 0
    assert res["trend"]["ppm"]["slope"] == 0.0
    assert res["trend"]["comprehension"]["slope"] == 0.0


def test_projection_calculation_accuracy(sample_results_with_trend):
    """
    Escenario 5: Cálculo sin base de datos.
    Dado una función pura de proyección y una serie conocida,
    cuando se ejecuta con datos de ejemplo, entonces devuelve
    valores calculables manualmente (regresión lineal simple).
    """
    res = calculate_evolution_projection(sample_results_with_trend)

    # Con 5 puntos (0,1,2,3,4) y PPM creciente, la pendiente debe ser positiva
    assert res["trend"]["ppm"]["slope"] > 0

    # Comprensión también crece: CL inicial ~27.5%, final 50.0%
    assert res["trend"]["comprehension"]["slope"] > 0

    # Verificar que los valores están en rangos razonables
    assert 0 <= res["trend"]["ppm"]["slope"] <= 100  # PPM por índice
    assert -10 <= res["trend"]["comprehension"]["slope"] <= 10  # comprensión % por índice
