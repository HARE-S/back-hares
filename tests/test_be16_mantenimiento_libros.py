import datetime
import uuid
import pytest
from sqlalchemy import inspect
from app.models.book import Book, ReadedBook
from app.models.student import Student


def test_scenario_1_create_book_success(client):
    """
    Escenario 1: Alta de libro (POST /api/books y POST /api/v1/books)
    Dado un coordinador con sesión activa
    Cuando envía title y level
    Entonces el sistema crea el libro
    Y devuelve 201 Created
    """
    headers = {"X-User-Role": "coordinator"}
    payload = {
        "title": "El Principito",
        "level": "I",
        "copies_note": "5 ejemplares en biblioteca",
        "sessions_note": "Sesión semanal de 30 min",
    }

    # Probar endpoint directo /api/books
    resp = client.post("/api/books", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "El Principito"
    assert data["book"] == "El Principito"
    assert data["level"] == "I"
    assert data["copies_note"] == "5 ejemplares en biblioteca"
    assert data["sessions_note"] == "Sesión semanal de 30 min"
    assert "id" in data

    # Probar también endpoint canónico /api/v1/books
    payload_v1 = {
        "title": "Don Quijote de la Mancha",
        "level": "II",
    }
    resp_v1 = client.post("/api/v1/books", json=payload_v1, headers=headers)
    assert resp_v1.status_code == 201
    assert resp_v1.get_json()["title"] == "Don Quijote de la Mancha"


def test_scenario_2_duplicate_title_rejected(client):
    """
    Escenario 2: Título duplicado
    Dado un libro existente con el mismo título
    Cuando se intenta crear otro igual
    Entonces el sistema rechaza la petición
    Y devuelve 409 Conflict
    """
    headers = {"X-User-Role": "coordinator"}
    payload = {
        "title": "Cien años de soledad",
        "level": "II",
    }

    # Primera creación exitosa
    resp1 = client.post("/api/v1/books", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Segunda creación con el mismo título
    resp2 = client.post("/api/v1/books", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert "Ya existe un libro" in resp2.get_json()["error"]

    # Duplicado insensible a mayúsculas
    payload_case = {
        "title": "cien AÑOS de SOLEDAD",
        "level": "I",
    }
    resp3 = client.post("/api/v1/books", json=payload_case, headers=headers)
    assert resp3.status_code == 409


def test_scenario_3_query_and_modification(client):
    """
    Escenario 3: Consulta y modificación
    Dado un libro existente
    Cuando se consulta, reemplaza o modifica parcialmente
    Entonces el sistema responde 200 OK
    Y 422 si los datos de la modificación no son válidos
    """
    headers = {"X-User-Role": "coordinator"}
    create_resp = client.post(
        "/api/v1/books",
        json={"title": "La metamorfosis", "level": "I"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    book_id = create_resp.get_json()["id"]

    # 1. Consulta individual GET -> 200 OK
    get_resp = client.get(f"/api/v1/books/{book_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["title"] == "La metamorfosis"

    # También a través de /api/books/<id>
    get_resp_alias = client.get(f"/api/books/{book_id}")
    assert get_resp_alias.status_code == 200
    assert get_resp_alias.get_json()["title"] == "La metamorfosis"

    # 2. Reemplazo completo PUT -> 200 OK
    put_payload = {
        "title": "La metamorfosis - Edición anotada",
        "level": "I/II",
        "copies_note": "3 copias",
        "sessions_note": "Trimestre 2",
    }
    put_resp = client.put(f"/api/v1/books/{book_id}", json=put_payload, headers=headers)
    assert put_resp.status_code == 200
    put_data = put_resp.get_json()
    assert put_data["title"] == "La metamorfosis - Edición anotada"
    assert put_data["level"] == "I/II"
    assert put_data["copies_note"] == "3 copias"

    # 3. Modificación parcial PATCH -> 200 OK
    patch_payload = {
        "level": "II",
    }
    patch_resp = client.patch(f"/api/v1/books/{book_id}", json=patch_payload, headers=headers)
    assert patch_resp.status_code == 200
    patch_data = patch_resp.get_json()
    assert patch_data["level"] == "II"
    assert patch_data["title"] == "La metamorfosis - Edición anotada"

    # 4. Datos inválidos -> 422 Unprocessable Entity (Nivel inválido no perteneciente a BE-15)
    invalid_patch = {"level": "III"}
    err_resp = client.patch(f"/api/v1/books/{book_id}", json=invalid_patch, headers=headers)
    assert err_resp.status_code == 422
    assert "no reconocido" in err_resp.get_json()["error"]

    # Título vacío en PUT -> 422
    invalid_put = {"title": "   ", "level": "0"}
    err_put = client.put(f"/api/v1/books/{book_id}", json=invalid_put, headers=headers)
    assert err_put.status_code == 422

    # Intentar renombrar a un título que ya tiene otro libro -> 409 Conflict
    client.post("/api/v1/books", json={"title": "Ficciones", "level": "II"}, headers=headers)
    dup_patch = {"title": "Ficciones"}
    err_dup = client.patch(f"/api/v1/books/{book_id}", json=dup_patch, headers=headers)
    assert err_dup.status_code == 409


def test_scenario_4_soft_delete_preserves_reading_records(client, session):
    """
    Escenario 4: Baja lógica
    Dado un libro activo
    Cuando se envía DELETE
    Entonces se rellena disabled_at
    Y devuelve 204 No Content
    Y las lecturas registradas de ese libro siguen siendo consultables
    """
    headers = {"X-User-Role": "coordinator"}
    # 1. Crear libro
    book_resp = client.post(
        "/api/v1/books",
        json={"title": "El Lazarillo de Tormes", "level": "0-I"},
        headers=headers,
    )
    assert book_resp.status_code == 201
    book_id = uuid.UUID(book_resp.get_json()["id"])

    # 2. Registrar una lectura asociada a un alumno
    student = Student(name="Lázaro de Tormes")
    session.add(student)
    session.flush()

    reading = ReadedBook(
        student_id=student.id,
        book_id=book_id,
        start_date=datetime.date(2026, 1, 15),
        end_date=datetime.date(2026, 2, 10),
    )
    session.add(reading)
    session.commit()

    # 3. Enviar DELETE al libro
    del_resp = client.delete(f"/api/v1/books/{book_id}", headers=headers)
    assert del_resp.status_code == 204

    # 4. Verificar que se rellenó disabled_at
    book_in_db = session.get(Book, book_id)
    assert book_in_db is not None
    assert book_in_db.disabled_at is not None
    assert book_in_db.disabled_at == datetime.date.today()

    # 5. Verificar que la lectura registrada sigue existiendo y siendo consultable
    reading_in_db = session.query(ReadedBook).filter_by(book_id=book_id).first()
    assert reading_in_db is not None
    assert reading_in_db.student_id == student.id
    assert reading_in_db.start_date == datetime.date(2026, 1, 15)

    # 6. El catálogo por defecto ya no lo lista
    list_resp = client.get("/api/v1/books")
    listed_ids = [b["id"] for b in list_resp.get_json()]
    assert str(book_id) not in listed_ids

    # Pero con include_disabled=true sí aparece
    list_all_resp = client.get("/api/v1/books?include_disabled=true")
    listed_all_ids = [b["id"] for b in list_all_resp.get_json()]
    assert str(book_id) in listed_all_ids


def test_scenario_5_books_resource_contains_no_student_references(app):
    """
    Escenario 5: El catálogo no contiene alumnos
    Dado el recurso de libros
    Cuando se inspecciona su estructura
    Entonces no contiene ninguna referencia a un alumno concreto
    Y la relación entre alumno y libro vive únicamente en read_books / readed_books
    """
    from app.extensions import db
    inspector = inspect(db.engine)
    book_columns = [col["name"] for col in inspector.get_columns("books")]

    # Verificar que NO existe student_id en books
    assert "student_id" not in book_columns
    assert "student" not in book_columns

    # Verificar que no hay foreign key a students en books
    fks = inspector.get_foreign_keys("books")
    fk_referred_tables = [fk.get("referred_table") for fk in fks]
    assert "students" not in fk_referred_tables

    # Verificar atributos y columnas del modelo Book
    mapper = inspect(Book)
    model_columns = [c.key for c in mapper.columns]
    assert "student_id" not in model_columns
    assert not hasattr(Book, "student_id")
    assert not hasattr(Book, "student")

    # Verificar que la relación vive en la tabla de asociación de lecturas
    table_names = inspector.get_table_names()
    reading_table = "read_books" if "read_books" in table_names else "readed_books"
    reading_columns = [col["name"] for col in inspector.get_columns(reading_table)]
    assert "student_id" in reading_columns
    assert "book_id" in reading_columns


def test_security_mutations_require_coordinator_or_admin(client):
    """
    Seguridad: POST, PUT, PATCH y DELETE requieren rol 'coordinator' o 'admin'.
    Roles no autorizados (ej: tutor o student) reciben 403 Forbidden.
    """
    # 1. POST
    resp_post = client.post(
        "/api/v1/books",
        json={"title": "Libro no autorizado", "level": "I"},
        headers={"X-User-Role": "tutor"},
    )
    assert resp_post.status_code == 403

    # Crear un libro con rol coordinator para pruebas de edición/borrado
    created = client.post(
        "/api/v1/books",
        json={"title": "Libro de prueba seguridad", "level": "0"},
        headers={"X-User-Role": "coordinator"},
    )
    book_id = created.get_json()["id"]

    # 2. PUT
    resp_put = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Modificado", "level": "0"},
        headers={"X-User-Role": "tutor"},
    )
    assert resp_put.status_code == 403

    # 3. PATCH
    resp_patch = client.patch(
        f"/api/v1/books/{book_id}",
        json={"level": "I"},
        headers={"X-User-Role": "student"},
    )
    assert resp_patch.status_code == 403

    # 4. DELETE
    resp_del = client.delete(
        f"/api/v1/books/{book_id}",
        headers={"X-User-Role": "tutor"},
    )
    assert resp_del.status_code == 403

    # 5. GET está permitido sin restricción de rol
    resp_get = client.get(f"/api/v1/books/{book_id}", headers={"X-User-Role": "tutor"})
    assert resp_get.status_code == 200
