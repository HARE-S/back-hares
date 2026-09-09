import csv
import io
import uuid
from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from app.core.exceptions import (
    ConflictError,
    DuplicateCodeError,
    SchemaValidationError,
    ValidationError,
)
from app.models.book import Book
from app.models.test import Test
from app.repositories.book_repository import BookRepository
from app.repositories.test_repository import TestRepository
from app.schemas.book_schema import BookCreateSchema, BookUpdateSchema
from app.schemas.common import paginate_response
from app.schemas.test_schema import TestUpdateSchema


class CatalogService:
    """
    Servicio de lógica de negocio para los catálogos de pruebas y libros (Bloque B).
    Implementa reglas de unicidad, validación de palabras/niveles y deducción de nivel/tipo.
    """

    def __init__(self, session: Session):
        self.session = session
        self.test_repo = TestRepository(session)
        self.book_repo = BookRepository(session)


    @staticmethod
    def deduce_level_and_type_from_code(code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Deduce nivel y tipo a partir de la convención de códigos del centro (ej. '0IF', '1AL', '2BF'):
        - Primer carácter: Nivel (ej: '0', '1', '2', '3')
        - Último carácter: Tipo (ej: 'F' para ficción, 'L' para literatura)
        """
        level = None
        test_type = None
        if code and len(code) >= 2:
            if code[0].isdigit():
                level = code[0]
            if code[-1].upper() in ("F", "L"):
                test_type = code[-1].upper()
        return level, test_type

    def create_test(
        self,
        code: Optional[str],
        name: Optional[str],
        words: Optional[int],
        level: Optional[str] = None,
        type: Optional[str] = None,
    ) -> Test:
        """
        Crea una prueba en el catálogo aplicando las reglas de negocio de BE-11:
        1. Campos obligatorios: code y name (Escenario 4).
        2. Palabras válidas: entero estrictamente positivo > 0 (Escenario 3).
        3. Código único: rechaza duplicados con DuplicateCodeError -> 409 (Escenario 2).
        4. Opcionalmente level y type, o deducidos del código (Escenario 1).
        """
        # Validación de campos obligatorios (Escenario 4)
        if not code or not str(code).strip():
            raise ValidationError("El campo 'code' es obligatorio")
        if not name or not str(name).strip():
            raise ValidationError("El campo 'name' es obligatorio")

        code_str = str(code).strip()
        name_str = str(name).strip()

        # Validación de número de palabras (Escenario 3)
        if words is None:
            raise ValidationError("El campo 'words' es obligatorio")

        # Comprobación de que sea numérico y no booleano
        if isinstance(words, bool):
            raise ValidationError("El campo 'words' debe ser un número entero mayor que cero")

        try:
            words_int = int(words)
        except (ValueError, TypeError):
            raise ValidationError("El campo 'words' debe ser un número entero mayor que cero")

        if words_int <= 0:
            raise ValidationError("El campo 'words' debe ser mayor que cero")

        # Comprobación de unicidad de código (Escenario 2)
        if self.test_repo.exists_by_code(code_str):
            raise DuplicateCodeError(
                f"Ya existe una prueba registrada con el código '{code_str}'"
            )

        # Inferencia de nivel y tipo si no se han provisto explícitamente
        deduced_level, deduced_type = self.deduce_level_and_type_from_code(code_str)
        final_level = str(level).strip() if level is not None else deduced_level
        final_type = str(type).strip() if type is not None else deduced_type

        return self.test_repo.create(
            code=code_str,
            name=name_str,
            words=words_int,
            level=final_level,
            type=final_type,
        )

    @classmethod
    def parse_tests_csv(cls, content: str) -> List[Dict[str, Any]]:
        """
        Parsea el contenido de tests.csv aplicando las reglas y tolerancias de BE-12:
        - Separador ';' y codificación UTF-8.
        - Ignora la columna vacía final producida por ';' al terminar cada línea (Escenario 2).
        - Preserva comillas dobles y caracteres acentuados íntegros (Escenario 3).
        - Deriva automáticamente level y type a partir del código (Escenario 4).
        """
        if not content:
            return []

        # Limpiar posible marca BOM UTF-8
        if content.startswith("\ufeff"):
            content = content[1:]

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return []

        # Parsear cabecera (línea 1)
        header_line = lines[0]
        header_tokens = [tok.strip().lower() for tok in header_line.split(";")]
        while header_tokens and header_tokens[-1] == "":
            header_tokens.pop()

        expected = {"code", "name", "words"}
        if not expected.issubset(set(header_tokens)):
            raise ValidationError("El archivo CSV debe contener las columnas: code, name, words")

        code_idx = header_tokens.index("code")
        name_idx = header_tokens.index("name")
        words_idx = header_tokens.index("words")

        parsed_rows = []

        for line_num, line in enumerate(lines[1:], start=2):
            try:
                reader = csv.reader(io.StringIO(line), delimiter=";")
                tokens = next(reader)
            except Exception:
                tokens = line.split(";")

            # Eliminar columnas vacías excedentes al final (producidas por el ';' final - Escenario 2)
            while len(tokens) > len(header_tokens) and tokens[-1] == "":
                tokens.pop()

            if len(tokens) < len(header_tokens):
                raise ValidationError(
                    f"Línea {line_num}: Faltan columnas requeridas (esperadas {len(header_tokens)}, recibidas {len(tokens)})"
                )

            code = tokens[code_idx].strip()
            name = tokens[name_idx].strip()
            words_raw = tokens[words_idx].strip()

            if not code:
                raise ValidationError(f"Línea {line_num}: El campo 'code' no puede estar vacío")
            if not name:
                raise ValidationError(f"Línea {line_num}: El campo 'name' no puede estar vacío")

            try:
                words = int(words_raw)
                if words <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Línea {line_num}: El campo 'words' debe ser un número entero mayor que cero (recibido '{words_raw}')"
                )

            # Derivación de nivel y tipo (Escenario 4)
            level, test_type = cls.deduce_level_and_type_from_code(code)

            parsed_rows.append({
                "code": code,
                "name": name,
                "words": words,
                "level": level,
                "type": test_type,
            })

        return parsed_rows

    def import_tests_from_csv(
        self,
        file_source: Union[str, bytes, io.IOBase, Path],
    ) -> Dict[str, Any]:
        """
        Importa o actualiza el catálogo de pruebas desde un CSV (Escenarios 1 a 5 de BE-12).
        Es idempotente: crea pruebas nuevas y actualiza existentes por su código sin duplicarlas.
        """
        content = ""
        if isinstance(file_source, (str, Path)):
            path_obj = Path(file_source)
            if path_obj.is_file():
                with open(path_obj, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = str(file_source)
        elif isinstance(file_source, bytes):
            content = file_source.decode("utf-8")
        elif hasattr(file_source, "read"):
            raw = file_source.read()
            if isinstance(raw, bytes):
                content = raw.decode("utf-8")
            else:
                content = str(raw)
        else:
            raise ValidationError("Fuente de archivo no válida para importación CSV")

        parsed_data = self.parse_tests_csv(content)

        created_count = 0
        updated_count = 0
        tests_result = []

        for row in parsed_data:
            test, created = self.test_repo.upsert_by_code(
                code=row["code"],
                name=row["name"],
                words=row["words"],
                level=row["level"],
                type=row["type"],
                commit=False,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            tests_result.append(test)

        self.session.commit()

        return {
            "total": len(parsed_data),
            "created": created_count,
            "updated": updated_count,
            "tests": tests_result,
        }

    def update_test(
        self,
        identifier: Union[str, uuid.UUID],
        data: Dict[str, Any],
        is_patch: bool = False,
    ) -> Optional[Test]:
        """
        Actualiza una prueba por su ID o código (BE-13).
        - Si is_patch=False (PUT): reemplazo completo (requiere code, name, words).
        - Si is_patch=True (PATCH): modificación parcial (campos opcionales).
        - Valida datos con TestUpdateSchema (lanza SchemaValidationError -> 422 si hay datos inválidos).
        - Escenario 4: Si se intenta cambiar el código (new_code != current_code) y la prueba
          ya tiene resultados asociados, deniega con ConflictError -> 409 Conflict.
        - Si el nuevo código ya existe en otra prueba, deniega con DuplicateCodeError -> 409 Conflict.
        - Retorna la entidad Test actualizada o None si no existe la prueba.
        """
        test = self.test_repo.get_by_id_or_code(identifier)
        if not test:
            return None

        # Valida esquema de actualización (lanza SchemaValidationError si falla)
        cleaned = TestUpdateSchema.validate(data, is_patch=is_patch)

        # Regla de negocio: comprobar intento de cambio de código funcional
        if "code" in cleaned:
            new_code = cleaned["code"]
            if new_code != test.code:
                # 1. Comprobar si la prueba ya tiene resultados de alumnos (Escenario 4)
                if self.test_repo.has_results(test.id):
                    raise ConflictError(
                        f"No se puede modificar el código de la prueba '{test.code}' "
                        f"porque ya tiene resultados de alumnos asociados"
                    )

                # 2. Comprobar si otra prueba ya está usando el nuevo código
                if self.test_repo.exists_by_code(new_code):
                    raise DuplicateCodeError(
                        f"Ya existe otra prueba registrada con el código '{new_code}'"
                    )

        # En PUT (reemplazo completo), si no se especifican level ni type, se deducen del código
        if not is_patch:
            target_code = cleaned.get("code", test.code)
            deduced_lvl, deduced_tp = self.deduce_level_and_type_from_code(target_code)
            if "level" not in cleaned or cleaned["level"] is None:
                cleaned["level"] = deduced_lvl
            if "type" not in cleaned or cleaned["type"] is None:
                cleaned["type"] = deduced_tp

        # Actualizar campos en el repositorio
        updated_test = self.test_repo.update(test, commit=True, **cleaned)
        return updated_test

    def soft_delete_test(self, identifier: Union[str, uuid.UUID]) -> bool:
        """
        Da de baja lógica una prueba de lectura (Escenario 5 de BE-13 y BE-04).
        Preserva los resultados asociados en base de datos.
        """
        return self.test_repo.soft_delete(identifier)

    def list_tests(
        self,
        filter_text: Optional[str] = None,
        level: Optional[str] = None,
        type: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        include_disabled: bool = False,
    ) -> Dict[str, Any]:
        """
        Consulta paginada y filtrada de pruebas de lectura (BE-14).
        Retorna la respuesta paginada estructurada según el Contrato 4:
        {"items": [...], "total": int, "page": int, "limit": int, "pages": int}
        """
        items, total = self.test_repo.get_paginated(
            filter_text=filter_text,
            level=level,
            type=type,
            page=page,
            limit=limit,
            include_disabled=include_disabled,
        )
        return paginate_response(
            items=[t.to_dict() for t in items],
            total=total,
            page=page,
            limit=limit,
        )
    def create_book(self, data: Dict[str, Any]) -> Book:
        """
        Alta de libro en el catálogo (BE-16 Escenario 1 y 2).
        - Valida datos con BookCreateSchema (lanza SchemaValidationError -> 422 si falla).
        - Valida unicidad de título (lanza DuplicateCodeError -> 409 si ya existe).
        - Persiste el libro y retorna la entidad.
        """
        validated = BookCreateSchema.validate(data)
        title = validated["title"]

        if self.book_repo.exists_by_title(title):
            raise DuplicateCodeError(f"Ya existe un libro registrado con el título '{title}'")

        return self.book_repo.create(
            book=title,
            level=validated["level"],
            copies_note=validated.get("copies_note"),
            sessions_note=validated.get("sessions_note"),
        )

    def get_book(self, book_id: Union[str, uuid.UUID]) -> Optional[Book]:
        """Obtiene un libro por su ID o retorna None si no existe."""
        return self.book_repo.get_by_id(book_id)

    def list_books(
        self,
        level: Optional[str] = None,
        order_by_level: bool = False,
        include_disabled: bool = False,
    ) -> List[Book]:
        """Consulta libros con filtros por nivel, ordenación pedagógica y estado."""
        return self.book_repo.get_all(
            level=level,
            order_by_level=order_by_level,
            include_disabled=include_disabled,
        )

    def update_book(
        self,
        book_id: Union[str, uuid.UUID],
        data: Dict[str, Any],
        is_patch: bool = False,
    ) -> Optional[Book]:
        """
        Actualiza un libro existente (BE-16 Escenario 3).
        - Si is_patch=False (PUT): reemplazo completo (requiere title y level).
        - Si is_patch=True (PATCH): modificación parcial.
        - Valida datos con BookUpdateSchema (lanza SchemaValidationError -> 422 si falla).
        - Si se modifica el título y coincide con otro libro existente, lanza DuplicateCodeError -> 409.
        """
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None

        cleaned = BookUpdateSchema.validate(data, is_patch=is_patch)

        if "title" in cleaned:
            new_title = cleaned["title"]
            if new_title.lower() != book.book.lower():
                if self.book_repo.exists_by_title(new_title, exclude_id=book.id):
                    raise DuplicateCodeError(
                        f"Ya existe otro libro registrado con el título '{new_title}'"
                    )

        updated_book = self.book_repo.update(book, commit=True, **cleaned)
        return updated_book

    def soft_delete_book(self, book_id: Union[str, uuid.UUID]) -> bool:
        """
        Baja lógica de un libro (BE-16 Escenario 4).
        Establece disabled_at y preserva lecturas asociadas.
        """
        return self.book_repo.soft_delete(book_id)

