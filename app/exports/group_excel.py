"""
Generador de informes Excel (.xlsx) para grupos y centros (BE-37 / Escenario 5).

Reutiliza openpyxl para construir un libro estructurado con:
- Hoja 'Resumen': Datos identificativos, totales y medias.
- Hoja 'Distribución': Tramos pedagógicos de velocidad y comprensión, y estadísticos.
- Hoja 'Desglose Secciones' (para informe de centro): Comparativa entre secciones.
- Tipos de datos nativos reales (fechas, enteros, decimales) y formato visual corporativo.
"""

import io
from typing import Any, Dict, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def generate_group_report_excel(
    report_data: Dict[str, Any],
    is_center: bool = False,
) -> io.BytesIO:
    """
    Genera un libro Excel en memoria para un informe de grupo o centro.

    :param report_data: Diccionario con la estructura del informe (generado por GroupReportService).
    :param is_center: True si es informe de centro con desglose de secciones.
    :return: BytesIO con el contenido binario del archivo .xlsx.
    """
    wb = openpyxl.Workbook()

    # Estilos compartidos
    title_font = Font(name="Arial", size=14, bold=True, color="1F4E79")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    sub_header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    data_font = Font(name="Arial", size=10)
    bold_font = Font(name="Arial", size=10, bold=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    # -------------------------------------------------------------
    # 1. Hoja "Resumen"
    # -------------------------------------------------------------
    ws_summary = wb.active
    ws_summary.title = "Resumen"
    ws_summary.views.sheetView[0].showGridLines = True

    entity_type = "Centro" if is_center else "Sección"
    entity_name = report_data.get("name", "N/A")
    title_text = f"INFORME AGREGADO DE {entity_type.upper()}: {entity_name.upper()}"

    ws_summary.cell(row=1, column=1, value=title_text).font = title_font
    ws_summary.row_dimensions[1].height = 25

    metadata_rows = [
        ("Tipo de Informe", f"Informe de {entity_type}"),
        ("Nombre", entity_name),
        ("Año Académico", report_data.get("academic_year") or "N/A"),
        ("Fecha de Generación", str(report_data.get("generated_at", ""))[:19].replace("T", " ")),
        ("Tiene Datos Registrados", "Sí" if report_data.get("has_data") else "No"),
    ]

    curr_row = 3
    for label, val in metadata_rows:
        c1 = ws_summary.cell(row=curr_row, column=1, value=label)
        c1.font = bold_font
        c1.alignment = align_left
        c2 = ws_summary.cell(row=curr_row, column=2, value=val)
        c2.font = data_font
        c2.alignment = align_left
        curr_row += 1

    curr_row += 1
    # Métricas agregadas
    ws_summary.cell(row=curr_row, column=1, value="Indicador").font = header_font
    ws_summary.cell(row=curr_row, column=1).fill = header_fill
    ws_summary.cell(row=curr_row, column=1).alignment = align_center

    ws_summary.cell(row=curr_row, column=2, value="Valor").font = header_font
    ws_summary.cell(row=curr_row, column=2).fill = header_fill
    ws_summary.cell(row=curr_row, column=2).alignment = align_center
    ws_summary.row_dimensions[curr_row].height = 22

    summary_metrics = [
        ("Participantes Únicos", report_data.get("participants_count", 0), False),
        ("Total de Pruebas Realizadas", report_data.get("results_count", 0), False),
        (
            "Media Palabras Por Minuto (PPM)",
            report_data.get("mean_ppm"),
            True,
        ),
        (
            "Media Porcentaje de Comprensión / Precisión (%)",
            report_data.get("mean_accuracy"),
            True,
        ),
        (
            "Media Velocidad Eficaz (Vef)",
            report_data.get("mean_vef"),
            True,
        ),
    ]

    curr_row += 1
    for label, val, is_float in summary_metrics:
        c1 = ws_summary.cell(row=curr_row, column=1, value=label)
        c1.font = data_font
        c1.border = thin_border
        c1.alignment = align_left

        c2 = ws_summary.cell(row=curr_row, column=2)
        if val is None:
            c2.value = "Sin datos"
            c2.alignment = align_center
        elif is_float:
            c2.value = float(val)
            c2.number_format = "#,##0.00"
            c2.alignment = align_right
        else:
            c2.value = int(val)
            c2.number_format = "#,##0"
            c2.alignment = align_right

        c2.font = bold_font
        c2.border = thin_border
        curr_row += 1

    # Autoajuste de columnas de Resumen
    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_summary.column_dimensions[col_letter].width = max(max_len + 4, 16)

    # -------------------------------------------------------------
    # 2. Hoja "Distribución"
    # -------------------------------------------------------------
    distribution = report_data.get("distribution")
    if distribution:
        ws_dist = wb.create_sheet(title="Distribución")
        ws_dist.views.sheetView[0].showGridLines = True

        # Tabla 1: Distribución Comprensión
        ws_dist.cell(row=1, column=1, value="DISTRIBUCIÓN DE COMPRENSIÓN LECTORA (%)").font = title_font
        dist_row = 3
        headers_dist = ["Tramo", "Descripción / Nivel", "Nº Alumnos / Pruebas", "Porcentaje (%)"]
        for col_idx, h in enumerate(headers_dist, 1):
            cell = ws_dist.cell(row=dist_row, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
        ws_dist.row_dimensions[dist_row].height = 22

        dist_row += 1
        for item in distribution.get("accuracy_brackets", []):
            ws_dist.cell(row=dist_row, column=1, value=item["bracket"]).alignment = align_center
            ws_dist.cell(row=dist_row, column=2, value=item["label"]).alignment = align_left
            c_cnt = ws_dist.cell(row=dist_row, column=3, value=int(item["count"]))
            c_cnt.number_format = "#,##0"
            c_cnt.alignment = align_right
            c_pct = ws_dist.cell(row=dist_row, column=4, value=float(item["percentage"]))
            c_pct.number_format = "0.00"
            c_pct.alignment = align_right

            for col_idx in range(1, 5):
                c = ws_dist.cell(row=dist_row, column=col_idx)
                c.font = data_font
                c.border = thin_border
            dist_row += 1

        dist_row += 2
        # Tabla 2: Distribución Velocidad PPM
        ws_dist.cell(row=dist_row, column=1, value="DISTRIBUCIÓN DE VELOCIDAD (PPM)").font = title_font
        dist_row += 2
        headers_ppm = ["Tramo", "Rango de PPM", "Nº Alumnos / Pruebas", "Porcentaje (%)"]
        for col_idx, h in enumerate(headers_ppm, 1):
            cell = ws_dist.cell(row=dist_row, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = sub_header_fill
            cell.alignment = align_center
        ws_dist.row_dimensions[dist_row].height = 22

        dist_row += 1
        for item in distribution.get("ppm_brackets", []):
            ws_dist.cell(row=dist_row, column=1, value=item["bracket"]).alignment = align_center
            ws_dist.cell(row=dist_row, column=2, value=item["label"]).alignment = align_left
            c_cnt = ws_dist.cell(row=dist_row, column=3, value=int(item["count"]))
            c_cnt.number_format = "#,##0"
            c_cnt.alignment = align_right
            c_pct = ws_dist.cell(row=dist_row, column=4, value=float(item["percentage"]))
            c_pct.number_format = "0.00"
            c_pct.alignment = align_right

            for col_idx in range(1, 5):
                c = ws_dist.cell(row=dist_row, column=col_idx)
                c.font = data_font
                c.border = thin_border
            dist_row += 1

        dist_row += 2
        # Tabla 3: Estadísticos
        ws_dist.cell(row=dist_row, column=1, value="ESTADÍSTICOS DESCRIPTIVOS").font = title_font
        dist_row += 2
        headers_stats = ["Métrica", "Mínimo", "Máximo", "Mediana", "Q1 (25%)", "Q3 (75%)", "Desv. Típica"]
        for col_idx, h in enumerate(headers_stats, 1):
            cell = ws_dist.cell(row=dist_row, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
        ws_dist.row_dimensions[dist_row].height = 22

        dist_row += 1
        stats_data = distribution.get("stats", {})
        stat_rows = [
            ("Velocidad (PPM)", stats_data.get("ppm", {})),
            ("Comprensión (%)", stats_data.get("accuracy", {})),
            ("Velocidad Eficaz (Vef)", stats_data.get("vef", {})),
        ]
        for m_name, m_stats in stat_rows:
            ws_dist.cell(row=dist_row, column=1, value=m_name).alignment = align_left
            keys = ["min", "max", "median", "q1", "q3", "std_dev"]
            for k_idx, k in enumerate(keys, 2):
                val = m_stats.get(k)
                cell = ws_dist.cell(row=dist_row, column=k_idx)
                if val is not None:
                    cell.value = float(val)
                    cell.number_format = "#,##0.00"
                    cell.alignment = align_right
                else:
                    cell.value = "N/A"
                    cell.alignment = align_center

            for col_idx in range(1, 8):
                c = ws_dist.cell(row=dist_row, column=col_idx)
                c.font = data_font
                c.border = thin_border
            dist_row += 1

        for col in ws_dist.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_dist.column_dimensions[col_letter].width = max(max_len + 4, 14)

    # -------------------------------------------------------------
    # 3. Hoja "Desglose Secciones" (para informe de centro)
    # -------------------------------------------------------------
    sections = report_data.get("sections")
    if is_center and sections is not None:
        ws_sec = wb.create_sheet(title="Desglose Secciones")
        ws_sec.views.sheetView[0].showGridLines = True

        ws_sec.cell(row=1, column=1, value=f"DESGLOSE POR SECCIÓN: {entity_name.upper()}").font = title_font

        headers_sec = [
            "Sección",
            "Año Académico",
            "Participantes",
            "Pruebas",
            "Media PPM",
            "Media Comprensión (%)",
            "Media Vef",
            "Tiene Datos",
        ]
        sec_row = 3
        for col_idx, h in enumerate(headers_sec, 1):
            cell = ws_sec.cell(row=sec_row, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
        ws_sec.row_dimensions[sec_row].height = 22

        sec_row += 1
        for s in sections:
            ws_sec.cell(row=sec_row, column=1, value=s.get("name", "N/A")).alignment = align_left
            ws_sec.cell(row=sec_row, column=2, value=s.get("academic_year") or "N/A").alignment = align_center

            c_part = ws_sec.cell(row=sec_row, column=3, value=int(s.get("participants_count", 0)))
            c_part.number_format = "#,##0"
            c_part.alignment = align_right

            c_res = ws_sec.cell(row=sec_row, column=4, value=int(s.get("results_count", 0)))
            c_res.number_format = "#,##0"
            c_res.alignment = align_right

            # PPM
            c_ppm = ws_sec.cell(row=sec_row, column=5)
            if s.get("mean_ppm") is not None:
                c_ppm.value = float(s["mean_ppm"])
                c_ppm.number_format = "#,##0.00"
                c_ppm.alignment = align_right
            else:
                c_ppm.value = "N/A"
                c_ppm.alignment = align_center

            # Comprensión
            c_acc = ws_sec.cell(row=sec_row, column=6)
            if s.get("mean_accuracy") is not None:
                c_acc.value = float(s["mean_accuracy"])
                c_acc.number_format = "0.00"
                c_acc.alignment = align_right
            else:
                c_acc.value = "N/A"
                c_acc.alignment = align_center

            # Vef
            c_vef = ws_sec.cell(row=sec_row, column=7)
            if s.get("mean_vef") is not None:
                c_vef.value = float(s["mean_vef"])
                c_vef.number_format = "#,##0.00"
                c_vef.alignment = align_right
            else:
                c_vef.value = "N/A"
                c_vef.alignment = align_center

            ws_sec.cell(row=sec_row, column=8, value="Sí" if s.get("has_data") else "No").alignment = align_center

            for col_idx in range(1, 9):
                c = ws_sec.cell(row=sec_row, column=col_idx)
                c.font = data_font
                c.border = thin_border
            sec_row += 1

        for col in ws_sec.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_sec.column_dimensions[col_letter].width = max(max_len + 4, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
