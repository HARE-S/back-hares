"""Parser para hojas de cálculo de Lectura Eficaz (Tabla GENERAL datos pruebas).

Interpreta hojas de cálculo con pestañas por curso (p. ej. PRUEBAS 2º ESO)
donde la fila 3 contiene los códigos de prueba (2IF, 2IL, etc.) y la fila 4
las columnas de alumno, especialidad y métricas (tiempo, aciertos, errores, VEF).

Extrae:
- Estudiantes con su identificador único estable, nombre y especialidad/sección.
- Evaluaciones reales con tiempo, aciertos, errores y VEF para cada prueba completada.
- CSV normalizado para el StudentImporter.
"""
import datetime
import re
import unicodedata
from typing import Any, Dict, List, Tuple


def slugify(text: str) -> str:
    """Genera un identificador alfanumérico limpio a partir de un texto."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    slug = re.sub(r"[^A-Z0-9]+", "-", normalized.upper()).strip("-")
    return slug or "ALU-GEN"


def get_test_date(test_code: str, default_year: int = 2025) -> datetime.date:
    """Asigna fecha aproximada según la fase de la prueba (I: Inicial, A: Media A, B: Media B, C: Final)."""
    phase = test_code[1] if len(test_code) >= 2 else "I"
    if phase == "I":
        return datetime.date(default_year, 10, 15)
    elif phase == "A":
        return datetime.date(default_year, 12, 15)
    elif phase == "B":
        return datetime.date(default_year + 1, 2, 15)
    elif phase == "C":
        return datetime.date(default_year + 1, 5, 15)
    return datetime.date(default_year, 11, 1)


def is_lectura_eficaz_excel(wb: Any) -> bool:
    """Determina si el libro Excel corresponde a la matriz de Lectura Eficaz."""
    for sheetname in wb.sheetnames:
        if "PRUEBAS" in sheetname.upper():
            ws = wb[sheetname]
            for r in range(1, min(6, ws.max_row + 1)):
                row_vals = [str(ws.cell(r, c).value or "") for c in range(1, min(20, ws.max_column + 1))]
                if any("ALUMNO" in v.upper() for v in row_vals) or any(re.match(r"^[0-9][A-Z]{2}", v.strip()) for v in row_vals):
                    return True
    return False


def parse_lectura_eficaz_workbook(
    wb: Any, center_name: str = "Fundación Peñascal"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Parsea el libro de Lectura Eficaz.

    Retorna:
    (students_list, evaluations_list, csv_content_for_student_importer)
    """
    students_map: Dict[str, Dict[str, Any]] = {}
    evaluations: List[Dict[str, Any]] = []

    for sheetname in wb.sheetnames:
        if "PRUEBAS" not in sheetname.upper():
            continue
        ws = wb[sheetname]
        course_name = sheetname.upper().replace("PRUEBAS", "").strip() or "General"

        # 1. Identificar bloques de pruebas en la fila 3
        test_blocks = []
        for col in range(3, ws.max_column + 1):
            val = ws.cell(3, col).value
            if val and str(val).strip():
                m = re.match(r"^([0-9][A-Z]{2})\s*(.*)", str(val).strip())
                if m:
                    test_blocks.append({
                        "code": m.group(1),
                        "name": m.group(2).strip(),
                        "col": col,
                    })

        # 2. Iterar filas de alumnos (desde fila 5)
        for r in range(5, ws.max_row + 1):
            name_val = ws.cell(r, 1).value
            if not name_val or not str(name_val).strip():
                continue
            raw_name = str(name_val).strip()
            clean_name = re.sub(r"\s+", " ", raw_name).strip()

            # Especialidad o sección
            spec_val = ws.cell(r, 2).value
            section_name = str(spec_val).strip() if spec_val and str(spec_val).strip() else course_name

            student_id = "ALU-" + slugify(clean_name)[:22]

            if student_id not in students_map:
                students_map[student_id] = {
                    "student_id": student_id,
                    "student_name": clean_name,
                    "sections": [section_name],
                    "center": center_name,
                    "course": course_name,
                }
            else:
                if section_name not in students_map[student_id]["sections"]:
                    students_map[student_id]["sections"].append(section_name)

            # Extraer evaluaciones para cada prueba
            for tb in test_blocks:
                c = tb["col"]
                tiempo = ws.cell(r, c + 1).value
                aciertos = ws.cell(r, c + 2).value
                errores = ws.cell(r, c + 3).value
                vef = ws.cell(r, c + 7).value

                try:
                    t_val = int(float(tiempo)) if tiempo is not None else 0
                    a_val = int(float(aciertos)) if aciertos is not None else 0
                    e_val = int(float(errores)) if errores is not None else 0
                    v_val = float(vef) if vef is not None else 0.0

                    if t_val > 0 and (a_val > 0 or v_val > 0):
                        evaluations.append({
                            "student_id": student_id,
                            "section_name": section_name,
                            "test_code": tb["code"],
                            "time": t_val,
                            "successes": a_val,
                            "mistakes": e_val,
                            "vef": v_val,
                            "test_date": get_test_date(tb["code"]).isoformat(),
                        })
                except Exception:
                    pass

    students_list = list(students_map.values())

    # Generar contenido CSV compatible con StudentImporter
    csv_lines = ["student_id;student_name;sections;center"]
    for s in students_list:
        secs = ",".join(s["sections"])
        sid = s["student_id"]
        sname = s["student_name"]
        scenter = s["center"]
        csv_lines.append(f"{sid};{sname};{secs};{scenter}")
    csv_content = "\n".join(csv_lines)

    return students_list, evaluations, csv_content
