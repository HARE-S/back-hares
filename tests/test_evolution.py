from datetime import date
import pytest
from app.analytics.evolution import calculate_individual_evolution


@pytest.fixture
def sample_results():
    """Fixture con 5 resultados desordenados de un alumno."""
    return [
        {
            "test_date": "2026-05-15",
            "word_count": 800,
            "time_seconds": 300,  # 160 PPM
            "successes": 9,
            "mistakes": 1,        # 90% aciertos
            "test_name": "Prueba Mayo",
        },
        {
            "test_date": "2026-03-01",
            "word_count": 600,
            "time_seconds": 360,  # 100 PPM
            "successes": 7,
            "mistakes": 3,        # 70% aciertos
            "test_name": "Prueba Marzo",
        },
        {
            "test_date": "2026-04-10",
            "word_count": 750,
            "time_seconds": 300,  # 150 PPM
            "successes": 8,
            "mistakes": 2,        # 80% aciertos
            "test_name": "Prueba Abril",
        },
        {
            "test_date": "2026-06-20",
            "word_count": 900,
            "time_seconds": 270,  # 200 PPM
            "successes": 10,
            "mistakes": 0,        # 100% aciertos
            "test_name": "Prueba Junio",
        },
        {
            "test_date": "2026-03-20",
            "word_count": 660,
            "time_seconds": 330,  # 120 PPM
            "successes": 7,
            "mistakes": 3,        # 70% aciertos
            "test_name": "Prueba Marzo Final",
        },
    ]


def test_time_series_ordered_by_date_scenario_1(sample_results):
    """
    Escenario 1: Serie temporal ordenada cronológicamente por fecha.
    """
    res = calculate_individual_evolution(sample_results)

    assert res["has_insufficient_data"] is False
    assert res["total_tests"] == 5

    dates = [item["test_date"] for item in res["time_series"]]
    assert dates == [
        "2026-03-01",
        "2026-03-20",
        "2026-04-10",
        "2026-05-15",
        "2026-06-20",
    ]

    # Verificar que el primer test es de marzo (100 PPM) y el último de junio (200 PPM)
    assert res["time_series"][0]["ppm"] == 100.0
    assert res["time_series"][-1]["ppm"] == 200.0


def test_date_range_filtering_scenario_2(sample_results):
    """
    Escenario 2: Acotación por rango de fechas (marzo a abril).
    """
    res = calculate_individual_evolution(
        sample_results,
        start_date="2026-03-01",
        end_date="2026-04-30",
    )

    assert res["has_insufficient_data"] is False
    assert res["total_tests"] == 3

    dates = [item["test_date"] for item in res["time_series"]]
    assert dates == ["2026-03-01", "2026-03-20", "2026-04-10"]


def test_variations_calculation_scenario_3(sample_results):
    """
    Escenario 3: Variación entre primera (100 PPM, 70%) y última prueba (200 PPM, 100%).
    Variación PPM: +100.0 abs, +100.0%
    Variación Aciertos: +30.0 abs, +42.86%
    """
    res = calculate_individual_evolution(sample_results)

    variations = res["variations"]

    # PPM
    assert variations["ppm"]["absolute"] == 100.0  # 200 - 100
    assert variations["ppm"]["percentage"] == 100.0  # ((200 - 100) / 100) * 100

    # Aciertos
    assert variations["accuracy"]["absolute"] == 30.0  # 100 - 70
    assert pytest.approx(variations["accuracy"]["percentage"], 0.01) == 42.86  # ((100 - 70) / 70) * 100


def test_insufficient_data_one_test_scenario_4():
    """
    Escenario 4: Dado un alumno con 1 sola prueba, devuelve has_insufficient_data = True
    y 200 OK estructurado sin marcar tendencia falsa.
    """
    single_result = [
        {
            "test_date": "2026-03-01",
            "word_count": 600,
            "time_seconds": 360,
            "successes": 8,
            "mistakes": 2,
        }
    ]

    res = calculate_individual_evolution(single_result)

    assert res["has_insufficient_data"] is True
    assert res["total_tests"] == 1
    assert len(res["time_series"]) == 1
    assert res["variations"]["ppm"]["absolute"] == 0.0


def test_no_results_scenario_5():
    """
    Escenario 5: Dado un alumno sin pruebas, devuelve serie vacía con has_insufficient_data = True.
    """
    res = calculate_individual_evolution([])

    assert res["has_insufficient_data"] is True
    assert res["total_tests"] == 0
    assert res["time_series"] == []
