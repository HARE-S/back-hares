"""Clasificación de velocidad eficaz por bandas de nivel lector."""

import os
from typing import Optional

# Umbrales configurables por entorno (en palabras/minuto)
# Defaults: < 25 (bajo), 25-85 (normal), > 85 (alto)
# Para Peñascal específicamente (población con bajo rendimiento lector)
THRESHOLD_LOW = float(os.getenv("READING_LEVEL_THRESHOLD_LOW", "25.0"))
THRESHOLD_HIGH = float(os.getenv("READING_LEVEL_THRESHOLD_HIGH", "85.0"))

# Nombre de las bandas
LEVEL_LOW = "bajo"
LEVEL_NORMAL = "normal"
LEVEL_HIGH = "alto"


def classify_reading_level(vef: Optional[float]) -> Optional[str]:
    """
    Clasifica velocidad eficaz en banda de nivel lector.

    Bandas:
    - bajo: vef < THRESHOLD_LOW (default < 25 ppm)
    - normal: THRESHOLD_LOW <= vef <= THRESHOLD_HIGH (default 25-85)
    - alto: vef > THRESHOLD_HIGH (default > 85)

    :param vef: Velocidad eficaz en palabras/minuto, o None
    :return: Nombre de banda ("bajo", "normal", "alto") o None si vef es None
    """
    if vef is None:
        return None

    if vef < THRESHOLD_LOW:
        return LEVEL_LOW
    elif vef <= THRESHOLD_HIGH:
        return LEVEL_NORMAL
    else:
        return LEVEL_HIGH
