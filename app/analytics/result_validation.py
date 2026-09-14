"""Validación y detección de anómalos en resultados de lectura."""

import os
from typing import Dict, Optional, Tuple

# Rangos configurables por entorno (en segundos)
# Default: 30-600 seg (0.5-10 minutos) — rango plausible para una prueba de lectura
TIME_MIN_SECONDS = int(os.getenv("RESULT_TIME_MIN_SECONDS", "30"))
TIME_MAX_SECONDS = int(os.getenv("RESULT_TIME_MAX_SECONDS", "600"))

# Rango plausible de Vef para marcar aviso (no rechazo)
# Default: > 0 y < 200 ppm (Vef = ppm × comprehension)
VEF_PLAUSIBLE_MAX = float(os.getenv("RESULT_VEF_PLAUSIBLE_MAX", "200.0"))


def validate_result(
    time_seconds: int, successes: int, mistakes: int
) -> Tuple[bool, Optional[str]]:
    """
    Valida rangos de un resultado (RECHAZO si falla).

    Reglas:
    1. Tiempo: TIME_MIN_SECONDS <= time <= TIME_MAX_SECONDS
    2. Aciertos: 0 <= successes <= 20
    3. Errores: 0 <= mistakes <= 20
    4. Suma: successes + mistakes <= 20

    :param time_seconds: Tiempo en segundos
    :param successes: Número de aciertos
    :param mistakes: Número de errores
    :return: (is_valid, error_message or None)
    """
    if time_seconds < TIME_MIN_SECONDS or time_seconds > TIME_MAX_SECONDS:
        return False, f"Tiempo fuera de rango: {TIME_MIN_SECONDS}-{TIME_MAX_SECONDS} segundos"

    if not (0 <= successes <= 20):
        return False, "Aciertos deben estar entre 0 y 20"

    if not (0 <= mistakes <= 20):
        return False, "Errores deben estar entre 0 y 20"

    if successes + mistakes > 20:
        return False, f"Suma de aciertos + errores no puede exceder 20 (recibido: {successes + mistakes})"

    return True, None


def is_result_anomalous(time_seconds: int, successes: int, mistakes: int, vef: Optional[float]) -> Tuple[bool, Optional[str]]:
    """
    Detecta resultados anómalos y devuelve AVISO (no rechazo).

    Marcas de anómalo:
    1. Vef implausiblemente alto (> VEF_PLAUSIBLE_MAX)
    2. Vef negativo o muy bajo (artefacto de datos malos)

    :param time_seconds: Tiempo en segundos
    :param successes: Número de aciertos
    :param mistakes: Número de errores
    :param vef: Velocidad eficaz calculada, o None
    :return: (is_anomalous, warning_message or None)
    """
    if vef is None or vef < 0:
        return True, "Vef negativo o indeterminado: posible error de entrada"

    if vef > VEF_PLAUSIBLE_MAX:
        return True, f"Vef implausiblemente alto ({vef:.2f} > {VEF_PLAUSIBLE_MAX}): verificar entrada"

    return False, None
