"""Alta y modificación manual de alumnado, centros y secciones (BE-50).

Solo administradores. El servicio registra en auditoría cada operación
con el valor anterior de los campos modificados.
"""

from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint

from app.auth.decorators import get_current_user, require_role
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.extensions import db
from app.schemas.manual_crud_schema import (
    ManualCenterCreateSchema,
    ManualCenterResponseSchema,
    ManualCenterUpdateSchema,
    ManualErrorResponseSchema,
    ManualSectionCreateSchema,
    ManualSectionMembershipSchema,
    ManualSectionResponseSchema,
    ManualSectionUpdateSchema,
    ManualStudentCreateSchema,
    ManualStudentResponseSchema,
    ManualStudentUpdateSchema,
)
from app.services.manual_crud_service import ManualCrudService

students_manual_bp = Blueprint(
    "students_manual_v1",
    __name__,
    description="Alta y modificación manual de alumnado (BE-50)",
)
centers_manual_bp = Blueprint(
    "centers_manual_v1",
    __name__,
    description="Alta y modificación manual de centros (BE-50)",
)
sections_manual_bp = Blueprint(
    "sections_manual_v1",
    __name__,
    description="Alta y modificación manual de secciones (BE-50)",
)


@students_manual_bp.route("/students")
class ManualStudents(MethodView):
    @require_role("admin")
    @students_manual_bp.arguments(ManualStudentCreateSchema)
    @students_manual_bp.response(201, ManualStudentResponseSchema)
    @students_manual_bp.alt_response(400, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def post(self, payload):
        """Alta manual de un alumno (BE-50, Escenario 1)."""
        service = ManualCrudService(db.session)
        try:
            student = service.create_student(
                name=payload["name"],
                center_id=payload["center_id"],
                section_ids=payload["section_ids"],
                current_user=get_current_user(),
                birth_date=payload.get("birth_date"),
                gender=payload.get("gender"),
                academic_status=payload.get("academic_status"),
                sector=payload.get("sector"),
                area=payload.get("area"),
            )
            db.session.commit()
            return service.student_to_dict(student), 201
        except ValidationError as e:
            abort(400, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))


@students_manual_bp.route("/students/<student_id>")
class ManualStudentDetail(MethodView):
    @require_role("admin")
    @students_manual_bp.arguments(ManualStudentUpdateSchema)
    @students_manual_bp.response(200, ManualStudentResponseSchema)
    @students_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def patch(self, payload, student_id):
        """Modificación de los datos de un alumno (BE-50, Escenario 2)."""
        service = ManualCrudService(db.session)
        try:
            student = service.update_student(student_id, payload, get_current_user())
            db.session.commit()
            return service.student_to_dict(student), 200
        except NotFoundError as e:
            abort(404, description=str(e))

    @require_role("admin")
    @students_manual_bp.response(204)
    @students_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    def delete(self, student_id):
        """Baja lógica de un alumno (BE-50, Escenario 5)."""
        service = ManualCrudService(db.session)
        try:
            service.soft_delete_student(student_id, get_current_user())
            db.session.commit()
            return "", 204
        except NotFoundError as e:
            abort(404, description=str(e))


@students_manual_bp.route("/students/<student_id>/sections")
class ManualStudentSectionMembership(MethodView):
    @require_role("admin")
    @students_manual_bp.arguments(ManualSectionMembershipSchema)
    @students_manual_bp.response(200, ManualStudentResponseSchema)
    @students_manual_bp.alt_response(400, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def post(self, payload, student_id):
        """Asignar una sección a un alumno."""
        service = ManualCrudService(db.session)
        try:
            student = service.assign_student_section(
                student_id, payload["section_id"], get_current_user()
            )
            db.session.commit()
            return service.student_to_dict(student), 200
        except ValidationError as e:
            abort(400, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))
        except ConflictError as e:
            abort(409, description=str(e))


@students_manual_bp.route("/students/<student_id>/sections/<section_id>")
class ManualStudentSectionRemoval(MethodView):
    @require_role("admin")
    @students_manual_bp.response(204)
    @students_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @students_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    def delete(self, student_id, section_id):
        """Retirar una sección de un alumno."""
        service = ManualCrudService(db.session)
        try:
            service.remove_student_section(
                student_id, section_id, get_current_user()
            )
            db.session.commit()
            return "", 204
        except NotFoundError as e:
            abort(404, description=str(e))


@centers_manual_bp.route("/centers")
class ManualCenters(MethodView):
    @require_role("admin")
    @centers_manual_bp.arguments(ManualCenterCreateSchema)
    @centers_manual_bp.response(201, ManualCenterResponseSchema)
    @centers_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def post(self, payload):
        """Alta manual de un centro."""
        service = ManualCrudService(db.session)
        try:
            center = service.create_center(payload["name"], get_current_user())
            db.session.commit()
            return center, 201
        except ConflictError as e:
            abort(409, description=str(e))


@centers_manual_bp.route("/centers/<center_id>")
class ManualCenterDetail(MethodView):
    @require_role("admin")
    @centers_manual_bp.arguments(ManualCenterUpdateSchema)
    @centers_manual_bp.response(200, ManualCenterResponseSchema)
    @centers_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def patch(self, payload, center_id):
        """Modificación de un centro."""
        service = ManualCrudService(db.session)
        try:
            center = service.update_center(center_id, payload, get_current_user())
            db.session.commit()
            return center, 200
        except ConflictError as e:
            abort(409, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))

    @require_role("admin")
    @centers_manual_bp.response(204)
    @centers_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @centers_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    def delete(self, center_id):
        """Baja lógica de un centro."""
        service = ManualCrudService(db.session)
        try:
            service.soft_delete_center(center_id, get_current_user())
            db.session.commit()
            return "", 204
        except NotFoundError as e:
            abort(404, description=str(e))


@sections_manual_bp.route("/sections")
class ManualSections(MethodView):
    @require_role("admin")
    @sections_manual_bp.arguments(ManualSectionCreateSchema)
    @sections_manual_bp.response(201, ManualSectionResponseSchema)
    @sections_manual_bp.alt_response(400, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def post(self, payload):
        """Alta manual de una sección (BE-50, Escenario 7: sin centro → 400)."""
        service = ManualCrudService(db.session)
        try:
            section = service.create_section(
                name=payload["name"],
                center_id=payload.get("center_id"),
                academic_year=payload.get("academic_year"),
                current_user=get_current_user(),
            )
            db.session.commit()
            return section, 201
        except ValidationError as e:
            abort(400, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))
        except ConflictError as e:
            abort(409, description=str(e))


@sections_manual_bp.route("/sections/<section_id>")
class ManualSectionDetail(MethodView):
    @require_role("admin")
    @sections_manual_bp.arguments(ManualSectionUpdateSchema)
    @sections_manual_bp.response(200, ManualSectionResponseSchema)
    @sections_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(409, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(422, schema=ManualErrorResponseSchema)
    def patch(self, payload, section_id):
        """Modificación de una sección."""
        service = ManualCrudService(db.session)
        try:
            section = service.update_section(section_id, payload, get_current_user())
            db.session.commit()
            return section, 200
        except ConflictError as e:
            abort(409, description=str(e))
        except NotFoundError as e:
            abort(404, description=str(e))

    @require_role("admin")
    @sections_manual_bp.response(204)
    @sections_manual_bp.alt_response(403, schema=ManualErrorResponseSchema)
    @sections_manual_bp.alt_response(404, schema=ManualErrorResponseSchema)
    def delete(self, section_id):
        """Baja lógica de una sección."""
        service = ManualCrudService(db.session)
        try:
            service.soft_delete_section(section_id, get_current_user())
            db.session.commit()
            return "", 204
        except NotFoundError as e:
            abort(404, description=str(e))