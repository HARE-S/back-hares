"""Lector y validador del CSV de alumnado (BE-06 format).

El fichero de importación utiliza punto y coma como separador y codificación
UTF-8, con las columnas reales de Alexia:
    student_id;student_name;sections;center

El campo `sections` es multivalor: varias secciones separadas por comas
dentro de una única columna.

Dos modos de parseo:
- Estricto (`parse_students_csv`): aborta ante la primera fila inválida
  (BE-05 / BE-06, escenario 5 de separador incorrecto).
- Tolerante (`parse_students_csv_collect`): rechaza la fila inválida y
  continúa con el resto, acumulando errores con línea, columna y motivo
  (BE-07 escenario 5; el informe de errores BE-08 consume esta estructura).
"""
import csv
import io
from typing import Any, Dict, List, Tuple

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


def _read_row_tokens(line: str) -> List[str]:
    """Reads a single CSV line with ', respecting quotes when possible."""
    try:
        reader = csv.reader(io.StringIO(line), delimiter=";")
        tokens = next(reader)
    except Exception:
        tokens = line.split(";")
    return tokens


def _parse_students_csv(
    content: str,
    strict: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses the students CSV content applying BE-06 rules.

    Returns (rows, errors). In strict mode any validation issue raises
    ValidationError and errors is always empty.
    """
    if not content:
        return [], []

    if content.startswith("\ufeff"):
        content = content[1:]

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return [], []

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
    errors: List[Dict[str, Any]] = []

    for line_num, line in enumerate(lines[1:], start=2):
        # Fila de alumnado: las 4 columnas son exactas; no se elimina el token
        # vacío final (el ';' final tolerado es exclusivo de tests.csv, BE-12),
        # para que un centro vacío se detecte como tal y no como columna perdida.
        tokens = _read_row_tokens(line)

        error = None

        if len(tokens) != len(header_tokens):
            error = {
                "line": line_num,
                "column": None,
                "reason": (
                    f"Número de columnas distinto al esperado "
                    f"(esperadas {len(header_tokens)}, recibidas {len(tokens)})"
                ),
            }

        if error is None:
            student_id = tokens[id_idx].strip()
            student_name = tokens[name_idx].strip()
            sections_raw = tokens[sections_idx]
            center = tokens[center_idx].strip()

            if not student_id:
                error = {
                    "line": line_num,
                    "column": "student_id",
                    "reason": "El campo 'student_id' no puede estar vacío",
                }
            elif not student_name:
                error = {
                    "line": line_num,
                    "column": "student_name",
                    "reason": "El campo 'student_name' no puede estar vacío",
                }
            elif not center:
                error = {
                    "line": line_num,
                    "column": "center",
                    "reason": "El campo 'center' no puede estar vacío",
                }

            sections = None
            if error is None:
                sections = parse_sections_field(sections_raw)
                if not sections:
                    error = {
                        "line": line_num,
                        "column": "sections",
                        "reason": "El campo 'sections' debe contener al menos una sección",
                    }

        if error is not None:
            if strict:
                column = f" (columna '{error['column']}')" if error["column"] else ""
                raise ValidationError(
                    f"Línea {line_num}{column}: {error['reason']}"
                )
            errors.append(error)
            continue

        parsed_rows.append({
            "student_id": student_id,
            "student_name": student_name,
            "sections": sections,
            "center": center,
            "line": line_num,
        })

    return parsed_rows, errors


def parse_students_csv(content: str) -> List[Dict[str, Any]]:
    """
    Strict parsing (BE-06): raises ValidationError on the first invalid row.

    Used by BE-05 seeding and BE-06 import, where a wrong separator or a
    malformed row must abort without leaving partial records.
    """
    rows, _ = _parse_students_csv(content, strict=True)
    return rows


def parse_students_csv_collect(
    content: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Tolerant parsing (BE-07): rejects invalid rows and keeps processing.

    Returns (rows, errors) where each error is a dict with keys
    `line`, `column` (or None) and `reason`.
    """
    return _parse_students_csv(content, strict=False)