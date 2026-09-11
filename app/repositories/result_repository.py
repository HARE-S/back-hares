"""Repository de resultados (mínimo para BE-05).

Proporciona el acceso a datos necesario para la generación idempotente de
resultados sintéticos: comprobación de existencia por (student, test, date)
y alta de nuevos resultados.
"""
import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.test import Result


class ResultRepository:
    """Data access for reading and creating test results."""

    def __init__(self, session: Session):
        self.session = session

    def exists(
        self,
        student_id,
        test_id,
        test_date: datetime.date,
    ) -> bool:
        """Checks whether a result already exists for the triplicate key."""
        stmt = select(Result).where(
            Result.student_id == student_id,
            Result.test_id == test_id,
            Result.test_date == test_date,
        )
        return self.session.scalars(stmt).first() is not None

    def create(
        self,
        student_id,
        section_id,
        test_id,
        test_date: datetime.date,
        time: int,
        successes: int,
        mistakes: int,
        commit: bool = False,
    ) -> Result:
        """Creates a new result (flushes unless commit=True)."""
        result = Result(
            student_id=student_id,
            section_id=section_id,
            test_id=test_id,
            test_date=test_date,
            time=time,
            successes=successes,
            mistakes=mistakes,
        )
        self.session.add(result)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return result

    def count(self) -> int:
        """Returns the total number of results."""
        return int(self.session.scalar(select(func.count(Result.id))) or 0)

    def get_by_student(self, student_id) -> List[Result]:
        """Returns all results of a student ordered by test date."""
        stmt = (
            select(Result)
            .where(Result.student_id == student_id)
            .order_by(Result.test_date.asc())
        )
        return list(self.session.scalars(stmt).all())