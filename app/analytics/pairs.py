"""
Métricas de par y progresión entre pruebas (Batería de Lectura Eficaz).

En la batería, la unidad de evaluación no es la prueba suelta sino el PAR de
textos de una misma prueba: uno funcional y uno literario, aplicados en días
consecutivos. De ahí salen las tres cifras que el departamento de pedagogía
usa en sus informes:

    MEDIA     = media de la velocidad eficaz funcional y literaria
    DIF F-L   = Vef literario - Vef funcional
    PROGRESO  = MEDIA de una prueba - MEDIA de la anterior

Módulo puro: recibe números y devuelve números, sin dependencias de base de datos.
"""

from typing import Any, Dict, List, Optional

# Orden pedagógico de las pruebas. La Inicial es diagnóstica y se aplica al
# comienzo del curso; A, B y C al final de cada trimestre. D y E son ampliaciones
# que el centro usa en algunos niveles.
TEST_LETTER_ORDER: Dict[str, int] = {
    "I": 0,
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
}

# Tipos de texto de la batería.
TYPE_FUNCTIONAL = "F"
TYPE_LITERARY = "L"

# La hoja del cliente trata una prueba no realizada como un CERO, porque su
# fórmula de velocidad devuelve 0 cuando el tiempo está vacío, y AVERAGE cuenta
# ese cero. Consecuencia: si un alumno solo hace el texto literario, su media
# sale a la mitad de lo que le corresponde.
#
# Aquí no se replica ese comportamiento: una prueba no realizada es ausencia de
# dato, no un cero. Si hace falta reproducir exactamente las cifras históricas de
# ORI, pasar missing_as_zero=True.
MISSING_AS_ZERO_DEFAULT = False


def calculate_pair(
    vef_functional: Optional[float],
    vef_literary: Optional[float],
    missing_as_zero: bool = MISSING_AS_ZERO_DEFAULT,
) -> Dict[str, Any]:
    """
    Calcula la media y la diferencia de un par funcional / literario.

    :param vef_functional: Velocidad eficaz del texto funcional, o None si no se hizo.
    :param vef_literary: Velocidad eficaz del texto literario, o None si no se hizo.
    :param missing_as_zero: Si True, una prueba ausente cuenta como cero (modo ORI).
    :return: Diccionario con mean, difference, is_complete y available.

    Ejemplos:
        calculate_pair(100.0, 140.0)
        -> {"mean": 120.0, "difference": 40.0, "is_complete": True, "available": 2}

        calculate_pair(None, 140.0)
        -> {"mean": 140.0, "difference": None, "is_complete": False, "available": 1}

        calculate_pair(None, 140.0, missing_as_zero=True)
        -> {"mean": 70.0, "difference": 140.0, "is_complete": False, "available": 1}
    """
    if missing_as_zero:
        functional = vef_functional if vef_functional is not None else 0.0
        literary = vef_literary if vef_literary is not None else 0.0
        return {
            "mean": round((functional + literary) / 2.0, 2),
            "difference": round(literary - functional, 2),
            "is_complete": vef_functional is not None and vef_literary is not None,
            "available": sum(v is not None for v in (vef_functional, vef_literary)),
        }

    present = [v for v in (vef_functional, vef_literary) if v is not None]

    if not present:
        return {"mean": None, "difference": None, "is_complete": False, "available": 0}

    mean = round(sum(present) / len(present), 2)

    difference = None
    if vef_functional is not None and vef_literary is not None:
        difference = round(vef_literary - vef_functional, 2)

    return {
        "mean": mean,
        "difference": difference,
        "is_complete": len(present) == 2,
        "available": len(present),
    }


def build_pair_series(
    results: List[Dict[str, Any]],
    missing_as_zero: bool = MISSING_AS_ZERO_DEFAULT,
) -> List[Dict[str, Any]]:
    """
    Agrupa resultados sueltos en pares por letra de prueba.

    Cada elemento de `results` debe traer al menos: test_letter, type y vef.
    Si un alumno repitió una prueba, se toma el resultado más reciente: la
    progresión mide el estado alcanzado, no cada intento.

    :param results: Lista de resultados con test_letter, type, vef y test_date.
    :param missing_as_zero: Ver calculate_pair.
    :return: Lista ordenada por orden pedagógico, un elemento por letra de prueba.
    """
    by_letter: Dict[str, Dict[str, Any]] = {}

    for item in results:
        letter = str(item.get("test_letter") or "").strip().upper()
        if letter not in TEST_LETTER_ORDER:
            continue

        text_type = str(item.get("type") or "").strip().upper()
        if text_type not in (TYPE_FUNCTIONAL, TYPE_LITERARY):
            continue

        slot = by_letter.setdefault(
            letter,
            {"test_letter": letter, "functional": None, "literary": None,
             "functional_date": None, "literary_date": None},
        )

        key = "functional" if text_type == TYPE_FUNCTIONAL else "literary"
        date_key = f"{key}_date"
        current_date = slot[date_key]
        new_date = item.get("test_date")

        # Nos quedamos con el intento más reciente de cada mitad del par
        if current_date is None or (new_date is not None and str(new_date) >= str(current_date)):
            slot[key] = item.get("vef")
            slot[date_key] = new_date

    series = []
    for letter in sorted(by_letter, key=lambda x: TEST_LETTER_ORDER[x]):
        slot = by_letter[letter]
        pair = calculate_pair(slot["functional"], slot["literary"], missing_as_zero)
        series.append({
            "test_letter": letter,
            "order": TEST_LETTER_ORDER[letter],
            "vef_functional": slot["functional"],
            "vef_literary": slot["literary"],
            "mean": pair["mean"],
            "difference": pair["difference"],
            "is_complete": pair["is_complete"],
        })

    return series


def calculate_progress(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula la progresión entre pruebas consecutivas y la progresión global.

    Las transiciones se nombran como en los informes del cliente: I-A, A-B, B-C...
    Solo se calcula una transición cuando ambas pruebas tienen media; en caso
    contrario se devuelve None, nunca un cero, porque un cero se leería como
    estancamiento cuando en realidad es ausencia de dato.

    La progresión global es la diferencia entre la PRIMERA y la ÚLTIMA prueba con
    datos. Conviene saber que la hoja del cliente calcula ahí MEDIA B - MEDIA I,
    ignorando la prueba C: parece una fórmula que se quedó sin actualizar cuando se
    añadió esa prueba. Aquí se toman los extremos reales.

    :param series: Salida de build_pair_series.
    :return: Diccionario con transitions, global_progress y measured_span.
    """
    with_mean = [s for s in series if s.get("mean") is not None]

    transitions = []
    for previous, current in zip(series, series[1:]):
        label = f"{previous['test_letter']}-{current['test_letter']}"
        if previous.get("mean") is None or current.get("mean") is None:
            transitions.append({"transition": label, "value": None, "improved": None})
            continue

        delta = round(current["mean"] - previous["mean"], 2)
        transitions.append({
            "transition": label,
            "value": delta,
            "improved": delta > 0,
        })

    global_progress = None
    measured_span = None
    if len(with_mean) >= 2:
        first, last = with_mean[0], with_mean[-1]
        global_progress = round(last["mean"] - first["mean"], 2)
        measured_span = f"{first['test_letter']}-{last['test_letter']}"

    return {
        "transitions": transitions,
        "global_progress": global_progress,
        "measured_span": measured_span,
        "tests_with_data": len(with_mean),
    }


def summarize_group_progress(students_series: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Resume la progresión de un grupo, como el bloque PROGRESO POR PRUEBAS de ORI.

    Importante: en los informes del cliente "progreso" de un grupo NO es la media de
    las diferencias, sino CUÁNTOS alumnos mejoran y en qué porcentaje. Se replica ese
    criterio para que las cifras sean comparables con las suyas.

    :param students_series: Una lista de series (salida de build_pair_series) por alumno.
    :return: Conteo y porcentaje de alumnos que mejoran, por transición y en global.
    """
    per_transition: Dict[str, Dict[str, int]] = {}
    improved_global = 0
    measurable_global = 0

    for series in students_series:
        progress = calculate_progress(series)

        for transition in progress["transitions"]:
            label = transition["transition"]
            bucket = per_transition.setdefault(label, {"improved": 0, "measurable": 0})
            if transition["improved"] is None:
                continue
            bucket["measurable"] += 1
            if transition["improved"]:
                bucket["improved"] += 1

        if progress["global_progress"] is not None:
            measurable_global += 1
            if progress["global_progress"] > 0:
                improved_global += 1

    transitions = {}
    for label, bucket in per_transition.items():
        percentage = (
            round((bucket["improved"] / bucket["measurable"]) * 100.0, 2)
            if bucket["measurable"] > 0
            else None
        )
        transitions[label] = {
            "improved": bucket["improved"],
            "measurable": bucket["measurable"],
            "percentage": percentage,
        }

    global_percentage = (
        round((improved_global / measurable_global) * 100.0, 2)
        if measurable_global > 0
        else None
    )

    return {
        "transitions": transitions,
        "global": {
            "improved": improved_global,
            "measurable": measurable_global,
            "percentage": global_percentage,
        },
        "population": len(students_series),
    }
