"""Repository for students, centers and sections (Bloque A).

Provides idempotent access to the student data model: creation and
upserts resolved by `external_id` (BE-05 / BE-07), get-or-create
helpers for centers and sections, and enrollment management.
"""
import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.center import Center, Section
from app.models.student import Student, StudentSection

# Valor reservado para filtrar alumnos cuyo campo no está informado (BE-27).
MISSING_VALUE = "__missing__"


def _shift_years(value: datetime.date, years: int) -> datetime.date:
    """Shifts a date by a whole number of years (Feb 29 rolls to Feb 28)."""
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def birth_date_upper_bound(age: int, today: datetime.date) -> datetime.date:
    """Latest birth_date that still yields an age >= ``age`` on ``today``."""
    return _shift_years(today, age)


def birth_date_lower_bound(age: int, today: datetime.date) -> datetime.date:
    """Earliest birth_date that still yields an age <= ``age`` on ``today``."""
    return _shift_years(today, age + 1) + datetime.timedelta(days=1)


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

    def get_all_active_centers(self) -> List[Center]:
        """Returns all non-disabled centers ordered by name (BE-10)."""
        stmt = (
            select(Center)
            .where(Center.disabled_at.is_(None))
            .order_by(Center.name.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_active_center(self, center_id) -> Optional[Center]:
        """Returns a center by id, excluding disabled ones (BE-10)."""
        stmt = select(Center).where(
            Center.id == center_id,
            Center.disabled_at.is_(None),
        )
        return self.session.scalars(stmt).first()

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

    def get_sections_by_center(self, center_id) -> List[Section]:
        """Returns the non-disabled sections of a center ordered by name (BE-10)."""
        stmt = (
            select(Section)
            .where(
                Section.center_id == center_id,
                Section.disabled_at.is_(None),
            )
            .order_by(Section.name.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_active_section(self, section_id) -> Optional[Section]:
        """Returns a section by id, excluding disabled ones (BE-10)."""
        stmt = select(Section).where(
            Section.id == section_id,
            Section.disabled_at.is_(None),
        )
        return self.session.scalars(stmt).first()

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

    def get_students_by_section(self, section_id) -> List[Student]:
        """Returns the non-disabled students enrolled in a section (BE-10)."""
        stmt = (
            select(Student)
            .join(StudentSection, StudentSection.student_id == Student.id)
            .where(
                StudentSection.section_id == section_id,
                Student.disabled_at.is_(None),
            )
            .order_by(Student.name.asc(), Student.external_id.asc())
        )
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

    # ------------------------------------------------------------------ filtering (BE-27)

    @staticmethod
    def _student_filter_query(filters: Dict[str, Any]) -> select:
        """
        Builds a SELECT of distinct, active students applying combinable
        multi-criteria filters (T-BE27-02/03/04/05).

        Returns the statement without ORDER or LIMIT so callers can reuse it
        for both the count query and the final paged fetch.
        """
        stmt = (
            select(Student)
            .join(Student.student_sections)
            .join(StudentSection.section)
            .where(Student.disabled_at.is_(None))
            .distinct()
        )

        center_id = filters.get("center_id")
        if center_id is not None:
            stmt = stmt.where(Section.center_id == center_id)

        section_ids = filters.get("section_ids")
        if section_ids:
            stmt = stmt.where(StudentSection.section_id.in_(section_ids))

        for field in ("gender", "academic_status", "sector"):
            value = filters.get(field)
            if value == MISSING_VALUE:
                stmt = stmt.where(getattr(Student, field).is_(None))
            elif value is not None:
                stmt = stmt.where(getattr(Student, field) == value)

        today = datetime.date.today()

        min_age = filters.get("min_age")
        if min_age is not None:
            stmt = stmt.where(
                Student.birth_date <= birth_date_upper_bound(min_age, today)
            )

        max_age = filters.get("max_age")
        if max_age is not None:
            stmt = stmt.where(
                Student.birth_date >= birth_date_lower_bound(max_age, today)
            )

        return stmt

    def filter_students(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Student], int]:
        """
        Returns a page of active students matching all supplied filters and the
        total count of students matching those filters (without pagination).

        The ``section_ids`` key in filters can represent an explicit section
        filter **or** the scope enforced by the user's role.
        """
        base = self._student_filter_query(filters or {})
        sub = base.subquery()
        total = int(self.session.scalar(select(func.count()).select_from(sub)) or 0)

        stmt = base.order_by(Student.name.asc(), Student.external_id.asc())
        stmt = stmt.offset((page - 1) * limit).limit(limit)
        return list(self.session.scalars(stmt).all()), total

    def count_students_missing_field(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Counts active students where ``field IS NULL`` within the scope defined
        by ``filters`` **excluding** the equality constraint on ``field``
        itself (BE-27, Escenario 5 — "sin datos").

        Returns the number so the API response can indicate that those students
        were not silently omitted from the result.
        """
        base_filters = dict(filters or {})
        base_filters.pop(field, None)
        base = self._student_filter_query(base_filters)
        stmt = base.where(getattr(Student, field).is_(None))
        sub = stmt.subquery()
        return int(self.session.scalar(select(func.count()).select_from(sub)) or 0)