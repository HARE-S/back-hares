import pytest
from app.models.book import Book
from app.models.enums import BookLevel
from app.repositories.book_repository import BookRepository


def test_scenario_1_valid_levels_accepted(session):
    """
    Escenario 1: Niveles válidos aceptados
    Dado los niveles usados por el centro
    Cuando se registra un libro con nivel "0", "0-I", "I", "II" o "I/II"
    Entonces el sistema acepta el valor
    Y lo conserva tal cual
    """
    valid_levels = ["0", "0-I", "I", "II", "I/II"]
    repo = BookRepository(session)

    for lvl in valid_levels:
        book = repo.create(book=f"Libro nivel {lvl}", level=lvl)
        assert book.id is not None
        assert book.level == lvl

    # Verificar que en la base de datos se conservan tal cual
    saved_books = repo.get_all()
    saved_levels = {b.level for b in saved_books}
    assert saved_levels == set(valid_levels)


def test_scenario_2_invalid_level_rejected(session):
    """
    Escenario 2: Nivel no reconocido
    Dado un libro con nivel "III"
    Cuando se intenta registrar
    Entonces el sistema rechaza la petición
    Y devuelve error enumerando los niveles válidos
    """
    repo = BookRepository(session)

    with pytest.raises(ValueError) as exc_info:
        repo.create(book="Libro nivel prohibido", level="III")

    error_message = str(exc_info.value)
    # Debe rechazar y enumerar los niveles válidos
    assert "no reconocido" in error_message
    assert "'0'" in error_message
    assert "'0-I'" in error_message
    assert "'I'" in error_message
    assert "'I/II'" in error_message
    assert "'II'" in error_message


def test_scenario_3_ordering_by_pedagogical_level(session):
    """
    Escenario 3: Ordenación por nivel
    Dado libros de niveles "II", "0", "I/II" y "0-I"
    Cuando se consulta el catálogo ordenado por nivel
    Entonces se devuelven en el orden pedagógico 0, 0-I, I, I/II, II
    Y no en orden alfabético
    """
    repo = BookRepository(session)

    # Insertamos en orden deliberadamente desordenado
    repo.create(book="Libro D", level="II")
    repo.create(book="Libro A", level="0")
    repo.create(book="Libro C", level="I/II")
    repo.create(book="Libro B", level="0-I")
    repo.create(book="Libro Intermedio", level="I")

    # Consultamos ordenado por nivel
    ordered_books = repo.get_all(order_by_level=True)
    ordered_levels = [b.level for b in ordered_books]

    # Orden pedagógico esperado: 0, 0-I, I, I/II, II
    expected_order = ["0", "0-I", "I", "I/II", "II"]
    assert ordered_levels == expected_order


def test_scenario_4_filter_by_exact_level(session):
    """
    Escenario 4: Filtro por nivel
    Dado un catálogo con libros de varios niveles
    Cuando se filtra por nivel "I"
    Entonces se devuelven solo los libros de ese nivel
    Y no los de "0-I" ni "I/II"
    """
    repo = BookRepository(session)

    repo.create(book="Lectura Nivel 0", level="0")
    repo.create(book="Lectura Nivel 0-I", level="0-I")
    b1 = repo.create(book="Lectura Nivel I - Tomo 1", level="I")
    b2 = repo.create(book="Lectura Nivel I - Tomo 2", level="I")
    repo.create(book="Lectura Nivel I/II", level="I/II")
    repo.create(book="Lectura Nivel II", level="II")

    # Filtrar estrictamente por nivel "I"
    results = repo.get_all(level="I")

    assert len(results) == 2
    for b in results:
        assert b.level == "I"
        assert b.level != "0-I"
        assert b.level != "I/II"

    result_titles = {b.book for b in results}
    assert result_titles == {"Lectura Nivel I - Tomo 1", "Lectura Nivel I - Tomo 2"}
