"""
Módulo de análisis de evolución individual de un alumno (BE-31).

Este módulo es independiente y no importa dependencias de base de datos ni de Flask.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from app.analytics.metrics import calculate_accuracy, calculate_ppm


def _parse_date(val: Any) -> Optional[date]:
    """Convierte una fecha en formato string ISO, date o datetime a un objeto date."""
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.split("T")[0]).date()
        except ValueError:
            return None
    return None


def calculate_individual_evolution(
    results: List[Dict[str, Any]],
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calcula la evolución temporal de un alumno a partir de su lista de resultados.

    :param results: Lista de diccionarios con datos de resultados.
                    Estructura esperada:
                    {
                        "test_date": date|str,
                        "word_count": int,
                        "time_seconds": float,
                        "correct_answers": int,
                        "total_questions": int,
                        "test_id": str (opcional),
                        "test_name": str (opcional)
                    }
    :param start_date: Fecha inicial de acotación (opcional).
    :param end_date: Fecha final de acotación (opcional).
    :return: Diccionario estructurado con series temporales, variaciones e indicador de datos.
    """
    filter_start = _parse_date(start_date)
    filter_end = _parse_date(end_date)

    processed_results = []
    for item in results:
        t_date = _parse_date(item.get("test_date") or item.get("date"))
        if t_date is None:
            continue

        # Acotación por rango de fechas (Escenario 2)
        if filter_start and t_date < filter_start:
            continue
        if filter_end and t_date > filter_end:
            continue

        word_count = item.get("word_count", 0)
        time_seconds = item.get("time_seconds") or item.get("time", 0)

        # Si el diccionario trae aciertos y errores en lugar de total
        correct_answers = item.get("correct_answers") if item.get("correct_answers") is not None else item.get("successes", 0)
        if "total_questions" in item:
            total_questions = item["total_questions"]
        elif "mistakes" in item:
            total_questions = correct_answers + item.get("mistakes", 0)
        else:
            total_questions = 0

        ppm = item.get("ppm")
        if ppm is None:
            ppm = calculate_ppm(word_count, time_seconds)

        accuracy = item.get("accuracy")
        if accuracy is None:
            if total_questions > 0:
                accuracy = round((correct_answers / total_questions) * 100.0, 2)
            else:
                accuracy = 0.0

        processed_results.append({
            "test_date": t_date.isoformat(),
            "_raw_date": t_date,
            "test_id": item.get("test_id", ""),
            "test_name": item.get("test_name", ""),
            "word_count": word_count,
            "time_seconds": time_seconds,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "ppm": float(ppm),
            "accuracy": float(accuracy),
        })

    # Ordenar cronológicamente por fecha
    processed_results.sort(key=lambda x: x["_raw_date"])

    # Limpiar campo temporal interno
    time_series = []
    for res in processed_results:
        clean_res = {k: v for k, v in res.items() if k != "_raw_date"}
        time_series.append(clean_res)

    total_count = len(time_series)

    # Escenarios 4 y 5: Datos insuficientes (menos de 2 pruebas)
    if total_count < 2:
        return {
            "has_insufficient_data": True,
            "message": "Se requieren al menos 2 pruebas en el periodo para calcular la tendencia de evolución.",
            "total_tests": total_count,
            "time_series": time_series,
            "variations": {
                "ppm": {"absolute": 0.0, "percentage": 0.0},
                "accuracy": {"absolute": 0.0, "percentage": 0.0},
            },
        }

    # Escenario 3: Cálculo de variación entre extremos
    first = time_series[0]
    last = time_series[-1]

    ppm_abs = round(last["ppm"] - first["ppm"], 2)
    ppm_pct = (
        round(((last["ppm"] - first["ppm"]) / first["ppm"]) * 100.0, 2)
        if first["ppm"] > 0
        else 0.0
    )

    acc_abs = round(last["accuracy"] - first["accuracy"], 2)
    acc_pct = (
        round(((last["accuracy"] - first["accuracy"]) / first["accuracy"]) * 100.0, 2)
        if first["accuracy"] > 0
        else 0.0
    )

    return {
        "has_insufficient_data": False,
        "message": f"Evolución calculada sobre {total_count} pruebas registradas.",
        "total_tests": total_count,
        "time_series": time_series,
        "variations": {
            "ppm": {
                "absolute": ppm_abs,
                "percentage": ppm_pct,
            },
            "accuracy": {
                "absolute": acc_abs,
                "percentage": acc_pct,
            },
        },
    }
