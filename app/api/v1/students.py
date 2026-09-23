from flask import Blueprint, abort, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint as SmorestBlueprint
from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.schemas.common import StudentFilterArgsSchema, StudentSearchQuerySchema
from app.schemas.student_schema import (
    StudentErrorResponseSchema,
    StudentListResponseSchema,
    StudentSearchResponseSchema,
)
from app.services.student_service import StudentService

students_bp = Blueprint("students_v1", __name__)

students_list_bp = SmorestBlueprint(
    "students_list_v1",
    __name__,
    description="Listado paginado y filtrado multicriterio del alumnado (BE-27)",
)

students_search_bp = SmorestBlueprint(
    "students_search_v1",
    __name__,
    description="Búsqueda de alumnos por fragmento de nombre (BE-29)",
)


@students_list_bp.route("")
class StudentList(MethodView):
    """Listado del alumnado con filtros combinables (BE-27)."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @students_list_bp.arguments(StudentFilterArgsSchema, location="query")
    @students_list_bp.response(200, StudentListResponseSchema)
    @students_list_bp.alt_response(400, schema=StudentErrorResponseSchema)
    @students_list_bp.alt_response(403, schema=StudentErrorResponseSchema)
    @students_list_bp.alt_response(422, schema=StudentErrorResponseSchema)
    def get(self, filters):
        """
        Devuelve el alumnado activo que cumple todos los criterios (AND).

        - Tutor: ámbito restringido a sus secciones asignadas (Escenario 6).
        - `__missing__` en academic_status/sector selecciona los alumnos
          sin ese campo informado; `missing_data` indica cuántos se omitieron
          por no tenerlo (Escenario 5).
        - 403 Forbidden si el rol es 'pendiente' o si el tutor no tiene secciones.
        """
        current_user = get_current_user()
        service = StudentService(db.session)

        try:
            return service.list_students(filters=filters, current_user=current_user)
        except ValidationError as e:
            abort(400, description=str(e))
        except ForbiddenError as e:
            abort(403, description=str(e))


@students_search_bp.route("/search")
class StudentSearch(MethodView):
    """Búsqueda de alumnos por fragmento de nombre (BE-29)."""

    @require_role("tutor", "coordinator", "coordinador", "admin")
    @students_search_bp.arguments(StudentSearchQuerySchema, location="query")
    @students_search_bp.response(200, StudentSearchResponseSchema)
    @students_search_bp.alt_response(400, schema=StudentErrorResponseSchema)
    @students_search_bp.alt_response(403, schema=StudentErrorResponseSchema)
    @students_search_bp.alt_response(422, schema=StudentErrorResponseSchema)
    def get(self, args):
        """
        Busca alumnos cuyo nombre contiene el fragmento dado.

        - Normalización insensible a acentos y mayúsculas (Esc. 2).
        - Sin mínimo de caracteres; acepta 1 o 2 caracteres (Esc. 3).
        - Cada resultado incluye secciones activas con su centro (Esc. 4).
        - Tutor: ámbito restringido a sus secciones asignadas (Esc. 5).
        """
        current_user = get_current_user()
        service = StudentService(db.session)

        try:
            return service.search_students(
                term=args["q"],
                page=args.get("page", 1),
                limit=args.get("limit", 10),
                current_user=current_user,
            )
        except ValidationError as e:
            abort(400, description=str(e))
        except ForbiddenError as e:
            abort(403, description=str(e))


@students_bp.route("/no-progress", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_students_without_progress():
    """
    Listado de detección de alumnos sin progreso (BE-34).
    - Identifica alumnos con tendencia negativa (Escenario 1) y tendencia plana (Escenario 2).
    - Separa estrictamente 'insufficient_data' sin mezclarlo con 'no_progress' (Escenario 3).
    - Parámetros configurables: n_tests (default 3), threshold (default 0.0), metric (default 'ppm') y section_id (Escenario 4).
    - Alcance por rol: tutores solo ven alumnos de sus secciones asignadas (Escenario 5).
    - 403 Forbidden si el rol es 'pendiente' o si el tutor consulta una sección no asignada.
    - 401 Unauthorized si no hay sesión autenticada.
    """
    current_user = get_current_user()
    service = StudentService(db.session)

    raw_n_tests = request.args.get("n_tests") or request.args.get("last_n_tests")
    try:
        n_tests = int(raw_n_tests) if raw_n_tests is not None else 3
    except (ValueError, TypeError):
        return (
            jsonify(
                {
                    "error": "El parámetro 'n_tests' debe ser un número entero válido",
                    "field": "n_tests",
                }
            ),
            400,
        )

    raw_threshold = request.args.get("threshold")
    try:
        threshold = float(raw_threshold) if raw_threshold is not None else 0.0
    except (ValueError, TypeError):
        return (
            jsonify(
                {
                    "error": "El parámetro 'threshold' debe ser un número decimal válido",
                    "field": "threshold",
                }
            ),
            400,
        )

    metric = request.args.get("metric", "ppm")
    section_id = request.args.get("section_id")

    try:
        result = service.get_students_without_progress(
            current_user=current_user,
            n_tests=n_tests,
            threshold=threshold,
            metric=metric,
            section_id=section_id,
        )
    except ValidationError as e:
        payload = {"error": str(e)}
        if hasattr(e, "field") and e.field:
            payload["field"] = e.field
        return jsonify(payload), 400
    except NotFoundError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403

    return jsonify(result), 200


@students_bp.route("/<student_id>", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_detail(student_id):

    """
    Consulta la ficha agregada del alumno en una sola petición (BE-28).
    - 200 OK con datos personales, secciones, resultados y lecturas (Escenarios 1, 2, 3 y 4).
    - 400 Bad Request si el UUID no es válido.
    - 404 Not Found si el alumno no existe (Escenario 5).
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 5).
    - 401 Unauthorized si no hay sesión autenticada.
    """
    current_user = get_current_user()
    service = StudentService(db.session)

    try:
        data = service.get_student_detail(
            student_id=student_id,
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

    return jsonify(data), 200


@students_bp.route("/<student_id>/report", methods=["GET"])
@require_role("tutor", "coordinator", "coordinador", "admin")
def get_student_report(student_id):
    """
    Consulta los datos estructurados para el informe individual de un alumno (BE-36).
    - 200 OK con datos personales, secciones, resultados con métricas, lecturas y serie de evolución.
    - Soporta acotación opcional por start_date y end_date.
    - 400 Bad Request si el UUID del alumno no es válido.
    - 404 Not Found si el alumno no existe.
    - 403 Forbidden si el tutor no tiene permiso sobre el alumno o rol 'pendiente' (Escenario 4).
    - 401 Unauthorized si la petición no está autenticada.
    """
    current_user = get_current_user()
    service = StudentService(db.session)

    start_date = request.args.get("start_date") or request.args.get("from_date")
    end_date = request.args.get("end_date") or request.args.get("to_date")

    try:
        report_data = service.get_student_report(
            student_id=student_id,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
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

    return jsonify(report_data), 200
