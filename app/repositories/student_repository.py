"""Repository for students, centers and sections (Bloque A).

Provides idempotent access to the student data model: creation and
upserts resolved by `external_id` (BE-05 / BE-07), get-or-create
helpers for centers and sections, and enrollment management.
"""
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.center import Center, Section
from app.models.student import Student, StudentSection


class StudentRepository:
    """Data access for the enrollment model (centers, sections, students)."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------ centers
    def get_center_by_name(self, name: str) -> Optional[Center]:
        """Returns the center with the given name or None if not found."""
        stmt = select(Center).where(Center.name == name)
        return self.session.scalars(stmt).first()

    def create_center(self, name: str) -> Center:
        """Creates and persists a new center."""
        center = Center(name=name)
        self.session.add(center)
        self.session.flush()
        return center

    def get_or_create_center(self, name: str) -> Tuple[Center, bool]:
        """Returns the existing center or creates it (idempotent).

        The boolean indicates whether the center was newly created.
        """
        center = self.get_center_by_name(name)
        if center is None:
            return self.create_center(name), True
        return center, False

    # ---------------------------------------------------------------- sections
    def get_section_by_name(self, center: Center, name: str) -> Optional[Section]:
        """Returns a section by name within the given center."""
        stmt = select(Section).where(
            Section.center_id == center.id,
            Section.name == name,
        )
        return self.session.scalars(stmt).first()

    def create_section(self, center: Center, name: str) -> Section:
        """Creates and persists a new section belonging to a center."""
        section = Section(center_id=center.id, name=name)
        self.session.add(section)
        self.session.flush()
        return section

    def get_or_create_section(self, center: Center, name: str) -> Tuple[Section, bool]:
        """Returns the existing section or creates it (idempotent).

        The boolean indicates whether the section was newly created.
        """
        section = self.get_section_by_name(center, name)
        if section is None:
            return self.create_section(center, name), True
        return section, False

    # ---------------------------------------------------------------- students
    def get_student_by_external_id(self, external_id: str) -> Optional[Student]:
        """Returns the student by its source identifier (external_id)."""
        stmt = select(Student).where(Student.external_id == external_id)
        return self.session.scalars(stmt).first()

    def create_student(self, external_id: str, name: str) -> Student:
        """Creates and persists a new student."""
        student = Student(external_id=external_id, name=name)
        self.session.add(student)
        self.session.flush()
        return student

    def upsert_student(self, external_id: str, name: str) -> Tuple[Student, bool, bool]:
        """
        Creates or updates a student resolved by external_id (BE-07).

        Returns a tuple (student, created, changed):
        - created is True when a new row was inserted.
        - changed is True when an existing student had its name updated;
          False when the student already existed with the same name (omitted).
        """
        student = self.get_student_by_external_id(external_id)
        if student is None:
            return self.create_student(external_id, name), True, False

        if student.name != name:
            student.name = name
            self.session.flush()
            return student, False, True
        return student, False, False

    def get_all_students(self) -> List[Student]:
        """Returns all students ordered by their external identifier."""
        stmt = select(Student).order_by(Student.external_id.asc())
        return list(self.session.scalars(stmt).all())

    def count_students(self) -> int:
        """Returns the total number of students."""
        return int(self.session.scalar(select(func.count(Student.id))) or 0)

    def count_centers(self) -> int:
        """Returns the total number of centers."""
        return int(self.session.scalar(select(func.count(Center.id))) or 0)

    def count_sections(self) -> int:
        """Returns the total number of sections."""
        return int(self.session.scalar(select(func.count(Section.id))) or 0)

    # -------------------------------------------------------------- enrollments
    def has_enrollment(self, student: Student, section: Section) -> bool:
        """Checks whether a student is already enrolled in a section."""
        stmt = select(StudentSection).where(
            StudentSection.student_id == student.id,
            StudentSection.section_id == section.id,
        )
        return self.session.scalars(stmt).first() is not None

    def add_enrollment(self, student: Student, section: Section) -> Optional[StudentSection]:
        """
        Enrolls a student in a section without creating duplicates.

        Returns the StudentSection row or None when it already existed.
        """
        if self.has_enrollment(student, section):
            return None
        enrollment = StudentSection(student_id=student.id, section_id=section.id)
        self.session.add(enrollment)
        self.session.flush()
        return enrollment

    def count_enrollments(self) -> int:
        """Returns the total number of student-section enrollments."""
        return int(self.session.scalar(select(func.count(StudentSection.student_id))) or 0)