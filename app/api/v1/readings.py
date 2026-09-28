from flask import Blueprint, jsonify, request
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    SchemaValidationError,
    ValidationError,
)
from app.extensions import db
from app.services.reading_service import ReadingService

readings_bp = Blueprint("readings_v1", __name__)
single_readings_bp = Blueprint("single_readings_v1", __name__)


@readings_bp.route("/<student_id>/books", methods=["POST"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def assign_student_book(student_id):
    """
    Asigna un libro del catálogo de pruebas a un alumno registrando el inicio de lectura (BE-23).
    - 201 Created con el recurso y estado de lectura (Escenario 1 y 2).
    - 400 Bad Request si la prueba/libro no existe o está deshabilitada (Escenarios 3 y 4).
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 5).
    - 404 Not Found si el alumno no existe.
    - 409 Conflict si ya existe lectura idéntica para la misma fecha de inicio.
    - 422 Unprocessable Entity si la fecha de fin es anterior al inicio.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ReadingService(db.session)

    try:
        reading_data = service.assign_book(
            student_id=student_id,
            data=data,
            current_user=current_user,
        )
    except SchemaValidationError as e:
        return jsonify({"error": "UNPROCESSABLE_ENTITY", "message": str(e)}), 422
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(reading_data), 201


@single_readings_bp.route("", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def list_readings():
    """Listado general de lecturas activas/finalizadas con filtros y soporte para búsqueda."""
    import uuid
    from sqlalchemy import func, or_
    from sqlalchemy.orm import joinedload
    from app.models.book import ReadBook
    from app.models.student import Student
    from app.models.test import Test

    status_filter = request.args.get("status")
    student_id_filter = request.args.get("student_id")
    test_id_filter = request.args.get("test_id")
    book_title_filter = request.args.get("book_title") or request.args.get("book") or request.args.get("title")
    level_filter = request.args.get("level")
    filter_text = request.args.get("filter") or request.args.get("q") or request.args.get("search")

    query = (
        db.session.query(ReadBook)
        .outerjoin(ReadBook.test)
        .options(joinedload(ReadBook.student), joinedload(ReadBook.test))
    )

    if student_id_filter:
        try:
            query = query.filter(ReadBook.student_id == uuid.UUID(str(student_id_filter).strip()))
        except (ValueError, TypeError):
            pass

    if test_id_filter:
        try:
            query = query.filter(ReadBook.test_id == uuid.UUID(str(test_id_filter).strip()))
        except (ValueError, TypeError):
            pass

    if book_title_filter:
        term = str(book_title_filter).strip().lower()
        query = query.filter(
            (func.lower(ReadBook.book_title) == term) |
            (func.lower(Test.name) == term) |
            (func.lower(Test.code) == term)
        )

    if level_filter:
        lvl = str(level_filter).strip().upper()
        query = query.filter(
            (ReadBook.level == lvl) |
            (Test.test_letter == lvl) |
            (func.cast(Test.course, db.String) == lvl)
        )

    if filter_text:
        term = f"%{str(filter_text).strip().lower()}%"
        query = query.outerjoin(ReadBook.student).filter(
            or_(
                func.lower(ReadBook.book_title).like(term),
                func.lower(Test.name).like(term),
                func.lower(Test.code).like(term),
                func.lower(Student.name).like(term),
            )
        )

    readings = query.order_by(ReadBook.start_date.desc()).all()

    items = []
    for r in readings:
        is_completed = r.end_date is not None
        st = "finalizada" if is_completed else "en_curso"
        if status_filter and st != status_filter:
            continue
        duration = r.duration_days
        items.append({
            "id": str(r.id),
            "student_id": str(r.student_id),
            "student_name": r.student.name if r.student else "Alumno",
            "test_id": str(r.test_id) if r.test_id else None,
            "test_code": r.test_code,
            "book_id": str(r.test_id) if r.test_id else str(r.id),
            "book_title": r.book_title,
            "title": r.title,
            "book": r.book,
            "book_level": r.level,
            "level": r.level,
            "copies_note": r.copies_note,
            "sessions_note": r.sessions_note,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "duration_days": duration,
            "status": st
        })

    return jsonify({"items": items, "total": len(items)}), 200


@single_readings_bp.route("/titles", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def list_book_titles():
    """Catálogo agregado de libros/pruebas leídos y disponibles con métricas y nivel pedagógico."""
    from sqlalchemy import case, func
    from app.models.book import ReadBook
    from app.models.test import Test

    filter_text = request.args.get("filter") or request.args.get("q")
    level_filter = request.args.get("level")

    # 1. Pruebas oficiales activas
    test_rows = (
        db.session.query(
            Test.id.label("test_id"),
            Test.code.label("test_code"),
            Test.name.label("title"),
            case(
                (Test.test_letter.in_(["0", "0-I", "I", "I/II", "II"]), Test.test_letter),
                (Test.course == 0, "0"),
                (Test.course == 1, "I"),
                (Test.course >= 2, "II"),
                else_="0"
            ).label("level"),
            func.count(ReadBook.id).label("total_readings"),
            func.count(func.nullif(ReadBook.end_date.isnot(None), True)).label("active_readings")
        )
        .outerjoin(ReadBook, ReadBook.test_id == Test.id)
        .filter(Test.disabled_at.is_(None))
        .group_by(Test.id, Test.code, Test.name, Test.test_letter, Test.course)
        .all()
    )

    # 2. Libros propios registrados en lecturas que no están vinculados a tests
    custom_rows = (
        db.session.query(
            ReadBook.book_title.label("title"),
            ReadBook.level.label("level"),
            func.count(ReadBook.id).label("total_readings"),
            func.count(func.nullif(ReadBook.end_date.isnot(None), True)).label("active_readings")
        )
        .filter(ReadBook.test_id.is_(None))
        .group_by(ReadBook.book_title, ReadBook.level)
        .all()
    )

    items = []
    seen_titles = set()

    for r in test_rows:
        title_lower = r[2].strip().lower()
        seen_titles.add(title_lower)
        items.append({
            "test_id": str(r[0]) if r[0] else None,
            "test_code": r[1] if r[1] else None,
            "title": r[2],
            "book_title": r[2],
            "book": r[2],
            "level": r[3],
            "book_level": r[3],
            "total_readings": r[4],
            "active_readings": r[5],
        })

    for r in custom_rows:
        title_lower = r[0].strip().lower()
        if title_lower in seen_titles:
            continue
        items.append({
            "test_id": None,
            "test_code": None,
            "title": r[0],
            "book_title": r[0],
            "book": r[0],
            "level": r[1],
            "book_level": r[1],
            "total_readings": r[2],
            "active_readings": r[3],
        })

    if filter_text:
        term = filter_text.strip().lower()
        items = [
            it for it in items
            if term in it["title"].lower() or (it["test_code"] and term in it["test_code"].lower())
        ]

    if level_filter:
        lvl = level_filter.strip()
        items = [it for it in items if it["level"] == lvl]

    items.sort(key=lambda x: x["title"].lower())
    return jsonify({"items": items, "total": len(items)}), 200

@single_readings_bp.route("/test/<path:test_id>/students", methods=["GET"])
@single_readings_bp.route("/book/<path:book_title>/students", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_book_students_endpoint(test_id=None, book_title=None):
    """Consulta alumnos que han leído una prueba por ID o título."""
    identifier = test_id if test_id is not None else book_title
    status = request.args.get("status")
    current_user = get_current_user()
    service = ReadingService(db.session)
    results = service.get_book_students(identifier, status=status, current_user=current_user)
    return jsonify(results), 200


@single_readings_bp.route("", methods=["POST"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def create_reading():
    """Alias para asignar lectura directamente desde /api/v1/readings."""
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"error": "student_id es obligatorio"}), 400
    return assign_student_book(student_id)


@single_readings_bp.route("/<reading_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_reading(reading_id):
    """
    Cierre o reapertura de una lectura de libro (BE-24).
    - 200 OK con status 'finalizada' al fijar end_date (Escenario 1).
    - 422 Unprocessable Entity si end_date < start_date (Escenario 2).
    - 200 OK con status 'en curso' al pasar end_date nulo (reapertura, Escenario 4).
    - 404 Not Found si la lectura no existe (Escenario 5).
    - 403 Forbidden si el tutor no tiene asignada la sección del alumno o rol pendiente.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({"error": "Cuerpo de la petición inválido o ausente (se requiere JSON)"}),
            400,
        )

    current_user = get_current_user()
    service = ReadingService(db.session)

    try:
        reading_data = service.close_or_update_reading(
            reading_id=reading_id,
            data=data,
            current_user=current_user,
        )
    except SchemaValidationError as e:
        return jsonify({"error": "UNPROCESSABLE_ENTITY", "message": str(e)}), 422
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ConflictError as e:
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    return jsonify(reading_data), 200


@readings_bp.route("/<student_id>/books/<reading_id>", methods=["PATCH"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def update_student_reading(student_id, reading_id):
    """Alias anidado para actualización de lectura bajo /api/students/<student_id>/books/<reading_id>."""
    return update_reading(reading_id)


@readings_bp.route("/<student_id>/books", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_books(student_id):
    """
    Consulta el listado de lecturas de un alumno (BE-24 Escenario 3 y BE-26 Escenario 1).
    - 200 OK con la lista de lecturas con estado claramente indicado.
    - Soporta filtro opcional query param ?status=en curso o ?status=finalizada.
    - 404 Not Found si el alumno no existe.
    - 403 Forbidden si el tutor no tiene asignada la sección del alumno o rol pendiente.
    """
    current_user = get_current_user()
    service = ReadingService(db.session)

    status = request.args.get("status")

    try:
        readings = service.get_student_readings(
            student_id=student_id,
            status=status,
            current_user=current_user,
        )
    except ValidationError as e:
        response_payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            response_payload["field"] = e.field
        return jsonify(response_payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return jsonify(readings), 200
