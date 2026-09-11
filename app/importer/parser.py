"""Lector y validador del CSV de alumnado (BE-06 format).

El fichero de importación utiliza punto y coma como separador y codificación
UTF-8, con las columnas reales de Alexia:
    student_id;student_name;sections;center

El campo `sections` es multivalor: varias secciones separadas por comas
dentro de una única columna.
"""
import csv
import io
from typing import Any, Dict, List

from app.core.exceptions import ValidationError

EXPECTED_COLUMNS = {"student_id", "student_name", "sections", "center"}


def _strip_empty_tokens(tokens: List[str]) -> List[str]:
    """Removes empty trailing tokens produced by a final semicolon."""
    while tokens and tokens[-1] == "":
        tokens.pop()
    return tokens


def parse_sections_field(raw: str) -> List[str]:
    """Splits the multi-valued sections column into individual section names."""
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_students_csv(content: str) -> List[Dict[str, Any]]:
    """
    Parses the students CSV content applying BE-06 rules.

    - Semicolon separator and UTF-8 encoding.
    - Ignores empty trailing columns produced by a final semicolon.
    - Splits the multi-valued `sections` column.
    - Raises ValidationError when a row lacks any required column.
    """
    if not content:
        return []

    if content.startswith("\ufeff"):
        content = content[1:]

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return []

    header_line = lines[0]
    header_tokens = [tok.strip().lower() for tok in header_line.split(";")]
    header_tokens = _strip_empty_tokens(header_tokens)

    if not EXPECTED_COLUMNS.issubset(set(header_tokens)):
        raise ValidationError(
            "El archivo CSV debe contener las columnas: student_id, student_name, sections, center"
        )

    id_idx = header_tokens.index("student_id")
    name_idx = header_tokens.index("student_name")
    sections_idx = header_tokens.index("sections")
    center_idx = header_tokens.index("center")

    parsed_rows: List[Dict[str, Any]] = []

    for line_num, line in enumerate(lines[1:], start=2):
        try:
            reader = csv.reader(io.StringIO(line), delimiter=";")
            tokens = next(reader)
        except Exception:
            tokens = line.split(";")

        tokens = _strip_empty_tokens(tokens)

        if len(tokens) < len(header_tokens):
            raise ValidationError(
                f"Línea {line_num}: Faltan columnas requeridas "
                f"(esperadas {len(header_tokens)}, recibidas {len(tokens)})"
            )

        student_id = tokens[id_idx].strip()
        student_name = tokens[name_idx].strip()
        sections_raw = tokens[sections_idx]
        center = tokens[center_idx].strip()

        if not student_id:
            raise ValidationError(f"Línea {line_num}: El campo 'student_id' no puede estar vacío")
        if not student_name:
            raise ValidationError(f"Línea {line_num}: El campo 'student_name' no puede estar vacío")
        if not center:
            raise ValidationError(f"Línea {line_num}: El campo 'center' no puede estar vacío")

        sections = parse_sections_field(sections_raw)
        if not sections:
            raise ValidationError(
                f"Línea {line_num}: El campo 'sections' debe contener al menos una sección"
            )

        parsed_rows.append({
            "student_id": student_id,
            "student_name": student_name,
            "sections": sections,
            "center": center,
        })

    return parsed_rows