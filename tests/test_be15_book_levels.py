import datetime
import pytest
from app.models.book import ReadBook
from app.models.student import Student
from app.repositories.reading_repository import ReadingRepository


def test_scenario_1_valid_levels_accepted(session):
    """
    Escenario 1: Niveles válidos aceptados en ReadBook
    Dado los niveles pedagógicos del centro
    Cuando se valida o registra un libro leído con nivel "0", "0-I", "I", "II" o "I/II"
    Entonces el sistema acepta el valor
    Y lo conserva tal cual
    """
    valid_levels = ["0", "0-I", "I", "II", "I/II"]
    student = Student(name="Alumno Niveles")
    session.add(student)
    session.commit()

    repo = ReadingRepository(session)
    for i, lvl in enumerate(valid_levels):
        rb = repo.create(
            student_id=student.id,
            book_title=f"Libro nivel {lvl}",
            level=lvl,
            start_date=datetime.date(2026, 9, 1 + i),
        )
        assert rb.id is not None
        assert rb.level == lvl

    saved_readings = repo.get_by_student(student.id)
    saved_levels = {r.level for r in saved_readings}
    assert saved_levels == set(valid_levels)


def test_scenario_2_invalid_level_rejected():
    """
    Escenario 2: Nivel no reconocido
    Dado un nivel no reconocido como "III"
    Cuando se intenta registrar en ReadBook
    Entonces el sistema rechaza el valor
    Y devuelve error enumerando los niveles válidos
    """
    with pytest.raises(ValueError) as exc_info:
        ReadBook(book_title="Libro nivel prohibido", level="III")

    error_message = str(exc_info.value)
    assert "no reconocido" in error_message
    assert "'0'" in error_message
    assert "'0-I'" in error_message
    assert "'I'" in error_message
    assert "'I/II'" in error_message
    assert "'II'" in error_message


def test_scenario_3_ordering_by_pedagogical_level():
    """
    Escenario 3: Ordenación pedagógica por nivel
    Dado libros con niveles "II", "0", "I/II" y "0-I"
    Cuando se ordenan por su propiedad level_order
    Entonces se devuelven en el orden 0, 0-I, I, I/II, II y no alfabético
    """
    levels = ["II", "0", "I/II", "0-I", "I"]
    books = [ReadBook(book_title=f"Libro {lvl}", level=lvl) for lvl in levels]
    ordered = sorted(books, key=lambda b: b.level_order)
    expected_order = ["0", "0-I", "I", "I/II", "II"]
    assert [b.level for b in ordered] == expected_order


def test_scenario_4_filter_by_exact_level(session):
    """
    Escenario 4: Filtro por nivel exacto en lecturas
    Dado lecturas registradas con varios niveles
    Cuando se filtra por nivel exacto
    Entonces se devuelven solo las de ese nivel
    """
    student = Student(name="Alumno Filtro")
    session.add(student)
    session.commit()

    repo = ReadingRepository(session)
    repo.create(student_id=student.id, book_title="Libro Nivel 0", level="0", start_date=datetime.date(2026, 9, 1))
    repo.create(student_id=student.id, book_title="Libro Nivel 0-I", level="0-I", start_date=datetime.date(2026, 9, 2))
    repo.create(student_id=student.id, book_title="Libro Nivel I - 1", level="I", start_date=datetime.date(2026, 9, 3))
    repo.create(student_id=student.id, book_title="Libro Nivel I - 2", level="I", start_date=datetime.date(2026, 9, 4))
    repo.create(student_id=student.id, book_title="Libro Nivel I/II", level="I/II", start_date=datetime.date(2026, 9, 5))
    repo.create(student_id=student.id, book_title="Libro Nivel II", level="II", start_date=datetime.date(2026, 9, 6))

    all_readings = repo.get_by_student(student.id)
    level_i_readings = [r for r in all_readings if r.level == "I"]
    assert len(level_i_readings) == 2
    for r in level_i_readings:
        assert r.level == "I"
        assert r.level != "0-I"
        assert r.level != "I/II"

    titles = {r.book_title for r in level_i_readings}
    assert titles == {"Libro Nivel I - 1", "Libro Nivel I - 2"}

