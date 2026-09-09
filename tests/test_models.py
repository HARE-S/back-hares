import datetime
import uuid
from app.models import (
    Center,
    Section,
    Student,
    StudentSection,
    Test,
    Result,
    Book,
    ReadedBook,
)


def test_uuidv7_generation(session):
    center = Center(name="Centro Peñascal")
    session.add(center)
    session.commit()

    assert center.id is not None
    assert isinstance(center.id, uuid.UUID)
    assert center.id.version == 7


def test_center_and_section_relationship(session):
    center = Center(name="Boluetaberri")
    session.add(center)
    session.commit()

    section = Section(name="1CARMED2", center=center)
    session.add(section)
    session.commit()

    assert section.center_id == center.id
    assert len(center.sections) == 1
    assert center.sections[0].name == "1CARMED2"


def test_student_and_sections(session):
    center = Center(name="Boluetaberri")
    section = Section(name="1CARMED2", center=center)
    student = Student(
        name="STU01 - Juan Pérez",
        birth_date=datetime.date(2008, 5, 20),
        gender="M",
        academic_status="1º Grado Medio",
        sector="Mecanizado",
    )
    session.add_all([center, section, student])
    session.commit()

    enrollment = StudentSection(
        student_id=student.id,
        section_id=section.id,
        created_on=datetime.date.today(),
    )
    session.add(enrollment)
    session.commit()

    assert len(student.student_sections) == 1
    assert student.student_sections[0].section.name == "1CARMED2"
    assert len(section.student_sections) == 1
    assert student.gender == "M"
    assert student.sector == "Mecanizado"
    assert student.age is not None
    assert student.age > 0

    data = student.to_dict()
    assert data["name"] == "STU01 - Juan Pérez"
    assert data["gender"] == "M"
    assert data["age"] == student.age


def test_test_and_results(session):
    center = Center(name="Boluetaberri")
    section = Section(name="1CARMED2", center=center)
    student = Student(name="STU01")
    test = Test(code="0IF", name="Normativa piscinas", words=235)
    session.add_all([center, section, student, test])
    session.commit()

    res = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test.id,
        test_date=datetime.date(2026, 9, 8),
        time=145,
        successes=9,
        mistakes=1,
    )
    session.add(res)
    session.commit()

    assert res.id is not None
    assert res.id.version == 7
    assert res.student.name == "STU01"
    assert res.test.code == "0IF"
    assert res.time == 145
    assert len(student.results) == 1


def test_book_and_readed_books(session):
    student = Student(name="STU02")
    book = Book(book="El Lazarillo de Tormes", level="II")
    session.add_all([student, book])
    session.commit()

    readed = ReadedBook(
        student_id=student.id,
        book_id=book.id,
        start_date=datetime.date(2026, 9, 1),
        end_date=datetime.date(2026, 9, 15),
    )
    session.add(readed)
    session.commit()

    assert len(student.readed_books) == 1
    assert student.readed_books[0].book.book == "El Lazarillo de Tormes"
    assert student.readed_books[0].end_date == datetime.date(2026, 9, 15)


def test_to_dict_method(session):
    test = Test(code="0IL", name="Los cazadores de focas", words=258)
    session.add(test)
    session.commit()

    data = test.to_dict()
    assert isinstance(data["id"], str)
    assert data["code"] == "0IL"
    assert data["words"] == 258


def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
