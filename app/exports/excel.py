import datetime
import io
from typing import Any, Dict, List
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def generate_results_excel(results: List[Dict[str, Any]]) -> io.BytesIO:
    """
    Genera un archivo Excel (.xlsx) con los resultados de pruebas de lectura (BE-35).
    - Cabeceras legibles en castellano (T-BE35-01).
    - Tipos de datos nativos reales (fechas como Date, números como float/int) (T-BE35-03).
    - Métricas incluidas: PPM, porcentaje de comprensión/aciertos, Vef (Escenario 3).
    - Genera solo cabeceras si el conjunto está vacío (Escenario 5).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resultados"

    # Asegurar que se vean las líneas de división de cuadrícula
    ws.views.sheetView[0].showGridLines = True

    # 1. Definición de cabeceras en castellano
    headers = [
        "Fecha",
        "Alumno",
        "ID Alumno",
        "Sección",
        "Prueba",
        "Código Prueba",
        "Palabras",
        "Tiempo (s)",
        "Aciertos",
        "Fallos",
        "PPM",
        "Comprensión (%)",
        "Velocidad Eficaz (Vef)",
    ]

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.append(headers)

    # Estilar fila de cabeceras
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    ws.row_dimensions[1].height = 28

    # Fuentes y alineaciones de datos
    data_font = Font(name="Arial", size=10)
    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # 2. Inserción de filas de datos
    for row_idx, r in enumerate(results, start=2):
        # Conversión segura de fecha a datetime.date nativo
        raw_date = r.get("test_date")
        parsed_date: Any = None
        if isinstance(raw_date, (datetime.date, datetime.datetime)):
            parsed_date = raw_date if isinstance(raw_date, datetime.date) else raw_date.date()
        elif isinstance(raw_date, str) and raw_date.strip():
            try:
                parsed_date = datetime.date.fromisoformat(raw_date.strip())
            except ValueError:
                parsed_date = raw_date.strip()

        # Conversión de métricas y campos numéricos nativos
        student_name = str(r.get("student_name") or "")
        student_id = str(r.get("student_external_id") or r.get("student_id") or "")
        section_name = str(r.get("section_name") or "")
        test_name = str(r.get("test_name") or "")
        test_code = str(r.get("test_code") or "")

        words = int(r.get("words", r.get("test_words", 0)) or 0)
        time_sec = int(r.get("time", 0) or 0)
        successes = int(r.get("successes", 0) or 0)
        mistakes = int(r.get("mistakes", 0) or 0)

        ppm = round(float(r.get("ppm", 0.0) or 0.0), 2)
        comprehension = round(float(r.get("comprehension", r.get("accuracy", 0.0)) or 0.0), 2)
        vef = round(float(r.get("vef", 0.0) or 0.0), 2)

        row_values = [
            parsed_date,
            student_name,
            student_id,
            section_name,
            test_name,
            test_code,
            words,
            time_sec,
            successes,
            mistakes,
            ppm,
            comprehension,
            vef,
        ]
        ws.append(row_values)
        ws.row_dimensions[row_idx].height = 20

        # Formatear celdas de la fila según su tipo (T-BE35-03)
        for col_idx, val in enumerate(row_values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font

            if col_idx == 1:  # Fecha
                cell.alignment = align_center
                if isinstance(val, (datetime.date, datetime.datetime)):
                    cell.number_format = "yyyy-mm-dd"
            elif col_idx in (2, 4, 5):  # Textos descriptivos (Alumno, Sección, Prueba)
                cell.alignment = align_left
            elif col_idx in (3, 6):  # Códigos/IDs
                cell.alignment = align_center
            elif col_idx in (7, 8, 9, 10):  # Enteros (Palabras, Tiempo, Aciertos, Fallos)
                cell.alignment = align_right
                cell.number_format = "#,##0"
            elif col_idx in (11, 12, 13):  # Decimales (PPM, Comprensión, Vef)
                cell.alignment = align_right
                cell.number_format = "#,##0.00"

    # 3. Ajuste automático del ancho de columnas para visualización óptima
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = cell.value
            if val is not None:
                str_val = val.strftime("%Y-%m-%d") if isinstance(val, (datetime.date, datetime.datetime)) else str(val)
                max_len = max(max_len, len(str_val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # 4. Exportar a buffer en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
