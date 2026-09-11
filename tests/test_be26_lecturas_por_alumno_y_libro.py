import datetime
import uuid
import pytest
from app import create_app
from app.config import Config
from app.models.book import Book, ReadBook
from app.models.center import Center, Section
from app.models.student import Student, StudentSection


class NoBypassConfig(Config):
    TESTING = True
    APP_ENV = "development"
    DEV_AUTH_BYPASS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def setup_data(session):
    """Fixture para crear datos base de prueba para BE-26."""
    center = Center(name="Colegio Cervantes")
    session.add(center)
    session.flush()

    section1 = Section(name="1º ESO A", center_id=center.id)
    section2 = Section(name="1º ESO B", center_id=center.id)
    session.add_all([section1, section2])
    session.flush()

    s1 = Student(name="Aitor Ortiz")
    s2 = Student(name="Leire Blanco")
    s3_no_readings = Student(name="Mikel Lopez")
    session.add_all([s1, s2, s3_no_readings])
    session.flush()

    ss1 = StudentSection(student_id=s1.id, section_id=section1.id)
    ss2 = StudentSection(student_id=s2.id, section_id=section2.id)
    ss3 = StudentSection(student_id=s3_no_readings.id, section_id=section1.id)
    session.add_all([ss1, ss2, ss3])
    session.flush()

    book1 = Book(book="Don Quijote de la Mancha", level="I")
    book2 = Book(book="El Lazarillo de Tormes", level="0")
    book_unread = Book(book="La Celestina", level="II")
    session.add_all([book1, book2, book_unread])
    session.flush()

    # Lectura 1 de s1: Finalizada de book1
    r1 = ReadBook(
        student_id=s1.id,
        book_id=book1.id,
        start_date=datetime.date(2026, 9, 1),
        end_date=datetime.date(2026, 9, 25),
    )
    # Lectura 2 de s1: En curso de book2
    r2 = ReadBook(
        student_id=s1.id,
        book_id=book2.id,
        start_date=datetime.date(2026, 10, 1),
        end_date=None,
    )
    # Lectura 3 de s2: En curso de book1 (mismo libro que leyó s1)
    r3 = ReadBook(
        student_id=s2.id,
        book_id=book1.id,
        start_date=datetime.date(2026, 10, 5),
        end_date=None,
    )
    session.add_all([r1, r2, r3])
    session.commit()

    return {
        "center": center,
        "section1": section1,
        "section2": section2,
        "student1": s1,
        "student2": s2,
        "student_no_readings": s3_no_readings,
        "book1": book1,
        "book2": book2,
        "book_unread": book_unread,
        "reading1": r1,
        "reading2": r2,
        "reading3": r3,
    }


def test_scenario_1_student_readings_with_book_title_and_level(client, setup_data):
    """
    Escenario 1: Lecturas de un alumno
    Dado un alumno con varias lecturas registradas
    Cuando se consulta GET /api/students/{id}/books
    Entonces se devuelven sus lecturas con el título y el nivel de cada libro
    Y devuelve 200 OK
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    resp = client.get(f"/api/students/{s1.id}/books")
    assert resp.status_code == 200

    items = resp.get_json()
    assert isinstance(items, list)
    assert len(items) == 2

    titles = {item["title"] for item in items}
    levels = {item["level"] for item in items}
    assert "Don Quijote de la Mancha" in titles
    assert "El Lazarillo de Tormes" in titles
    assert "I" in levels
    assert "0" in levels

    # Verificar que también se incluyen book_title y book_level
    for item in items:
        assert item["book_title"] == item["title"]
        assert item["book_level"] == item["level"]
        assert "status" in item
        assert "start_date" in item


def test_scenario_2_students_who_read_a_book(client, setup_data):
    """
    Escenario 2: Alumnos que han leído un libro
    Dado un libro leído por varios alumnos (book1 leído por s1 y s2)
    Cuando se consulta GET /api/books/{id}/students
    Entonces se devuelve la lista de alumnos con sus fechas de lectura
    """
    b1 = setup_data["book1"]
    s1 = setup_data["student1"]
    s2 = setup_data["student2"]

    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    resp = client.get(f"/api/books/{b1.id}/students")
    assert resp.status_code == 200

    items = resp.get_json()
    assert isinstance(items, list)
    assert len(items) == 2

    student_names = {item["student_name"] for item in items}
    student_ids = {item["student_id"] for item in items}
    assert "Aitor Ortiz" in student_names
    assert "Leire Blanco" in student_names
    assert str(s1.id) in student_ids
    assert str(s2.id) in student_ids

    # Verificar fechas de lectura
    s1_item = next(item for item in items if item["student_id"] == str(s1.id))
    assert s1_item["start_date"] == "2026-09-01"
    assert s1_item["end_date"] == "2026-09-25"
    assert s1_item["status"] == "finalizada"

    s2_item = next(item for item in items if item["student_id"] == str(s2.id))
    assert s2_item["start_date"] == "2026-10-05"
    assert s2_item["end_date"] is None
    assert s2_item["status"] == "en curso"


def test_scenario_3_filter_by_status_in_progress_and_finished(client, setup_data):
    """
    Escenario 3: Filtro por estado
    Dado un alumno con lecturas en curso y finalizadas
    Cuando se consulta filtrando por estado "en curso"
    Entonces se devuelven solo las que no tienen fecha de fin
    """
    s1 = setup_data["student1"]
    sec1 = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    # 1. Filtro 'en curso'
    resp_in_progress = client.get(f"/api/students/{s1.id}/books?status=en curso")
    assert resp_in_progress.status_code == 200
    items_ip = resp_in_progress.get_json()
    assert len(items_ip) == 1
    assert items_ip[0]["status"] == "en curso"
    assert items_ip[0]["end_date"] is None
    assert items_ip[0]["title"] == "El Lazarillo de Tormes"

    # 2. Filtro 'finalizada'
    resp_finished = client.get(f"/api/students/{s1.id}/books?status=finalizada")
    assert resp_finished.status_code == 200
    items_fin = resp_finished.get_json()
    assert len(items_fin) == 1
    assert items_fin[0]["status"] == "finalizada"
    assert items_fin[0]["end_date"] == "2026-09-25"
    assert items_fin[0]["title"] == "Don Quijote de la Mancha"


def test_scenario_4_student_without_readings_returns_empty_list(client, setup_data):
    """
    Escenario 4: Sin lecturas
    Dado un alumno sin ninguna lectura registrada
    Cuando se consulta su listado
    Entonces se devuelve una lista vacía con 200 OK
    """
    s3 = setup_data["student_no_readings"]
    sec1 = setup_data["section1"]

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec1.id)]},
    )

    resp = client.get(f"/api/students/{s3.id}/books")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_scenario_5_tutor_without_permission_forbidden(client, setup_data):
    """
    Escenario 5: Tutor sin permiso
    Dado un tutor cuyas secciones no incluyen a ese alumno
    Cuando consulta sus lecturas
    Entonces el sistema devuelve 403 Forbidden
    """
    s1 = setup_data["student1"]  # Sección 1
    sec2 = setup_data["section2"]  # Tutor asignado solo a Sección 2

    client.post(
        "/api/dev/session",
        json={"role": "tutor", "sections": [str(sec2.id)]},
    )

    resp = client.get(f"/api/students/{s1.id}/books")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "FORBIDDEN"


def test_book_students_non_existent_book_404(client, setup_data):
    """Consulta de alumnos para un libro inexistente devuelve 404 Not Found."""
    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )
    non_existent_id = uuid.uuid4()
    resp = client.get(f"/api/books/{non_existent_id}/students")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "NOT_FOUND"


def test_book_students_unread_book_returns_empty_list(client, setup_data):
    """Libro que no ha sido leído por nadie devuelve lista vacía con 200 OK."""
    b_unread = setup_data["book_unread"]
    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )
    resp = client.get(f"/api/books/{b_unread.id}/students")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_book_students_filter_by_status(client, setup_data):
    """Filtro por status en GET /api/books/{id}/students."""
    b1 = setup_data["book1"]
    client.post(
        "/api/dev/session",
        json={"role": "coordinator", "sections": []},
    )

    # Solo en curso para book1 (leído por s2)
    resp = client.get(f"/api/books/{b1.id}/students?status=en curso")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]["student_name"] == "Leire Blanco"


def test_unauthenticated_and_pending_role(client, setup_data):
    """Control de acceso: 401 sin sesión y 403 con rol pendiente."""
    b1_id = str(setup_data["book1"].id)
    s1_id = str(setup_data["student1"].id)

    app = create_app(NoBypassConfig)
    with app.test_client() as unauth_client:
        # 401 sin sesión
        assert unauth_client.get(f"/api/students/{s1_id}/books").status_code == 401
        assert unauth_client.get(f"/api/books/{b1_id}/students").status_code == 401

    # 403 con rol pendiente
    client.post("/api/dev/session", json={"role": "pendiente", "sections": []})
    assert client.get(f"/api/students/{s1_id}/books").status_code == 403
    assert client.get(f"/api/books/{b1_id}/students").status_code == 403
