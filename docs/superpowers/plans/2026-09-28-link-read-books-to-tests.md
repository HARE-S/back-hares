# Plan de Implementación: Vinculación de Lecturas a Pruebas (read_books -> tests)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar la tabla `read_books` directamente a `tests` mediante la clave foránea `test_id`, unificando el catálogo oficial de libros evaluables y asegurando que las lecturas y pruebas apunten al mismo registro canónico.

**Architecture:** Modificar el esquema de base de datos en PostgreSQL y el modelo SQLAlchemy `ReadBook` para reemplazar el título en texto libre por `test_id` apuntando a `tests(id)` con eliminación en cascada. Actualizar repositorios, servicios, esquemas y endpoints para que la asignación, consulta y cierre de lecturas utilicen `test_id`, manteniendo propiedades computadas de compatibilidad (`title`, `book_title`) para el frontend.

**Tech Stack:** Python 3.14, Flask, SQLAlchemy, Alembic, PostgreSQL 18, Marshmallow, Pytest, Docker.

**Spec:** `docs/superpowers/specs/2026-09-28-link-read-books-to-tests-design.md`

## Global Constraints
- Clave foránea `read_books.test_id` obligatoria hacia `tests.id` con `ON DELETE CASCADE`.
- Restricción de unicidad: `uq_read_books_student_test_start UNIQUE (student_id, test_id, start_date)`.
- Compatibilidad hacia atrás: la API y `to_dict()` deben seguir exponiendo `title` y `book_title` derivados de `test.name`.
- Los tests deben ejecutarse dentro del contenedor Docker `hares_backend` contra `TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test`.

---

### Task 1: Migración de Base de Datos y Esquema en PostgreSQL

**Files:**
- Create: `migrations/versions/d4e5f6a7b8c9_link_read_books_to_tests.py`
- Modify: `app/models/book.py`

**Interfaces:**
- Consumes: `tests(id)`
- Produces: `read_books.test_id`, constraint `uq_read_books_student_test_start`

- [x] **Step 1: Crear archivo de migración de Alembic**
  Crear `migrations/versions/d4e5f6a7b8c9_link_read_books_to_tests.py`:
  - `op.drop_constraint('uq_read_books_student_title_start', 'read_books', type_='unique')`
  - `op.drop_column('read_books', 'book_title')`
  - `op.drop_column('read_books', 'level')`
  - `op.add_column('read_books', sa.Column('test_id', sa.Uuid(), nullable=False))`
  - `op.create_foreign_key('read_books_test_id_fkey', 'read_books', 'tests', ['test_id'], ['id'], ondelete='CASCADE')`
  - `op.create_unique_constraint('uq_read_books_student_test_start', 'read_books', ['student_id', 'test_id', 'start_date'])`
  - `op.create_index('ix_read_books_test_id', 'read_books', ['test_id'])`

- [x] **Step 2: Ejecutar migración en PostgreSQL `hares_db` y `hares_test`**
  Ejecutar comandos SQL en `hares_database` para actualizar las bases de datos de desarrollo y test.

- [x] **Step 3: Verificar estructura de tabla con `psql`**
  Ejecutar `\d read_books` en `hares_database` y verificar las nuevas columnas y constraints.

- [x] **Step 4: Commit**
  `git add migrations/`
  `git commit -m "feat(db): link read_books to tests via test_id foreign key"`

---

### Task 2: Actualización de Modelos SQLAlchemy (`ReadBook` y `Test`)

**Files:**
- Modify: `app/models/book.py`
- Modify: `app/models/test.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `Test.id`, `Test.name`, `Test.code`
- Produces: `ReadBook.test_id`, `ReadBook.test`, `ReadBook.title`, `ReadBook.book_title`, `Test.read_books`

- [x] **Step 1: Escribir test en `tests/test_models.py`**
  Verificar que `ReadBook` requiere `test_id`, expone relación con `Test`, y calcula `title` y `book_title` a partir de `test.name`.

- [x] **Step 2: Actualizar `ReadBook` en `app/models/book.py`**
  - Añadir columna `test_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)`
  - Definir relación `test = db.relationship('Test', back_populates='read_books', lazy='joined')`
  - Añadir propiedades:
    - `@property def title(self): return self.test.name if self.test else ""`
    - `@property def book_title(self): return self.title`
    - `@property def book(self): return self.title`
    - `@property def level(self): return self.test.test_letter or str(self.test.course or "")`
  - Actualizar `to_dict()` para incluir `test_id`, `test_code`, `title`, `book_title`.

- [x] **Step 3: Actualizar `Test` en `app/models/test.py`**
  - Añadir `read_books = db.relationship('ReadBook', back_populates='test', cascade='all, delete-orphan', lazy='select')`

- [x] **Step 4: Ejecutar tests de modelos en Docker**
  `docker cp app hares_backend:/app/ && docker cp tests hares_backend:/app/`
  `docker exec -e TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test hares_backend pytest tests/test_models.py`

- [x] **Step 5: Commit**
  `git add app/models/ tests/test_models.py`
  `git commit -m "feat(models): update ReadBook model with test_id relationship and properties"`

---

### Task 3: Capa de Repositorio y Servicio (`ReadingRepository` y `ReadingService`)

**Files:**
- Modify: `app/repositories/reading_repository.py`
- Modify: `app/services/reading_service.py`
- Modify: `app/schemas/reading_schema.py`

**Interfaces:**
- Consumes: `student_id: UUID`, `test_id: UUID`, `start_date: date`
- Produces: `ReadingService.assign_book`, `ReadingService.get_student_readings`, `ReadingService.get_test_students`

- [x] **Step 1: Actualizar `ReadingRepository`**
  - `create(student_id, test_id, start_date, end_date=None, copies_note=None, sessions_note=None)`
  - `exists_duplicate(student_id, test_id, start_date)`
  - `get_by_student(student_id, status=None)`
  - `get_by_test(test_id, status=None)`

- [x] **Step 2: Actualizar `ReadingSchema` y `ReadingCreateSchema`**
  - `ReadingCreateSchema`: acepta `test_id` (UUID obligatorio) o `test_code` (resolución al test correspondiente).
  - `ReadingSchema`: serializa `id`, `student_id`, `test_id`, `test_code`, `title`, `book_title`, `status`, `start_date`, `end_date`, `copies_note`, `sessions_note`.

- [x] **Step 3: Actualizar `ReadingService`**
  - En `assign_book`: validar que el `test_id` exista y no esté dado de baja (`disabled_at is None`).
  - En `get_test_students(test_id, status)`: listar alumnos que leyeron la prueba indicada.
  - En `close_or_update_reading`: validar fecha fin y actualizar.

- [x] **Step 4: Commit**
  `git add app/repositories/ app/services/ app/schemas/`
  `git commit -m "feat(services): adapt ReadingRepository and ReadingService to test_id"`

---

### Task 4: Endpoints y Controladores (`app/api/v1/readings.py`)

**Files:**
- Modify: `app/api/v1/readings.py`
- Modify: `app/services/student_service.py`

**Interfaces:**
- Consumes: HTTP POST / GET / PATCH sobre `/api/v1/students/<id>/books` y `/api/v1/readings`
- Produces: JSON payloads con lecturas vinculadas al test

- [x] **Step 1: Actualizar rutas en `app/api/v1/readings.py`**
  - `POST /api/v1/students/<student_id>/books`: recibe `test_id` (o `test_code`), asigna y devuelve 201 Created.
  - `GET /api/v1/students/<student_id>/books`: devuelve lista de lecturas con datos de prueba.
  - `GET /api/v1/readings/test/<test_id>/students`: devuelve los alumnos que leyeron esa prueba.
  - Alias canónicos en `/api/readings` y `/api/v1/readings`.

- [x] **Step 2: Verificar respuesta agregada en `StudentService`**
  - `get_student_card`: verificar que las lecturas en la ficha del alumno incluyan `test_id`, `title` y `status`.

- [x] **Step 3: Commit**
  `git add app/api/v1/readings.py app/services/student_service.py`
  `git commit -m "feat(api): update reading endpoints to support test_id"`

---

### Task 5: Actualización de Tests y Verificación de Regresión

**Files:**
- Modify: `tests/test_be23_asignar_libro.py`
- Modify: `tests/test_be24_cerrar_lectura.py`
- Modify: `tests/test_be25_relectura.py`
- Modify: `tests/test_be26_lecturas_por_alumno_y_libro.py`
- Modify: `tests/test_be28_ficha_alumno_agregada.py`
- Modify: `tests/test_be36_informe_individual_alumno.py`

- [x] **Step 1: Adaptar fixtures de tests a `test_id`**
  - En cada test de lecturas, crear o tomar una instancia de `Test` existente (ej. "Normativa piscinas" o `test1`) y pasar `test_id=test1.id`.

- [x] **Step 2: Ejecutar los tests de lecturas en Docker**
  `docker exec -e TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test hares_backend pytest tests/test_be23_asignar_libro.py tests/test_be24_cerrar_lectura.py tests/test_be25_relectura.py tests/test_be26_lecturas_por_alumno_y_libro.py`

- [x] **Step 3: Ejecutar la suite completa de pruebas**
  `docker exec -e TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test hares_backend pytest`

- [x] **Step 4: Reiniciar backend y comprobar `/api/health`**
  `docker restart hares_backend && curl -s http://localhost:5000/api/health`

- [x] **Step 5: Commit final**
  `git add tests/`
  `git commit -m "test: update reading test suites with test_id relationships"`
