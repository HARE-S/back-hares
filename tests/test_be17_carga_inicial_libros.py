"""BE-17: Carga inicial del catálogo de libros — escenarios 1 a 5.

Cubrimos la lectura del Excel del centro (formato canónico de hoja única
`titulo;nivel;ejemplares;sesiones`), la normalización de niveles BE-15, el
listado de revisión manual para filas no interpretables y la carga
idempotente por título.
"""
import datetime

import pytest
from openpyxl import Workbook

from app.core.exceptions import ValidationError
from app.extensions import db
from app.importer import BookImporter, normalize_book_level, parse_books_xlsx
from app.importer.books_parser import MAX_NOTE_LENGTH, write_review_csv
from app.repositories.book_repository import BookRepository

HEADER = ["titulo", "nivel", "ejemplares", "sesiones"]


def _make_workbook(rows, sheet_title="libros"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    for row in rows:
        ws.append(row)
    return wb


def _write_xlsx(wb, tmp_path, name="libros_tests.xlsx"):
    path = tmp_path / name
    wb.save(path)
    return path


def _import(session, path):
    return BookImporter(session).import_from_xlsx(path)


def _books(session, title):
    return BookRepository(session).get_by_title(title)


# --------------------------------------------------------------------------- #
# Normalización de niveles (BE-15: 0, 0-I, I, I/II, II)                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0", "0"),
        ("II", "II"),
        ("  I  ", "I"),
        ("Nivel 0-I", "0-I"),
        ("niVel I", "I"),
        ("N. 0-I", "0-I"),
        ("0 - I", "0-I"),
        ("I/II", "I/II"),
        ("I-II", "I/II"),
        ("i", "I"),
        ("NIVEL II", "II"),
    ],
)
def test_normalize_book_level_known_variants_map_to_canonical(raw, expected):
    assert normalize_book_level(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "III", "Nivel III", "IV", "2"])
def test_normalize_book_level_unknown_returns_none(raw):
    assert normalize_book_level(raw) is None


# --------------------------------------------------------------------------- #
# Escenario 1: Importación de filas válidas                                   #
# --------------------------------------------------------------------------- #


def test_scenario_1_valid_rows_create_books_and_full_summary(app, tmp_path):
    """Dado el Excel de listado de libros del centro
    Cuando se ejecuta la importación
    Entonces se crean los libros con su título y su nivel
    Y se informa del número de libros creados
    """
    rows = [
        HEADER,
        ("El pirata valiente", "Nivel 0-I", "12", "4"),
        ("Aventuras en el mar", "0-I", "PDF", "PREPARAR"),
        ("Misterios de invierno", "II", "3", "5+"),
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["books_created"] == 3
        assert summary["books_existing"] == 0
        assert summary["errors"] == 0
        assert summary["processed"] == 3
        assert summary["review"] == []

        assert _books(db.session, "El pirata valiente").level == "0-I"
        assert _books(db.session, "Aventuras en el mar").level == "0-I"
        assert _books(db.session, "Misterios de invierno").level == "II"


# --------------------------------------------------------------------------- #
# Escenario 2: Filas de cabecera repetidas                                    #
# --------------------------------------------------------------------------- #


def test_scenario_2_repeated_headers_mid_sheet_are_ignored(app, tmp_path):
    """Dado un fichero con cabeceras repetidas a mitad de la hoja
    Cuando se procesa
    Entonces esas filas se ignoran
    Y no se crean libros con títulos como "Título" o "Nivel"
    """
    rows = [
        HEADER,
        ("El pirata valiente", "I", "2", "1"),
        HEADER,
        ("Aventuras en el mar", "I", "2", "1"),
        ["titulo", "nivel", "ejemplares", "sesiones"],
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["headers_skipped"] == 2
        assert summary["books_created"] == 2
        assert summary["review"] == []

        assert _books(db.session, "titulo") is None
        assert _books(db.session, "nivel") is None


# --------------------------------------------------------------------------- #
# Escenario 3: Rótulos de sección                                             #
# --------------------------------------------------------------------------- #


def test_scenario_3_section_labels_are_separators_not_books(app, tmp_path):
    """Dado filas que contienen rótulos como "ELIGE TU PROPIA AVENTURA"
       o "TALLER DE LITERATURA"
    Cuando se procesan
    Entonces se reconocen como separadores y no como libros
    """
    rows = [
        HEADER,
        ("ELIGE TU PROPIA AVENTURA", None, None, None),
        ("TALLER DE LITERATURA", "", "", ""),
        ("El pirata valiente", "I", "2", "1"),
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["separators_skipped"] == 2
        assert summary["books_created"] == 1
        assert summary["review"] == []

        assert _books(db.session, "ELIGE TU PROPIA AVENTURA") is None
        assert _books(db.session, "TALLER DE LITERATURA") is None


# --------------------------------------------------------------------------- #
# Escenario 4: Campos de inventario no numéricos                              #
# --------------------------------------------------------------------------- #


def test_scenario_4_non_numeric_inventory_stored_as_free_text(app, tmp_path):
    """Dado filas con "11 Fotocopias", "PDF" o "12 + 6 fotocopias" en ejemplares
       Y con "PREPARAR", "4 o 5" o "5+" en sesiones
    Cuando se procesan
    Entonces esos valores se guardan como texto libre
    Y no provocan el rechazo de la fila
    """
    serial_date_like = datetime.datetime(2017, 12, 7)
    rows = [
        HEADER,
        ("a", "I", "11 Fotocopias", "PREPARAR"),
        ("b", "I", "12 + 6 fotocopias", "4 o 5"),
        ("c", "I", "PDF", "5+"),
        ("d", "I", 12, 4),
        ("e", "II", None, serial_date_like),
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["books_created"] == 5
        assert summary["errors"] == 0
        assert summary["review"] == []

        assert _books(db.session, "a").copies_note == "11 Fotocopias"
        assert _books(db.session, "a").sessions_note == "PREPARAR"
        assert _books(db.session, "b").copies_note == "12 + 6 fotocopias"
        assert _books(db.session, "b").sessions_note == "4 o 5"
        assert _books(db.session, "c").copies_note == "PDF"
        assert _books(db.session, "c").sessions_note == "5+"
        assert _books(db.session, "d").copies_note == "12"
        assert _books(db.session, "d").sessions_note == "4"
        assert _books(db.session, "e").copies_note is None
        assert _books(db.session, "e").sessions_note == "2017-12-07"


def test_scenario_4_longer_notes_are_truncated_not_rejected(app, tmp_path):
    long_note = "x" * (MAX_NOTE_LENGTH + 10)
    rows = [HEADER, ("a", "I", long_note, long_note)]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["books_created"] == 1
        assert summary["errors"] == 0
        assert _books(db.session, "a").copies_note == long_note[:MAX_NOTE_LENGTH]
        assert _books(db.session, "a").sessions_note == long_note[:MAX_NOTE_LENGTH]


# --------------------------------------------------------------------------- #
# Escenario 5: Filas no interpretables → listado de revisión manual           #
# --------------------------------------------------------------------------- #


def test_scenario_5_uninterpretable_rows_go_to_review_list(app, tmp_path):
    """Dado una fila que no permite extraer título ni nivel
    Cuando se procesa
    Entonces se añade a un listado aparte para revisión manual
    Y el resto del fichero continúa
    """
    rows = [
        HEADER,
        ("Ok Level", "I", "2", "1"),
        ("Este libro no", "III", "1", "1"),   # nivel no reconocido
        ("", "II", "2", "2"),                 # sin título
        ("Sin nivel", None, "2", "2"),        # sin nivel
        (None, None, None, None),             # fila vacía: se ignora, no revisión
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["books_created"] == 1
        assert _books(db.session, "Ok Level") is not None

        review = summary["review"]
        assert len(review) == 3
        motivos = {entry["motivo"] for entry in review}
        assert any("Nivel" in motivo for motivo in motivos)
        assert any("título" in motivo.lower() for motivo in motivos)
        assert any("Sin nivel" in entry["titulo"] for entry in review)


def test_scenario_5_review_csv_is_written_with_semicolon_separator(tmp_path):
    review = [
        {
            "line": 3,
            "titulo": "Este libro no",
            "nivel": "III",
            "ejemplares": "1",
            "sesiones": "1",
            "motivo": "Nivel 'III' no reconocido",
        },
        {
            "line": 4,
            "titulo": "",
            "nivel": "II",
            "ejemplares": "2",
            "sesiones": "2",
            "motivo": "No se puede extraer el título",
        },
    ]
    xlsx_path = tmp_path / "libros.xlsx"
    xlsx_path.write_bytes(b"")

    out = write_review_csv(xlsx_path, review)

    assert out.name == "libros_revision.csv"
    content = out.read_text(encoding="utf-8")
    lines = content.strip().splitlines()
    assert lines[0] == "linea;titulo;nivel;ejemplares;sesiones;motivo"
    assert "3;Este libro no;III;1;1;Nivel 'III' no reconocido" in lines[1]


# --------------------------------------------------------------------------- #
# Robustez estructural e idempotencia                                         #
# --------------------------------------------------------------------------- #


def test_missing_title_header_raises(app, tmp_path):
    with app.app_context():
        wb = _make_workbook([["foo", "bar"], [1, 2]])
        path = _write_xlsx(wb, tmp_path, "sin_cabecera.xlsx")
        with pytest.raises(ValidationError):
            parse_books_xlsx(path)


def test_header_without_level_column_raises(app, tmp_path):
    with app.app_context():
        wb = _make_workbook([["titulo", "ejemplares"], ["a", "2"]])
        path = _write_xlsx(wb, tmp_path, "sin_nivel.xlsx")
        with pytest.raises(ValidationError):
            parse_books_xlsx(path)


def test_reimport_is_idempotent_by_title(app, tmp_path):
    rows = [
        HEADER,
        ("El pirata valiente", "I", "2", "1"),
        ("Aventuras en el mar", "II", "3", "2"),
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        first = _import(db.session, path)
        assert first["books_created"] == 2

        second = _import(db.session, path)
        assert second["books_created"] == 0
        assert second["books_existing"] == 2
        assert second["errors"] == 0

        repo = BookRepository(db.session)
        assert len(repo.get_all(include_disabled=True)) == 2


def test_loader_isolates_a_failing_row_with_savepoint(app):
    """Una fila que falla en BD no aborta al resto (patrón BE-07 T-4)."""
    rows = [
        {"titulo": "Buen libro", "nivel": "I", "copies_note": None, "sessions_note": None, "line": 2},
        {"titulo": "Mal nivel", "nivel": "III", "copies_note": None, "sessions_note": None, "line": 3},
        {"titulo": "Otro bueno", "nivel": "II", "copies_note": "2", "sessions_note": None, "line": 4},
    ]

    with app.app_context():
        summary = BookImporter(db.session).import_rows(rows)

        assert summary["books_created"] == 2
        assert summary["errors"] == 1
        assert summary["error_details"][0]["line"] == 3
        assert _books(db.session, "Buen libro") is not None
        assert _books(db.session, "Otro bueno") is not None
        assert _books(db.session, "Mal nivel") is None


def test_duplicates_within_same_file_create_and_then_skip(app, tmp_path):
    rows = [
        HEADER,
        ("El pirata valiente", "I", "2", "1"),
        ("EL PIRATA VALIENTE", "II", "4", "2"),
    ]
    path = _write_xlsx(_make_workbook(rows), tmp_path)

    with app.app_context():
        summary = _import(db.session, path)

        assert summary["books_created"] == 1
        assert summary["books_existing"] == 1
        repo = BookRepository(db.session)
        assert len(repo.get_all(include_disabled=True)) == 1