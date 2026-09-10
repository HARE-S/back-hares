import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import ConflictError
from app.models.test import Result


class ResultRepository:
    """
    Repositorio para persistencia y consulta de resultados de pruebas (Bloque B).
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        student_id: uuid.UUID,
        section_id: uuid.UUID,
        test_id: uuid.UUID,
        test_date: datetime.date,
        time: int,
        successes: int,
        mistakes: int,
        commit: bool = True,
    ) -> Result:
        """
        Crea y persiste un nuevo resultado de prueba.
        Captura cualquier violación de unicidad a nivel de BD y lanza ConflictError (T-BE19-03).
        """
        result = Result(
            student_id=student_id,
            section_id=section_id,
            test_id=test_id,
            test_date=test_date,
            time=time,
            successes=successes,
            mistakes=mistakes,
        )
        try:
            self.session.add(result)
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_results_student_test_date" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe un resultado registrado para este alumno, prueba y fecha")
            raise
        return result

    def exists_duplicate(
        self,
        student_id: uuid.UUID,
        test_id: uuid.UUID,
        test_date: datetime.date,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Comprueba si ya existe un resultado para el mismo alumno, prueba y fecha exacta (Escenario 4 de BE-18 y Escenario 3 de BE-19).
        """
        stmt = select(Result).where(
            Result.student_id == student_id,
            Result.test_id == test_id,
            Result.test_date == test_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(Result.id != exclude_id)
        return self.session.scalars(stmt).first() is not None

    def get_by_id(self, result_id: uuid.UUID) -> Optional[Result]:
        """Obtiene un resultado por su identificador primario."""
        return self.session.get(Result, result_id)

    def get_by_student(self, student_id: uuid.UUID, order_asc: bool = True) -> List[Result]:
        """
        Obtiene todos los resultados asociados a un alumno con la información de la prueba unida (T-BE20-01).
        Por defecto ordenados cronológicamente por test_date ascendente (BE-19 Escenario 4 y T-BE19-04).
        """
        stmt = (
            select(Result)
            .where(Result.student_id == student_id)
            .options(joinedload(Result.test))
        )
        if order_asc:
            stmt = stmt.order_by(Result.test_date.asc(), Result.id.asc())
        else:
            stmt = stmt.order_by(Result.test_date.desc(), Result.id.desc())
        return list(self.session.scalars(stmt).all())

    def update(self, result: Result, commit: bool = True) -> Result:
        """
        Actualiza los cambios sobre un resultado persistido.
        Captura posibles colisiones de unicidad compuestas si se modificó la fecha o la prueba.
        """
        try:
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_results_student_test_date" in err_str or "unique constraint" in err_str:
                raise ConflictError("Ya existe un resultado registrado para este alumno, prueba y fecha")
            raise
        return result

    def delete(self, result: Result, commit: bool = True) -> None:
        """
        Elimina físicamente un resultado (BE-21 Escenario 3 y notas).
        """
        self.session.delete(result)
        if commit:
            self.session.commit()
        else:
            self.session.flush()

    def create_batch(self, items: List[Dict[str, Any]], commit: bool = True) -> List[Result]:
        """
        Crea e inserta en bloque múltiples resultados en una sola transacción (BE-22 Escenario 1 y 4).
        Si falla, realiza rollback completo para garantizar atomicidad sin resultados a medias.
        """
        created_results = []
        try:
            for item in items:
                res = Result(
                    student_id=item["student_id"],
                    section_id=item["section_id"],
                    test_id=item["test_id"],
                    test_date=item["test_date"],
                    time=item["time"],
                    successes=item["successes"],
                    mistakes=item["mistakes"],
                )
                self.session.add(res)
                created_results.append(res)
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            err_str = str(e).lower()
            if "uq_results_student_test_date" in err_str or "unique constraint" in err_str:
                raise ConflictError("Uno o más alumnos ya tienen un resultado registrado para esta prueba y fecha")
            raise
        except Exception:
            self.session.rollback()
            raise
        return created_results



