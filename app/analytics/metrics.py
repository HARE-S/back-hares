"""
Funciones puras de cálculo de métricas derivadas (BE-30 / Contrato 3).

Este módulo es independiente y no importa dependencias de base de datos ni de la aplicación.
"""


def calculate_ppm(word_count: int, time_seconds: float) -> float:
    """
    Calcula las Palabras Por Minuto (PPM).

    :param word_count: Número total de palabras de la prueba.
    :param time_seconds: Tiempo empleado expresado en segundos.
    :return: Palabras leídas por minuto (PPM) redondeado a 2 decimales.
    """
    if time_seconds <= 0 or word_count <= 0:
        return 0.0

    # Convertimos los segundos a minutos para calcular explícitamente por minuto
    time_minutes = time_seconds / 60.0
    ppm = word_count / time_minutes
    return round(ppm, 2)


def calculate_accuracy(correct_answers: int, total_questions: int) -> float:
    """
    Calcula el porcentaje de aciertos.

    :param correct_answers: Número de aciertos.
    :param total_questions: Número total de preguntas (aciertos + errores).
    :return: Porcentaje de aciertos entre 0.0 y 100.0 (0.0 si total_questions <= 0).
    """
    if total_questions <= 0 or correct_answers <= 0:
        return 0.0

    if correct_answers > total_questions:
        return 100.0

    accuracy = (correct_answers / total_questions) * 100.0
    return round(accuracy, 2)
