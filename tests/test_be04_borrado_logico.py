import datetime
import uuid
from app.models.book import Book
from app.models.center import Center, Section
from app.models.student import Student
from app.models.test import Result, Test
from app.repositories.book_repository import BookRepository
from app.repositories.test_repository import TestRepository


def test_scenario_1_delete_active_test_sets_disabled_at(client, session):
    """
    Escenario 1: Baja de una prueba
    Dado una prueba activa en el catálogo
    Cuando se envía DELETE sobre esa prueba
    Entonces el sistema rellena su campo disabled_at con la fecha actual
    Y NO borra la fila de la base de datos
    Y devuelve 204 No Content
    """
    repo = TestRepository(session)
    test = repo.create(code="0IF", name="Normativa piscinas", words=235)
    test_id = str(test.id)

    response = client.delete(f"/api/v1/tests/{test_id}")
    assert response.status_code == 204

    # Verificar que la fila sigue existiendo en la base de datos
    session.expire_all()
    saved_test = session.get(Test, uuid.UUID(test_id))
    assert saved_test is not None
    assert saved_test.disabled_at is not None
    assert saved_test.disabled_at == datetime.date.today()


def test_scenario_2_disabled_test_excluded_from_default_listing(client, session):
    """
    Escenario 2: La prueba desaparece del listado
    Dado una prueba con disabled_at relleno
    Cuando se consulta el listado de pruebas sin parámetros
    Entonces esa prueba no aparece en los resultados
    """
    repo = TestRepository(session)
    repo.create(code="0IF", name="Normativa piscinas activa", words=235)
    repo.create(
        code="0IL",
        name="Los cazadores de focas obsoleta",
        words=258,
        disabled_at=datetime.date(2025, 1, 1),
    )

    response = client.get("/api/v1/tests")
    assert response.status_code == 200

    data = response.get_json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    codes = [item["code"] for item in items]

    assert "0IF" in codes
    assert "0IL" not in codes


def test_scenario_3_include_disabled_shows_disabled_tests(client, session):
    """
    Escenario 3: Consulta explícita de deshabilitadas
    Dado una prueba con disabled_at relleno
    Cuando se consulta el listado con include_disabled=true
    Entonces esa prueba sí aparece en los resultados
    Y se distingue por llevar fecha en disabled_at
    """
    repo = TestRepository(session)
    repo.create(code="0IF", name="Normativa piscinas", words=235)
    repo.create(
        code="0IL",
        name="Los cazadores de focas obsoleta",
        words=258,
        disabled_at=datetime.date(2025, 1, 1),
    )

    response = client.get("/api/v1/tests?include_disabled=true")
    assert response.status_code == 200

    data = response.get_json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    codes = [item["code"] for item in items]

    assert "0IF" in codes
    assert "0IL" in codes

    disabled_item = next(item for item in items if item["code"] == "0IL")
    assert disabled_item["disabled_at"] == "2025-01-01"



def test_scenario_4_student_results_history_preserved_after_soft_delete(
    client, session
):
    """
    Escenario 4: El histórico se conserva
    Dado resultados de alumnos asociados a una prueba deshabilitada
    Cuando se consulta el histórico de esos alumnos
    Entonces los resultados siguen siendo accesibles
    Y muestran el nombre de la prueba con normalidad
    """
    center = Center(name="Centro Bolueta")
    section = Section(name="1CARMED2", center=center)
    student = Student(name="Alumno Pruebas Histórico")
    test = Test(code="0AF", name="La vaca", words=269)
    session.add_all([center, section, student, test])
    session.commit()

    # Se registra un resultado para el alumno con esa prueba
    result = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test.id,
        test_date=datetime.date(2024, 10, 15),
        time=120,
        successes=10,
        mistakes=0,
    )
    session.add(result)
    session.commit()

    # Se da de baja lógica la prueba
    client.delete(f"/api/v1/tests/{test.id}")

    # Verificar que el resultado histórico sigue intacto y conserva los datos de la prueba
    session.expire_all()
    saved_result = session.get(Result, result.id)
    assert saved_result is not None
    assert saved_result.test is not None
    assert saved_result.test.name == "La vaca"
    assert saved_result.test.code == "0AF"
    assert saved_result.test.disabled_at is not None


def test_scenario_5_delete_nonexistent_test_returns_404(client):
    """
    Escenario 5: Baja de una prueba inexistente
    Dado un identificador de prueba que no existe
    Cuando se envía DELETE
    Entonces el sistema devuelve 404 Not Found
    """
    random_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/tests/{random_id}")
    assert response.status_code == 404
    data = response.get_json()
    assert "no encontrada" in data.get("error", "").lower()


def test_book_soft_delete_scenarios(client, session):
    """
    Pruebas de borrado lógico aplicadas a la entidad Book (alcance de BE-04).
    """
    repo = BookRepository(session)
    b1 = repo.create(book="Libro Vigente", level="I")
    b2 = repo.create(
        book="Libro Antiguo", level="0", disabled_at=datetime.date(2024, 5, 1)
    )

    # 1. Por defecto no aparece el deshabilitado
    res_active = client.get("/api/v1/books")
    assert res_active.status_code == 200
    titles = [b["book"] for b in res_active.get_json()]
    assert "Libro Vigente" in titles
    assert "Libro Antiguo" not in titles

    # 2. Con include_disabled=true aparecen ambos
    res_all = client.get("/api/v1/books?include_disabled=true")
    titles_all = [b["book"] for b in res_all.get_json()]
    assert "Libro Vigente" in titles_all
    assert "Libro Antiguo" in titles_all

    # 3. DELETE sobre b1 rellena disabled_at y devuelve 204
    res_del = client.delete(f"/api/v1/books/{b1.id}")
    assert res_del.status_code == 204

    session.expire_all()
    b1_saved = session.get(Book, b1.id)
    assert b1_saved.disabled_at == datetime.date.today()

    # 4. DELETE sobre id inexistente devuelve 404
    res_404 = client.delete(f"/api/v1/books/{uuid.uuid4()}")
    assert res_404.status_code == 404
