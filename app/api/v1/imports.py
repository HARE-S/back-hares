"""Informe de errores de importación (BE-08) y subida de fichero (BE-09).

BE-08: el administrador descarga la lista de filas rechazadas en la última
importación de alumnado como CSV. La descarga queda registrada en auditoría.

BE-09: el administrador sube el CSV de Alexia desde el navegador, previsualiza
las primeras filas sin escribir en base de datos, y confirma la importación
reutilizando exactamente el mismo parser/loader del importador por CLI.
"""
import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from app.auth.decorators import get_current_user, require_role
from app.core.audit import log_audit
from app.core.exceptions import ValidationError
from app.core.upload_store import upload_store
from app.extensions import db
from app.importer import StudentImporter, parse_students_csv_collect
from app.models.import_report import ImportReport

import_bp = Blueprint("import_v1", __name__)

CSV_FILENAME = "informe_errores_importacion.csv"
PREVIEW_MAX_ROWS = 5
ERROR_DETAILS_MAX = 5


def _csv_from_report(report: ImportReport) -> "flask.wrappers.Response":
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["linea", "columna", "motivo"])
    for detail in report.error_details or []:
        writer.writerow([
            detail.get("line", ""),
            detail.get("column", "") or "",
            detail.get("reason", ""),
        ])

    from flask import Response

    return Response(
        output.getvalue(),
        status=200,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{CSV_FILENAME}"',
        },
    )


@import_bp.route("/report")
@require_role("admin")
def get_import_report():
    """Descarga el informe de errores de la última importación (BE-08).

    - 200 con el informe en CSV si existe alguna importación previa.
    - 404 si todavía no se ha importado ningún fichero.
    """
    stmt = (
        select(ImportReport)
        .order_by(ImportReport.created_at.desc(), ImportReport.id.desc())
        .limit(1)
    )
    report = db.session.scalars(stmt).first()

    if report is None:
        return (
            jsonify({"error": "No existe ningún informe de importación todavía"}),
            404,
        )

    log_audit(
        get_current_user(),
        action="descargar_informe_errores",
        resource_type="import_report",
        resource_id=report.id,
        details={
            "total": report.total,
            "processed": report.processed,
            "errors": report.errors,
            "queried_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return _csv_from_report(report)


@import_bp.route("/upload", methods=["POST"])
@require_role("admin")
def upload_import_file():
    """Subida y previsualización del CSV de Alexia (BE-09 Escenarios 1, 3 y 4).

    - 200 con token, previsualización y recuentos; NO escribe en la BD.
    - 400 si falta el fichero, la extensión no es válida, supera el tamaño
      máximo, no es UTF-8 o el CSV no tiene la cabecera esperada.
    """
    current_user = get_current_user()

    allowed_extensions = set(
        current_app.config.get("IMPORT_ALLOWED_EXTENSIONS", {".csv"})
    )
    max_bytes = int(current_app.config.get("IMPORT_UPLOAD_MAX_BYTES", 0) or 0)

    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "El campo 'file' es obligatorio"}), 400

    extension = Path(file.filename).suffix.lower()
    if extension not in allowed_extensions:
        return (
            jsonify(
                {
                    "error": (
                        "Extensión no permitida. Extensiones válidas: "
                        + ", ".join(sorted(allowed_extensions))
                    )
                }
            ),
            400,
        )

    if max_bytes > 0:
        raw = file.stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return (
                jsonify(
                    {
                        "error": (
                            "El fichero supera el tamaño máximo permitido "
                            f"({max_bytes} bytes)"
                        )
                    }
                ),
                400,
            )
    else:
        raw = file.stream.read()

    extra_data = None
    if extension in (".xlsx", ".xls"):
        try:
            import openpyxl
            from app.importer.lectura_eficaz_parser import is_lectura_eficaz_excel, parse_lectura_eficaz_workbook

            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
            if is_lectura_eficaz_excel(wb):
                students_list, evaluations_list, csv_content = parse_lectura_eficaz_workbook(wb)
                content = csv_content
                extra_data = {
                    "is_lectura_eficaz": True,
                    "evaluations": evaluations_list,
                    "students_count": len(students_list),
                    "evaluations_count": len(evaluations_list),
                }
            else:
                sheet = wb.active
                csv_lines = []
                first_row = True
                header_aliases = {
                    "student_id": "student_id",
                    "id": "student_id",
                    "identificador": "student_id",
                    "codigo": "student_id",
                    "student_name": "student_name",
                    "nombre": "student_name",
                    "alumno": "student_name",
                    "nombre_alumno": "student_name",
                    "sections": "sections",
                    "secciones": "sections",
                    "seccion": "sections",
                    "grupo": "sections",
                    "grupos": "sections",
                    "center": "center",
                    "centro": "center",
                    "colegio": "center",
                }
                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):
                        if first_row:
                            first_row = False
                            mapped = []
                            for cell in row:
                                val = str(cell if cell is not None else "").strip().lower()
                                mapped.append(header_aliases.get(val, val))
                            line = ";".join(mapped)
                        else:
                            line = ";".join(str(cell if cell is not None else "").strip() for cell in row)
                        csv_lines.append(line)
                content = "\n".join(csv_lines)
        except Exception as exc:
            return jsonify({"error": f"Error al procesar el archivo Excel: {str(exc)}"}), 400
    else:
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "El fichero debe estar codificado en UTF-8"}), 400

    try:
        rows, errors = parse_students_csv_collect(content)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    token = upload_store.put(file.filename, content, extra=extra_data)

    preview = [
        {
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "sections": row["sections"],
            "center": row["center"],
        }
        for row in rows[:PREVIEW_MAX_ROWS]
    ]

    log_audit(
        current_user,
        action="subir_fichero_importacion",
        resource_type="import",
        resource_id=token,
        details={
            "filename": file.filename,
            "total_rows": len(rows) + len(errors),
            "errors": len(errors),
        },
    )

    resp_payload = {
        "token": token,
        "filename": file.filename,
        "preview": preview,
        "total_rows": len(rows) + len(errors),
        "errors": len(errors),
        "error_details": errors[:ERROR_DETAILS_MAX],
        "allowed_extensions": sorted(allowed_extensions),
        "max_bytes": max_bytes,
    }
    if extra_data and extra_data.get("is_lectura_eficaz"):
        resp_payload["meta"] = {
            "type": "lectura_eficaz",
            "students_count": extra_data["students_count"],
            "evaluations_count": extra_data["evaluations_count"],
        }
    return jsonify(resp_payload), 200


@import_bp.route("/confirm", methods=["POST"])
@require_role("admin")
def confirm_import():
    """Confirmación de la importación del fichero subido (BE-09 Escenario 2).

    - 200 con el resumen de ejecución, idéntico al del importador por CLI.
    - 400 si falta el token; 404 si no existe o ha caducado.
    - 500 si falla la escritura (el fichero se conserva para reintentar).
    """
    current_user = get_current_user()

    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "El campo 'token' es obligatorio"}), 400

    entry = upload_store.get(token)
    if entry is None:
        return jsonify({"error": "El fichero subido no existe o ha caducado"}), 404

    try:
        summary = StudentImporter(db.session, current_user=get_current_user()).import_from_csv(
            entry["content"], commit=True
        )

        extra = entry.get("extra") or {}
        if extra.get("is_lectura_eficaz"):
            evaluations = extra.get("evaluations", [])
            evaluations_created = 0
            if evaluations:
                from app.models.student import Student
                from app.models.center import Section
                from app.models.test import Test, Result
                from datetime import date

                tests_by_code = {t.code: t for t in db.session.execute(select(Test)).scalars().all()}
                students_by_ext_id = {s.external_id: s for s in db.session.execute(select(Student)).scalars().all()}
                sections_by_name = {sec.name: sec for sec in db.session.execute(select(Section)).scalars().all()}

                for ev in evaluations:
                    student = students_by_ext_id.get(ev["student_id"])
                    test = tests_by_code.get(ev["test_code"])
                    section = sections_by_name.get(ev["section_name"])

                    if not section and student and student.student_sections:
                        section = student.student_sections[0].section

                    if student and test and section:
                        test_date = date.fromisoformat(ev["test_date"])
                        existing = db.session.execute(
                            select(Result).where(
                                Result.student_id == student.id,
                                Result.test_id == test.id,
                                Result.test_date == test_date,
                            )
                        ).scalar_one_or_none()

                        if not existing:
                            new_res = Result(
                                student_id=student.id,
                                section_id=section.id,
                                test_id=test.id,
                                test_date=test_date,
                                time=ev["time"],
                                successes=ev["successes"],
                                mistakes=ev["mistakes"],
                                anomalous=False,
                            )
                            db.session.add(new_res)
                            evaluations_created += 1

                db.session.commit()
                summary["evaluations_created"] = evaluations_created
    except Exception as exc:  # noqa: BLE001 - se conserva el fichero para reintentar
        db.session.rollback()
        return jsonify({"error": f"Error durante la importación: {exc}"}), 500

    upload_store.delete(token)

    report = (
        db.session.scalars(
            select(ImportReport)
            .order_by(ImportReport.created_at.desc(), ImportReport.id.desc())
            .limit(1)
        ).first()
    )

    log_audit(
        current_user,
        action="importar_alumnado",
        resource_type="import_report",
        resource_id=report.id if report else token,
        details={
            "filename": entry["filename"],
            "total": summary["total"],
            "processed": summary["processed"],
            "errors": summary["errors"],
            "students_created": summary["students_created"],
            "students_updated": summary["students_updated"],
        },
    )

    return (
        jsonify(
            {
                "message": "Importación completada",
                "report_id": str(report.id) if report else None,
                "summary": summary,
            }
        ),
        200,
    )