"""CRUD manual de alumnado, centros y secciones (BE-50).

Solo administradores. Toda operación queda en auditoría (BE-44) con
el valor anterior de los campos modificados.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


class ManualCrudService:

    def __init__(self, session: Session):
        self.session = session

    # ---------------------------------------------------------------- utils
    @staticmethod
    def _generate_manual_external_id() -> str:
        return f"MAN-{uuid.uuid4().hex}"

    @staticmethod
    def _extract_user_id(current_user):
        """Id ubíguo del usuario autenticado como cadena UUID, o None si no procede."""
        if not isinstance(current_user, dict) or not current_user.get("id"):
            return None
        try:
            return uuid.UUID(str(current_user["id"]))
        except (ValueError, TypeError):
            return None

    def _get_active_student(self, student_id) -> Student:
        student = self.session.get(Student, student_id)
        if student is None:
            raise NotFoundError("Alumno no encontrado.")
        return student

    def _get_active_center(self, center_id) -> Center:
        stmt = select(Center).where(Center.id == center_id, Center.disabled_at.is_(None))
        center = self.session.scalars(stmt).first()
        if center is None:
            raise NotFoundError("Centro no encontrado o dado de baja.")
        return center

    def _get_active_section(self, section_id) -> Section:
        stmt = select(Section).where(Section.id == section_id, Section.disabled_at.is_(None))
        section = self.session.scalars(stmt).first()
        if section is None:
            raise NotFoundError("Sección no encontrada o dada de baja.")
        return section

    def _has_enrollment(self, student: Student, section: Section) -> bool:
        stmt = select(StudentSection).where(
            StudentSection.student_id == student.id,
            StudentSection.section_id == section.id,
        )
        return self.session.scalars(stmt).first() is not None

    def _log(self, current_user, action, resource_type, resource_id, details=None):
        email = current_user.get("email") if isinstance(current_user, dict) else "anonymous"
        log_audit(
            user=current_user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or {},
        )

    # --------------------------------------------------------------- students
    def create_student(
        self,
        name: str,
        center_id,
        section_ids: List,
        current_user,
        **profile_fields,
    ) -> Student:
        center = self._get_active_center(center_id)

        sections = []
        for sid in section_ids:
            section = self._get_active_section(sid)
            if section.center_id != center.id:
                raise ValidationError(
                    f"La sección {sid} no pertenece al centro indicado."
                )
            sections.append(section)

        student = Student(
            external_id=self._generate_manual_external_id(),
            name=name,
            origin="manual",
            created_by_user_id=self._extract_user_id(current_user),
        )
        for field in ("academic_status", "sector", "area"):
            val = profile_fields.get(field)
            if val is not None:
                setattr(student, field, val)
        self.session.add(student)
        self.session.flush()

        for section in sections:
            self.session.add(StudentSection(student_id=student.id, section_id=section.id))
        self.session.flush()

        self._log(current_user, "CREATE_STUDENT_MANUAL", "student", student.id, {
            "name": name,
            "center_id": str(center_id),
        })
        return student

    def update_student(
        self,
        student_id,
        updates: Dict[str, Any],
        current_user,
    ) -> Student:
        student = self._get_active_student(student_id)
        prev = {}
        for field in ("name", "academic_status", "sector", "area"):
            if field in updates:
                old = getattr(student, field)
                new = updates[field]
                if old != new:
                    prev[field] = {"anterior": str(old) if old is not None else None,
                                   "nuevo": str(new) if new is not None else None}
                    setattr(student, field, new)
        if not prev:
            return student
        self.session.flush()
        self._log(current_user, "UPDATE_STUDENT", "student", student.id, prev)
        return student

    def soft_delete_student(self, student_id, current_user) -> Student:
        student = self._get_active_student(student_id)
        if student.disabled_at is not None:
            return student
        student.disabled_at = datetime.date.today()
        self.session.flush()
        self._log(current_user, "DEACTIVATE_STUDENT", "student", student.id, {
            "disabled_at": student.disabled_at.isoformat(),
        })
        return student

    def assign_student_section(
        self, student_id, section_id, current_user,
    ) -> Student:
        student = self._get_active_student(student_id)
        section = self._get_active_section(section_id)
        if self._has_enrollment(student, section):
            raise ConflictError("El alumno ya pertenece a esa sección.")
        self.session.add(StudentSection(student_id=student.id, section_id=section.id))
        self.session.flush()
        self._log(current_user, "ASSIGN_STUDENT_SECTION", "student_section",
                  f"{student.id}/{section.id}", {"section_id": str(section_id)})
        return student

    def remove_student_section(
        self, student_id, section_id, current_user,
    ) -> Student:
        student = self._get_active_student(student_id)
        section = self._get_active_section(section_id)
        stmt = select(StudentSection).where(
            StudentSection.student_id == student.id,
            StudentSection.section_id == section.id,
        )
        enrollment = self.session.scalars(stmt).first()
        if enrollment is None:
            raise NotFoundError("El alumno no pertenece a esa sección.")
        self.session.delete(enrollment)
        self.session.flush()
        self._log(current_user, "REMOVE_STUDENT_SECTION", "student_section",
                  f"{student.id}/{section.id}", {"section_id": str(section_id)})
        return student

    def get_student_sections(self, student_id) -> List[Dict[str, Any]]:
        student = self._get_active_student(student_id)
        stmt = (
            select(StudentSection, Section, Center)
            .join(Section, StudentSection.section_id == Section.id)
            .join(Center, Section.center_id == Center.id)
            .where(StudentSection.student_id == student.id)
            .order_by(Section.name.asc())
        )
        results = []
        for enrollment, section, center in self.session.execute(stmt).all():
            results.append({
                "id": section.id,
                "name": section.name,
                "center_id": center.id,
                "center_name": center.name,
            })
        return results

    def student_to_dict(self, student: Student) -> Dict[str, Any]:
        sections = self.get_student_sections(student.id)
        return {
            "id": student.id,
            "external_id": student.external_id,
            "name": student.name,
            "origin": student.origin,
            "area": student.area,
            "academic_status": student.academic_status,
            "sector": student.sector,
            "disabled_at": student.disabled_at,
            "sections": sections,
        }

    # ----------------------------------------------------------------- centers
    def _get_unique_center_name(self, name: str) -> None:
        stmt = select(Center).where(
            Center.name == name,
            Center.disabled_at.is_(None),
        )
        if self.session.scalars(stmt).first() is not None:
            raise ConflictError("Ya existe un centro activo con ese nombre.")

    def create_center(self, name: str, current_user) -> Center:
        self._get_unique_center_name(name)
        center = Center(name=name, origin="manual")
        self.session.add(center)
        self.session.flush()
        self._log(current_user, "CREATE_CENTER_MANUAL", "center", center.id, {"name": name})
        return center

    def update_center(self, center_id, updates: Dict[str, Any], current_user) -> Center:
        center = self._get_active_center(center_id)
        if "name" in updates:
            old_name = center.name
            new_name = updates["name"]
            if old_name != new_name:
                self._get_unique_center_name(new_name)
                center.name = new_name
                self.session.flush()
                self._log(current_user, "UPDATE_CENTER", "center", center.id,
                          {"name": {"anterior": old_name, "nuevo": new_name}})
        return center

    def soft_delete_center(self, center_id, current_user) -> Center:
        center = self._get_active_center(center_id)
        center.disabled_at = datetime.date.today()
        self.session.flush()
        self._log(current_user, "DEACTIVATE_CENTER", "center", center.id, {
            "disabled_at": center.disabled_at.isoformat(),
        })
        return center

    # ---------------------------------------------------------------- sections
    def _get_unique_section_name(self, center_id, name: str) -> None:
        stmt = select(Section).where(
            Section.center_id == center_id,
            Section.name == name,
            Section.disabled_at.is_(None),
        )
        if self.session.scalars(stmt).first() is not None:
            raise ConflictError("Ya existe una sección activa con ese nombre en ese centro.")

    def create_section(
        self, name: str, center_id, academic_year: Optional[str], current_user,
    ) -> Section:
        if center_id is None:
            raise ValidationError("El centro es obligatorio para crear una sección.")
        center = self._get_active_center(center_id)
        self._get_unique_section_name(center.id, name)
        section = Section(center_id=center.id, name=name,
                          academic_year=academic_year, origin="manual")
        self.session.add(section)
        self.session.flush()
        self._log(current_user, "CREATE_SECTION_MANUAL", "section", section.id, {
            "name": name, "center_id": str(center_id),
        })
        return section

    def update_section(self, section_id, updates: Dict[str, Any], current_user) -> Section:
        section = self._get_active_section(section_id)
        prev = {}
        if "name" in updates and updates["name"] != section.name:
            self._get_unique_section_name(section.center_id, updates["name"])
            prev["name"] = {"anterior": section.name, "nuevo": updates["name"]}
            section.name = updates["name"]
        if "academic_year" in updates and updates["academic_year"] != section.academic_year:
            prev["academic_year"] = {"anterior": section.academic_year, "nuevo": updates["academic_year"]}
            section.academic_year = updates["academic_year"]
        if prev:
            self.session.flush()
            self._log(current_user, "UPDATE_SECTION", "section", section.id, prev)
        return section

    def soft_delete_section(self, section_id, current_user) -> Section:
        section = self._get_active_section(section_id)
        section.disabled_at = datetime.date.today()
        self.session.flush()
        self._log(current_user, "DEACTIVATE_SECTION", "section", section.id, {
            "disabled_at": section.disabled_at.isoformat(),
        })
        return section