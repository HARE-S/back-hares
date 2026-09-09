import datetime
from typing import List, Optional, Tuple, Union
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.test import Result, Test
from app.schemas.common import remove_accents




class TestRepository:
    """
    Repositorio para el catálogo de pruebas de lectura.
    Proporciona consultas con exclusión de pruebas deshabilitadas por defecto y borrado lógico.
    """
    __test__ = False

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        code: str,
        name: str,
        words: int = 0,
        level: Optional[str] = None,
        type: Optional[str] = None,
        disabled_at=None,
    ) -> Test:
        """Crea y persiste una nueva prueba de lectura."""
        new_test = Test(
            code=code,
            name=name,
            words=words,
            level=level,
            type=type,
            disabled_at=disabled_at,
        )
        self.session.add(new_test)
        self.session.commit()
        return new_test

    def upsert_by_code(
        self,
        code: str,
        name: str,
        words: int = 0,
        level: Optional[str] = None,
        type: Optional[str] = None,
        disabled_at=None,
        commit: bool = True,
    ) -> Tuple[Test, bool]:
        """
        Crea o actualiza una prueba identificada por su código funcional único.
        Si la prueba ya existe, actualiza name, words, level y type.
        Retorna una tupla (test, created) donde created es True si se creó una nueva fila
        o False si se actualizó una existente.
        """
        test = self.get_by_code(code)
        if test:
            test.name = name
            test.words = words
            test.level = level
            test.type = type
            if disabled_at is not None:
                test.disabled_at = disabled_at
            if commit:
                self.session.commit()
            else:
                self.session.flush()
            return test, False

        new_test = Test(
            code=code,
            name=name,
            words=words,
            level=level,
            type=type,
            disabled_at=disabled_at,
        )
        self.session.add(new_test)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return new_test, True



    def get_by_id(self, test_id) -> Optional[Test]:
        """Obtiene una prueba por su ID (UUID)."""
        return self.session.get(Test, test_id)

    def get_by_code(self, code: str) -> Optional[Test]:
        """Obtiene una prueba por su código funcional (ej: '0IF')."""
        stmt = select(Test).where(Test.code == code)
        return self.session.scalars(stmt).first()

    def get_by_id_or_code(self, identifier: Union[str, uuid.UUID]) -> Optional[Test]:
        """
        Busca una prueba de lectura por su UUID o por su código funcional.
        Si identifier es un UUID (o string convertible a UUID), busca primero por id;
        si no se encuentra o no es UUID válido, busca por su campo code.
        """
        if isinstance(identifier, uuid.UUID):
            return self.get_by_id(identifier)

        identifier_str = str(identifier).strip()
        try:
            parsed_uuid = uuid.UUID(identifier_str)
            test = self.get_by_id(parsed_uuid)
            if test:
                return test
        except (ValueError, AttributeError):
            pass

        return self.get_by_code(identifier_str)

    def exists_by_code(self, code: str) -> bool:
        """Comprueba si ya existe una prueba registrada con ese código."""
        return self.get_by_code(code) is not None

    def has_results(self, test_id: uuid.UUID) -> bool:
        """Comprueba si una prueba tiene resultados de alumnos asociados en la base de datos."""
        stmt = select(func.count(Result.id)).where(Result.test_id == test_id)
        count = self.session.scalar(stmt) or 0
        return count > 0

    def update(self, test: Test, commit: bool = True, **fields) -> Test:
        """Actualiza los campos indicados en la entidad Test y persiste los cambios."""
        for key, value in fields.items():
            if hasattr(test, key):
                setattr(test, key, value)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return test

    def get_all(self, include_disabled: bool = False) -> List[Test]:
        """
        Consulta pruebas de lectura.
        Por defecto (include_disabled=False) solo devuelve pruebas activas.
        Si include_disabled=True, incluye también las deshabilitadas.
        """
        stmt = select(Test)
        if not include_disabled:
            stmt = stmt.where(Test.disabled_at.is_(None))
        stmt = stmt.order_by(Test.code.asc())
        return list(self.session.scalars(stmt).all())

    def get_paginated(
        self,
        filter_text: Optional[str] = None,
        level: Optional[str] = None,
        type: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        include_disabled: bool = False,
    ) -> Tuple[List[Test], int]:
        """
        Consulta paginada y filtrada de pruebas de lectura (BE-14).
        - Filtros combinables: filter_text (búsqueda en code y name insensible a acentos),
          level y type.
        - Excluye por defecto las pruebas con disabled_at (baja lógica).
        - Devuelve una tupla (items, total).
        """
        stmt = select(Test)
        count_stmt = select(func.count(Test.id))

        conditions = []

        if not include_disabled:
            conditions.append(Test.disabled_at.is_(None))

        if level is not None and str(level).strip() != "":
            conditions.append(Test.level == str(level).strip())

        if type is not None and str(type).strip() != "":
            conditions.append(Test.type == str(type).strip().upper())

        if filter_text is not None and str(filter_text).strip() != "":
            clean_term = f"%{remove_accents(str(filter_text).strip()).lower()}%"
            # Normalización de acentos y minúsculas con translate
            name_normalized = func.translate(
                func.lower(Test.name),
                "áéíóúüñ",
                "aeiouun",
            )
            code_normalized = func.translate(
                func.lower(Test.code),
                "áéíóúüñ",
                "aeiouun",
            )
            conditions.append(
                or_(
                    name_normalized.like(clean_term),
                    code_normalized.like(clean_term),
                )
            )

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = self.session.scalar(count_stmt) or 0

        # Paginación y ordenación
        stmt = stmt.order_by(Test.code.asc())
        offset = max(0, (page - 1) * limit)
        stmt = stmt.offset(offset).limit(limit)

        items = list(self.session.scalars(stmt).all())
        return items, total

    def soft_delete(self, identifier: Union[str, uuid.UUID]) -> bool:
        """
        Da de baja lógica una prueba estableciendo disabled_at con la fecha actual.
        Acepta UUID o código funcional de la prueba.
        No elimina la fila de la base de datos para preservar el histórico de resultados.
        Devuelve True si se deshabilitó, False si la prueba no existe.
        """
        test = self.get_by_id_or_code(identifier)
        if not test:
            return False
        test.disabled_at = datetime.date.today()
        self.session.commit()
        return True



