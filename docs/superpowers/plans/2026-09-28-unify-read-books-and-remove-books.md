# Unify Read Books and Remove Books Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the standalone `books` catalog table, model, endpoints, and triggers, and unify reading records and book attributes directly into a single `read_books` table and `ReadBook` model.

**Architecture:** Refactor PostgreSQL database schema and SQLAlchemy models so that `read_books` is self-contained with columns (`book_title`, `level`, `copies_note`, `sessions_note`, `start_date`, `end_date`) and a foreign key only to `students`. Remove the separate `Book` model, `books` database table, `books_bp` blueprint, and `sync_book_to_test` trigger. Update repositories, services, schemas, and test suites accordingly.

**Tech Stack:** Python 3.14, Flask, Flask-Smorest, SQLAlchemy 2.0, PostgreSQL 18, Alembic, Marshmallow, Pytest.

**Spec:** Architectural design approved in conversation: unified `read_books` storing book metadata directly with student reading history; total removal of `books`.

## Global Constraints

- Database engine dialect: PostgreSQL (with `uuidv7()` default PKs).
- Preserve student relationship: `Student.read_books` cascade delete.
- Level validation values: `'0'`, `'0-I'`, `'I'`, `'I/II'`, `'II'`.
- Unique constraint: `(student_id, book_title, start_date)` on `read_books`.
- Maintain endpoint compatibility on `/api/v1/students/<id>/books` and `/api/v1/readings`.

---

### Task 1: Database Migration & PostgreSQL Schema Unification

**Files:**
- Create: `migrations/versions/c3d4e5f6a7b8_unify_read_books_and_drop_books.py`
- Modify Database: `hares_db` and `hares_test` in `hares_database`

**Interfaces:**
- Consumes: Existing PostgreSQL tables `books` and `read_books`.
- Produces: Updated `read_books` table with `book_title`, `level`, `copies_note`, `sessions_note`; dropped `books` table and trigger.

- [ ] **Step 1: Write the Alembic migration file**

Create `migrations/versions/c3d4e5f6a7b8_unify_read_books_and_drop_books.py`:
```python
"""unify read_books and drop books

Revision ID: c3d4e5f6a7b8
Revises: 2e988e9f4a06
Create Date: 2026-09-28 00:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = '2e988e9f4a06'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop trigger and function if exists
    op.execute("DROP TRIGGER IF EXISTS trg_sync_book_to_test ON books;")
    op.execute("DROP FUNCTION IF EXISTS sync_book_to_test();")

    # 2. Modify read_books
    op.drop_constraint('read_books_book_id_fkey', 'read_books', type_='foreignkey')
    op.drop_constraint('uq_read_books_student_book_start', 'read_books', type_='unique')
    op.drop_column('read_books', 'book_id')

    op.add_column('read_books', sa.Column('book_title', sa.String(length=255), nullable=False, server_default=''))
    op.alter_column('read_books', 'book_title', server_default=None)
    op.add_column('read_books', sa.Column('level', sa.String(length=20), nullable=False, server_default='0'))
    op.add_column('read_books', sa.Column('copies_note', sa.String(length=255), nullable=True))
    op.add_column('read_books', sa.Column('sessions_note', sa.String(length=255), nullable=True))

    op.create_unique_constraint('uq_read_books_student_title_start', 'read_books', ['student_id', 'book_title', 'start_date'])

    # 3. Drop books table
    op.drop_table('books')


def downgrade():
    op.create_table(
        'books',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('book', sa.String(length=255), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False, server_default='0'),
        sa.Column('copies_note', sa.String(length=255), nullable=True),
        sa.Column('sessions_note', sa.String(length=255), nullable=True),
        sa.Column('disabled_at', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='books_pkey')
    )
    op.add_column('read_books', sa.Column('book_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('read_books_book_id_fkey', 'read_books', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('uq_read_books_student_title_start', 'read_books', type_='unique')
    op.drop_column('read_books', 'sessions_note')
    op.drop_column('read_books', 'copies_note')
    op.drop_column('read_books', 'level')
    op.drop_column('read_books', 'book_title')
    op.create_unique_constraint('uq_read_books_student_book_start', 'read_books', ['student_id', 'book_id', 'start_date'])
```

- [ ] **Step 2: Apply migration to PostgreSQL databases (`hares_db` and `hares_test`)**

Execute migration and verify `books` is dropped and `read_books` has the new columns:
```bash
docker exec hares_database psql -U hares_user -d hares_db -c "DROP TRIGGER IF EXISTS trg_sync_book_to_test ON books; DROP FUNCTION IF EXISTS sync_book_to_test();"
docker exec hares_database psql -U hares_user -d hares_db -c "ALTER TABLE read_books DROP CONSTRAINT IF EXISTS read_books_book_id_fkey; ALTER TABLE read_books DROP CONSTRAINT IF EXISTS uq_read_books_student_book_start; ALTER TABLE read_books DROP COLUMN IF EXISTS book_id; ALTER TABLE read_books ADD COLUMN IF NOT EXISTS book_title VARCHAR(255) NOT NULL DEFAULT ''; ALTER TABLE read_books ADD COLUMN IF NOT EXISTS level VARCHAR(20) NOT NULL DEFAULT '0'; ALTER TABLE read_books ADD COLUMN IF NOT EXISTS copies_note VARCHAR(255); ALTER TABLE read_books ADD COLUMN IF NOT EXISTS sessions_note VARCHAR(255); ALTER TABLE read_books ADD CONSTRAINT uq_read_books_student_title_start UNIQUE (student_id, book_title, start_date); DROP TABLE IF EXISTS books CASCADE;"
```

- [ ] **Step 3: Verify PostgreSQL table status**

Verify with:
```bash
docker exec hares_database psql -U hares_user -d hares_db -c "\d read_books"
docker exec hares_database psql -U hares_user -d hares_db -c "\dt books"
```
Expected: `books` did not match any relations; `read_books` shows `book_title`, `level`, `copies_note`, `sessions_note`, and `uq_read_books_student_title_start`.

- [ ] **Step 4: Commit migration**

```bash
git add migrations/versions/c3d4e5f6a7b8_unify_read_books_and_drop_books.py
git commit -m "feat(db): unify read_books and drop books table"
```

---

### Task 2: Model Refactoring: Update `ReadBook` & Remove `Book`

**Files:**
- Modify: `app/models/book.py`
- Modify: `app/models/__init__.py`
- Modify: `app/models/student.py`

**Interfaces:**
- Produces: `ReadBook` with properties `title`, `book`, `level`, `level_order`, `validate_level`. Removes `Book`.

- [ ] **Step 1: Update `app/models/book.py` to contain only `ReadBook`**

Replace `Book` model and update `ReadBook`:
```python
from sqlalchemy import orm, text, UniqueConstraint
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import BOOK_LEVEL_ORDER, validate_book_level
from app.utils.uuidv7 import uuidv7


class ReadBook(BaseModel):
    __tablename__ = "read_books"

    id = db.Column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuidv7,
        server_default=text("uuidv7()"),
    )
    student_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    book_title = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="0")
    copies_note = db.Column(db.String(255), nullable=True)
    sessions_note = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "book_title", "start_date",
            name="uq_read_books_student_title_start"
        ),
        db.Index("ix_read_books_student_id", "student_id"),
    )

    # Relaciones
    student = db.relationship("Student", back_populates="read_books")

    @property
    def title(self) -> str:
        return self.book_title

    @title.setter
    def title(self, value: str):
        self.book_title = value

    @property
    def book(self) -> str:
        return self.book_title

    @book.setter
    def book(self, value: str):
        self.book_title = value

    @orm.validates("level")
    def validate_level(self, key, value):
        return validate_book_level(value)

    @property
    def level_order(self) -> int:
        return BOOK_LEVEL_ORDER.get(self.level, 99)

    def to_dict(self):
        data = super().to_dict()
        data["title"] = self.book_title
        data["book"] = self.book_title
        data["book_title"] = self.book_title
        return data

    def __repr__(self):
        return (
            f"<ReadBook id={self.id} student_id={self.student_id} "
            f"title='{self.book_title}' level='{self.level}' start={self.start_date}>"
        )


# Alias para retrocompatibilidad
ReadedBook = ReadBook
```

- [ ] **Step 2: Update `app/models/__init__.py`**

Remove `Book` export, keep `ReadBook` and `ReadedBook`:
```python
from app.models.book import ReadBook, ReadedBook
```
Update `__all__`: remove `"Book"`.

- [ ] **Step 3: Update `app/models/student.py`**

Ensure `Student.read_books` relationship works cleanly with `ReadBook`.

- [ ] **Step 4: Commit model changes**

```bash
git add app/models/book.py app/models/__init__.py app/models/student.py
git commit -m "refactor(models): update ReadBook to store book details directly and remove Book model"
```

---

### Task 3: Repositories and Services Refactoring

**Files:**
- Modify: `app/repositories/reading_repository.py`
- Modify: `app/services/reading_service.py`
- Modify: `app/services/catalog_service.py`
- Modify: `app/services/seed_service.py`
- Delete: `app/repositories/book_repository.py`

**Interfaces:**
- `ReadingRepository.create(student_id, book_title, level, start_date, end_date=None, copies_note=None, sessions_note=None)`
- `ReadingRepository.exists_duplicate(student_id, book_title, start_date, exclude_id=None)`
- `ReadingService.assign_book(student_id, data, current_user)`: accepts `book_title` (or `title` / `book`), `level`, `start_date`, `end_date`, `copies_note`, `sessions_note`.

- [ ] **Step 1: Update `app/repositories/reading_repository.py`**

Adjust `create()`:
```python
def create(
    self,
    student_id: uuid.UUID,
    book_title: str,
    level: str = "0",
    start_date: datetime.date = None,
    end_date: Optional[datetime.date] = None,
    copies_note: Optional[str] = None,
    sessions_note: Optional[str] = None,
    commit: bool = True,
) -> ReadBook:
    reading = ReadBook(
        student_id=student_id,
        book_title=str(book_title).strip(),
        level=level,
        start_date=start_date,
        end_date=end_date,
        copies_note=copies_note,
        sessions_note=sessions_note,
    )
    try:
        self.session.add(reading)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
    except IntegrityError as e:
        self.session.rollback()
        err_str = str(e).lower()
        if "uq_read_books_student_title_start" in err_str or "unique constraint" in err_str:
            raise ConflictError("Ya existe una lectura registrada para este alumno, libro y fecha de inicio")
        raise
    return reading
```

Adjust `exists_duplicate()`:
```python
def exists_duplicate(
    self,
    student_id: uuid.UUID,
    book_title: str,
    start_date: datetime.date,
    exclude_id: Optional[uuid.UUID] = None,
) -> bool:
    stmt = select(ReadBook).where(
        ReadBook.student_id == student_id,
        func.lower(ReadBook.book_title) == str(book_title).strip().lower(),
        ReadBook.start_date == start_date,
    )
    if exclude_id is not None:
        stmt = stmt.where(ReadBook.id != exclude_id)
    return self.session.scalars(stmt).first() is not None
```

In `get_by_id()`: remove `joinedload(ReadBook.book)` (only join `ReadBook.student`).

- [ ] **Step 2: Update `app/services/reading_service.py`**

In `assign_book`:
Extract `book_title` from `data.get("book_title") or data.get("title") or data.get("book")`.
Validate `book_title` is not empty.
Extract `level` from `data.get("level", "0")`.
Check duplicate: `self.reading_repo.exists_duplicate(parsed_student_id, book_title, start_date)`.
Save directly via `self.reading_repo.create(...)`.

- [ ] **Step 3: Clean up `app/services/catalog_service.py` and `app/services/seed_service.py`**

Remove `BookRepository` imports and methods from `CatalogService`.
Remove `_seed_books()` from `SeedService`.
Delete `app/repositories/book_repository.py`.

- [ ] **Step 4: Commit repository and service updates**

```bash
git rm app/repositories/book_repository.py
git add app/repositories/reading_repository.py app/services/reading_service.py app/services/catalog_service.py app/services/seed_service.py
git commit -m "refactor(services): integrate book attributes directly into reading service and remove BookRepository"
```

---

### Task 4: Schemas and API Blueprints Refactoring

**Files:**
- Modify: `app/schemas/reading_schema.py`
- Modify: `app/api/v1/readings.py`
- Modify: `app/api/v1/__init__.py`
- Modify: `app/__init__.py`
- Delete: `app/api/v1/books.py`
- Delete: `app/schemas/book_schema.py`

**Interfaces:**
- `POST /api/students/<student_id>/books` / `POST /api/v1/students/<student_id>/books`: accepts `book_title` (or `title`), `level`, `start_date`, `end_date`.
- `GET /api/v1/readings`: returns list of readings with `book_title` and `book_level` directly from `ReadBook`.
- Removes `/api/v1/books` and `/api/books`.

- [ ] **Step 1: Update `app/schemas/reading_schema.py`**

Update `ReadingCreateSchema`:
```python
class ReadingCreateSchema(Schema):
    book_title = fields.Str(required=False, allow_none=True)
    title = fields.Str(required=False, allow_none=True)
    book = fields.Str(required=False, allow_none=True)
    level = fields.Str(load_default="0")
    start_date = fields.Date(required=True)
    end_date = fields.Date(load_default=None, allow_none=True)
    copies_note = fields.Str(load_default=None, allow_none=True)
    sessions_note = fields.Str(load_default=None, allow_none=True)
```

- [ ] **Step 2: Update `app/api/v1/readings.py`**

Update `list_readings()` to read `r.book_title` and `r.level` directly:
```python
"book_title": r.book_title,
"book_level": r.level,
```

- [ ] **Step 3: Remove `books_bp` from `app/api/v1/__init__.py` and `app/__init__.py`**

Delete `app/api/v1/books.py` and `app/schemas/book_schema.py`.
Remove registration of `books_bp` in `app/__init__.py`.

- [ ] **Step 4: Commit schemas and API changes**

```bash
git rm app/api/v1/books.py app/schemas/book_schema.py
git add app/schemas/reading_schema.py app/api/v1/readings.py app/api/v1/__init__.py app/__init__.py
git commit -m "refactor(api): remove books blueprint and update readings schemas"
```

---

### Task 5: Update Tests and End-to-End Verification

**Files:**
- Modify: `tests/test_be23_asignar_libro.py`
- Modify: `tests/test_be24_cerrar_lectura.py`
- Modify: `tests/test_be25_relectura.py`
- Modify: `tests/test_be26_lecturas_por_alumno_y_libro.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_be28_ficha_alumno_agregada.py`
- Modify: `tests/test_be36_informe_individual_alumno.py`

**Interfaces:**
- All tests construct `ReadBook` directly with `book_title` and `level`.

- [ ] **Step 1: Update reading tests to use `book_title`**

Update `tests/test_be23_asignar_libro.py`, `tests/test_be24_cerrar_lectura.py`, `tests/test_be25_relectura.py`, `tests/test_be26_lecturas_por_alumno_y_libro.py` so they test assigning with `{"book_title": "El Principito", "level": "I", "start_date": "2026-09-01"}`.

- [ ] **Step 2: Run reading tests suite**

```bash
docker exec -e TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test hares_backend pytest tests/test_be23_asignar_libro.py tests/test_be24_cerrar_lectura.py tests/test_be25_relectura.py tests/test_be26_lecturas_por_alumno_y_libro.py
```
Expected: All tests pass.

- [ ] **Step 3: Run full backend regression test suite**

```bash
docker exec -e TEST_DATABASE_URL=postgresql://hares_user:hares_dev_secret@database:5432/hares_test hares_backend pytest
```
Expected: Full test suite passes without regressions.

- [ ] **Step 4: Commit test updates**

```bash
git add tests/
git commit -m "test: update reading tests for unified read_books model"
```
