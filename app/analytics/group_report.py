"""
Módulo analítico puro para informes agregados de grupo y centro (BE-37).

Calcula:
- Medias de grupo: PPM (velocidad), porcentaje de aciertos / comprensión (CL), Vef.
- Participantes únicos y total de pruebas realizadas.
- Distribución de resultados por tramos pedagógicos (comprensión y velocidad).
- Estadísticos resumen (mínimo, máximo, mediana, cuartiles y desviación típica).
- Manejo de ausencia de datos sin divisiones sobre cero.
"""

import math
import statistics
from typing import Any, Dict, List, Optional


def _calculate_stats(values: List[float]) -> Dict[str, Optional[float]]:
    """Calcula estadísticos descriptivos para una lista de valores numéricos."""
    if not values:
        return {
            "min": None,
            "max": None,
            "median": None,
            "q1": None,
            "q3": None,
            "std_dev": None,
        }

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    min_val = round(float(sorted_vals[0]), 2)
    max_val = round(float(sorted_vals[-1]), 2)
    median_val = round(float(statistics.median(sorted_vals)), 2)
    std_val = round(float(statistics.stdev(sorted_vals)), 2) if n >= 2 else 0.0

    def percentile(p: float) -> float:
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[int(f)] * (c - k) + sorted_vals[int(c)] * (k - f)

    q1_val = round(float(percentile(0.25)), 2)
    q3_val = round(float(percentile(0.75)), 2)

    return {
        "min": min_val,
        "max": max_val,
        "median": median_val,
        "q1": q1_val,
        "q3": q3_val,
        "std_dev": std_val,
    }


def calculate_group_aggregates(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula agregados y distribución para un conjunto de resultados de lectura.

    :param results: Lista de diccionarios que representan resultados de pruebas,
                    cada uno con 'student_id', 'ppm', 'accuracy' (o 'comprehension') y opcionalmente 'vef'.
    :return: Diccionario con medias, conteos, indicador de datos y distribución.
    """
    if not results:
        return {
            "has_data": False,
            "participants_count": 0,
            "results_count": 0,
            "mean_ppm": None,
            "mean_accuracy": None,
            "mean_vef": None,
            "distribution": None,
        }

    results_count = len(results)
    participant_ids = {
        str(r.get("student_id")).strip()
        for r in results
        if r.get("student_id") is not None and str(r.get("student_id")).strip() != ""
    }
    participants_count = len(participant_ids)

    ppm_list = [float(r.get("ppm", 0.0) or 0.0) for r in results]
    accuracy_list = [
        float(r.get("accuracy", r.get("comprehension", 0.0)) or 0.0) for r in results
    ]
    vef_list = [float(r.get("vef", 0.0) or 0.0) for r in results]

    mean_ppm = round(sum(ppm_list) / results_count, 2)
    mean_accuracy = round(sum(accuracy_list) / results_count, 2)
    mean_vef = round(sum(vef_list) / results_count, 2)

    # Tramos pedagógicos de Comprensión / Precisión (%)
    # < 50% (Insuficiente), 50-69.9% (Suficiente/Medio), 70-84.9% (Notable), >= 85% (Sobresaliente)
    acc_brackets = {
        "<50": 0,
        "50-69": 0,
        "70-84": 0,
        ">=85": 0,
    }
    for acc in accuracy_list:
        if acc < 50.0:
            acc_brackets["<50"] += 1
        elif acc < 70.0:
            acc_brackets["50-69"] += 1
        elif acc < 85.0:
            acc_brackets["70-84"] += 1
        else:
            acc_brackets[">=85"] += 1

    accuracy_distribution = [
        {
            "bracket": "<50",
            "label": "< 50% (Insuficiente)",
            "count": acc_brackets["<50"],
            "percentage": round((acc_brackets["<50"] / results_count) * 100.0, 2),
        },
        {
            "bracket": "50-69",
            "label": "50% - 69% (Medio / Suficiente)",
            "count": acc_brackets["50-69"],
            "percentage": round((acc_brackets["50-69"] / results_count) * 100.0, 2),
        },
        {
            "bracket": "70-84",
            "label": "70% - 84% (Notable)",
            "count": acc_brackets["70-84"],
            "percentage": round((acc_brackets["70-84"] / results_count) * 100.0, 2),
        },
        {
            "bracket": ">=85",
            "label": ">= 85% (Sobresaliente)",
            "count": acc_brackets[">=85"],
            "percentage": round((acc_brackets[">=85"] / results_count) * 100.0, 2),
        },
    ]

    # Tramos de Velocidad (PPM)
    # < 100 PPM, 100 - 149 PPM, 150 - 199 PPM, >= 200 PPM
    ppm_brackets = {
        "<100": 0,
        "100-149": 0,
        "150-199": 0,
        ">=200": 0,
    }
    for ppm in ppm_list:
        if ppm < 100.0:
            ppm_brackets["<100"] += 1
        elif ppm < 150.0:
            ppm_brackets["100-149"] += 1
        elif ppm < 200.0:
            ppm_brackets["150-199"] += 1
        else:
            ppm_brackets[">=200"] += 1

    ppm_distribution = [
        {
            "bracket": "<100",
            "label": "< 100 PPM",
            "count": ppm_brackets["<100"],
            "percentage": round((ppm_brackets["<100"] / results_count) * 100.0, 2),
        },
        {
            "bracket": "100-149",
            "label": "100 - 149 PPM",
            "count": ppm_brackets["100-149"],
            "percentage": round((ppm_brackets["100-149"] / results_count) * 100.0, 2),
        },
        {
            "bracket": "150-199",
            "label": "150 - 199 PPM",
            "count": ppm_brackets["150-199"],
            "percentage": round((ppm_brackets["150-199"] / results_count) * 100.0, 2),
        },
        {
            "bracket": ">=200",
            "label": ">= 200 PPM",
            "count": ppm_brackets[">=200"],
            "percentage": round((ppm_brackets[">=200"] / results_count) * 100.0, 2),
        },
    ]

    distribution = {
        "accuracy_brackets": accuracy_distribution,
        "ppm_brackets": ppm_distribution,
        "stats": {
            "ppm": _calculate_stats(ppm_list),
            "accuracy": _calculate_stats(accuracy_list),
            "vef": _calculate_stats(vef_list),
        },
    }

    return {
        "has_data": True,
        "participants_count": participants_count,
        "results_count": results_count,
        "mean_ppm": mean_ppm,
        "mean_accuracy": mean_accuracy,
        "mean_vef": mean_vef,
        "distribution": distribution,
    }
