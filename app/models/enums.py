from enum import Enum
from sqlalchemy import case


class BookLevel(str, Enum):
    LEVEL_0 = "0"
    LEVEL_0_I = "0-I"
    LEVEL_I = "I"
    LEVEL_I_II = "I/II"
    LEVEL_II = "II"

    @classmethod
    def values(cls):
        return [item.value for item in cls]


# Ponderación del orden pedagógico: 0 < 0-I < I < I/II < II
BOOK_LEVEL_ORDER = {
    BookLevel.LEVEL_0.value: 0,
    BookLevel.LEVEL_0_I.value: 1,
    BookLevel.LEVEL_I.value: 2,
    BookLevel.LEVEL_I_II.value: 3,
    BookLevel.LEVEL_II.value: 4,
}


def validate_book_level(value: str) -> str:
    """
    Valida que el nivel del libro sea uno de los reconocidos por el centro.
    Lanza ValueError si el nivel no es válido, enumerando los permitidos.
    """
    if not isinstance(value, str):
        value = str(value)

    valid_values = BookLevel.values()
    if value not in valid_values:
        valid_list_str = ", ".join(f"'{v}'" for v in valid_values)
        raise ValueError(
            f"Nivel '{value}' no reconocido. Los niveles válidos son: {valid_list_str}"
        )
    return value


def book_level_order_case(column):
    """
    Genera una expresión CASE de SQLAlchemy para ordenar por el orden pedagógico en SQL:
    0 -> 0-I -> I -> I/II -> II.
    """
    return case(
        (column == BookLevel.LEVEL_0.value, 0),
        (column == BookLevel.LEVEL_0_I.value, 1),
        (column == BookLevel.LEVEL_I.value, 2),
        (column == BookLevel.LEVEL_I_II.value, 3),
        (column == BookLevel.LEVEL_II.value, 4),
        else_=99,
    )
