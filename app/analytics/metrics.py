"""
Funciones puras de cálculo de métricas derivadas (BE-30 / Contrato 3).

Implementación de la Batería de Lectura Eficaz (Bruño) con las tres métricas:
- VE (velocidad espontánea): palabras/minuto
- CL (comprensión lectora): porcentaje ponderado con penalización
- Vef (velocidad eficaz): palabras leídas Y comprendidas por minuto

Este módulo es independiente y no importa dependencias de base de datos ni de la aplicación.

Referencias:
- Documento: Batería de Pruebas de Evaluación de Fluidez y Comprensión Lectoras (Bruño)
- Fórmula CL: P = aciertos − (fallos / 2), luego CL = (P / 20) × 100, donde 20 = nº de ítems fijos
- Penalización: respuestas incorrectas se castigan; respuestas en blanco no penalizan pero no puntúan
"""


def calculate_ppm(word_count: int, time_seconds: float) -> float:
    """
    Calcula las Palabras Por Minuto (VE - Velocidad Espontánea).

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


def calculate_reading_comprehension(
    correct_answers: int, mistakes: int, unanswered: int = 0
) -> float:
    """
    Calcula el porcentaje de comprensión lectora (CL) con penalización.

    Implementa la Batería de Lectura Eficaz (Bruño):
    - Penaliza respuestas incorrectas (falsos positivos)
    - No penaliza respuestas en blanco (conservador)
    - Utiliza 20 ítems fijos

    Fórmula:
        P = aciertos − (fallos / 2)
        CL = (P / 20) × 100

    :param correct_answers: Número de aciertos.
    :param mistakes: Número de errores (respuestas incorrectas).
    :param unanswered: Número de preguntas sin responder (no penaliza).
    :return: Porcentaje de comprensión entre 0.0 y 100.0 redondeado a 2 decimales.

    Escenarios:
    - 20 aciertos, 0 fallos, 0 en blanco: P=20 → CL=100%
    - 15 aciertos, 3 fallos, 2 en blanco: P=15−1.5=13.5 → CL=67.5%
    - 10 aciertos, 10 fallos, 0 en blanco: P=10−5=5 → CL=25%
    - 0 aciertos: CL=0%
    """
    TOTAL_ITEMS = 20  # Número fijo de ítems en la batería

    # Penalización: falso es el que pone un mal positivo (responde mal)
    # P = aciertos - (fallos / 2)
    penalty = mistakes / 2.0
    adjusted_score = correct_answers - penalty

    # Clamp a mínimo 0 (no hay puntuaciones negativas)
    adjusted_score = max(0.0, adjusted_score)

    # CL = (puntuación ajustada / total de ítems) × 100
    comprehension = (adjusted_score / TOTAL_ITEMS) * 100.0

    # Clamp a máximo 100
    comprehension = min(100.0, comprehension)

    return round(comprehension, 2)


def calculate_effective_speed(ppm: float, comprehension: float) -> float:
    """
    Calcula la velocidad eficaz (Vef) — palabras leídas Y comprendidas por minuto.

    Combina velocidad y comprensión en una sola métrica.
    Un lector rápido pero que no entiende tiene baja Vef.

    Fórmula:
        Vef = VE × CL / 100

    :param ppm: Velocidad espontánea en palabras por minuto (VE).
    :param comprehension: Porcentaje de comprensión lectora (0-100).
    :return: Velocidad eficaz en palabras leídas y comprendidas por minuto.

    Ejemplo:
    - PPM=174.4, CL=67.5% → Vef = 174.4 × 0.675 = 117.7 palabras/minuto leídas y comprendidas
    """
    if ppm <= 0 or comprehension <= 0:
        return 0.0

    vef = (ppm * comprehension) / 100.0
    return round(vef, 2)


def calculate_accuracy(correct_answers: int, mistakes: int, unanswered: int = 0) -> float:
    """
    Calcula el porcentaje de comprensión lectora (CL) con penalización.

    ⚠️ DEPRECATED: Use calculate_reading_comprehension() en su lugar.
    Este nombre se mantiene para compatibilidad, pero implementa la fórmula de la Batería.

    :param correct_answers: Número de aciertos.
    :param mistakes: Número de errores (respuestas incorrectas).
    :param unanswered: Número de preguntas sin responder (ignorado en la firma antigua).
    :return: Porcentaje de comprensión entre 0.0 y 100.0.
    """
    return calculate_reading_comprehension(correct_answers, mistakes, unanswered)
