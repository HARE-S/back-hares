"""Tests para métricas de par (funcional/literario)."""

import uuid
import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.center import Center, Section
from app.models.student import Student, StudentSection
from app.models.test import Test, Result


@pytest.fixture
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session


def test_student_pair_series_complete(client, session):
    """Serie completa: alumno con pares funcional+literario para I, A."""
    center = Center(name="Test Center")
    section = Section(name="Test Section", center_id=center.id)
    student = Student(name="Test Student")
    test_if = Test(code="1IF", name="Test I-F", words=100, course=1, test_letter="I", type="F")
    test_il = Test(code="1IL", name="Test I-L", words=100, course=1, test_letter="I", type="L")
    test_af = Test(code="1AF", name="Test A-F", words=100, course=1, test_letter="A", type="F")
    test_al = Test(code="1AL", name="Test A-L", words=100, course=1, test_letter="A", type="L")

    session.add_all([center, section, student, test_if, test_il, test_af, test_al])
    session.flush()

    StudentSection(student_id=student.id, section_id=section.id)

    # 100 palabras, 60 segundos = 100 ppm
    # 18 aciertos, 2 errores = (18 - 1) / 20 * 100 = 85%
    # vef = 100 * 0.85 = 85.0
    result_if = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_if.id,
        test_date="2026-03-10",
        time=60,
        successes=18,
        mistakes=2,
    )
    result_il = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_il.id,
        test_date="2026-03-11",
        time=60,
        successes=18,
        mistakes=2,
    )
    result_af = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_af.id,
        test_date="2026-03-12",
        time=60,
        successes=18,
        mistakes=2,
    )
    result_al = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_al.id,
        test_date="2026-03-13",
        time=60,
        successes=18,
        mistakes=2,
    )
    session.add_all([result_if, result_il, result_af, result_al])
    session.commit()

    headers = {"X-User-Role": "tutor"}
    resp = client.get(f"/api/v1/students/{student.id}/pair-series", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert len(data["pairs"]) == 2  # I y A

    # Pair I: ambos tipos presentes, vef = 85.0 cada uno
    pair_i = data["pairs"][0]
    assert pair_i["test_letter"] == "I"
    assert pair_i["vef_functional"] == 85.0
    assert pair_i["vef_literary"] == 85.0
    assert pair_i["mean"] == 85.0
    assert pair_i["difference"] == 0.0
    assert pair_i["is_complete"] is True


def test_student_pair_series_incomplete(client, session):
    """Serie incompleta: alumno sin el tipo literario de la prueba."""
    center = Center(name="Test Center")
    section = Section(name="Test Section", center_id=center.id)
    student = Student(name="Test Student")
    test_if = Test(code="1IF", name="Test I-F", words=100, course=1, test_letter="I", type="F")

    session.add_all([center, section, student, test_if])
    session.flush()

    StudentSection(student_id=student.id, section_id=section.id)

    result_if = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_if.id,
        test_date="2026-03-10",
        time=60,
        successes=18,
        mistakes=2,
    )
    session.add(result_if)
    session.commit()

    headers = {"X-User-Role": "tutor"}
    resp = client.get(f"/api/v1/students/{student.id}/pair-series", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert len(data["pairs"]) == 1

    pair_i = data["pairs"][0]
    assert pair_i["vef_functional"] == 85.0
    assert pair_i["vef_literary"] is None
    assert pair_i["mean"] == 85.0  # media de lo que hay
    assert pair_i["is_complete"] is False


def test_student_without_results(client, session):
    """Alumno sin resultados devuelve serie vacía."""
    student = Student(name="Test Student")
    session.add(student)
    session.commit()

    headers = {"X-User-Role": "tutor"}
    resp = client.get(f"/api/v1/students/{student.id}/pair-series", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["pairs"] == []


def test_student_progress_transitions(client, session):
    """Progresión individual con transiciones I-A, A-B."""
    center = Center(name="Test Center")
    section = Section(name="Test Section", center_id=center.id)
    student = Student(name="Test Student")

    # Crear 3 pruebas: I, A, B con pares completos
    tests = []
    for letter in ["I", "A", "B"]:
        for test_type in ["F", "L"]:
            code = f"1{letter}{test_type}"
            test = Test(
                code=code,
                name=f"Test {letter}-{test_type}",
                words=100,
                course=1,
                test_letter=letter,
                type=test_type,
            )
            tests.append(test)
            session.add(test)

    session.add_all([center, section, student])
    session.flush()
    StudentSection(student_id=student.id, section_id=section.id)

    # Resultados: I=100, A=110, B=95 (mejora I-A, empeora A-B)
    vefs = {"I": 100.0, "A": 110.0, "B": 95.0}
    date_counter = 0
    for test in tests:
        result = Result(
            student_id=student.id,
            section_id=section.id,
            test_id=test.id,
            test_date=f"2026-03-{10 + date_counter:02d}",
            time=60,
            successes=20,
            mistakes=0,
        )
        # Simular el vef deseado ajustando successes
        # vef = ppm * comprehension = (100/min) * (success/20)*100 = vef deseado
        result.successes = int((vefs[test.test_letter] / 100) * 20)
        session.add(result)
        date_counter += 1

    session.commit()

    headers = {"X-User-Role": "tutor"}
    resp = client.get(f"/api/v1/students/{student.id}/progress", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert len(data["transitions"]) == 2  # I-A y A-B
    assert data["transitions"][0]["transition"] == "I-A"
    assert data["transitions"][0]["improved"] is True  # 110 > 100
    assert data["transitions"][1]["transition"] == "A-B"
    assert data["transitions"][1]["improved"] is False  # 95 < 110
    assert data["global_progress"] is not None


def test_transition_without_data_returns_none(client, session):
    """Transición sin datos en ambas pruebas devuelve None, nunca 0."""
    center = Center(name="Test Center")
    section = Section(name="Test Section", center_id=center.id)
    student = Student(name="Test Student")

    # Solo prueba I, no hay A ni B
    test_if = Test(code="1IF", name="Test I-F", words=100, course=1, test_letter="I", type="F")
    test_il = Test(code="1IL", name="Test I-L", words=100, course=1, test_letter="I", type="L")

    session.add_all([center, section, student, test_if, test_il])
    session.flush()
    StudentSection(student_id=student.id, section_id=section.id)

    result_if = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_if.id,
        test_date="2026-03-10",
        time=60,
        successes=18,
        mistakes=2,
    )
    result_il = Result(
        student_id=student.id,
        section_id=section.id,
        test_id=test_il.id,
        test_date="2026-03-11",
        time=60,
        successes=18,
        mistakes=2,
    )
    session.add_all([result_if, result_il])
    session.commit()

    headers = {"X-User-Role": "tutor"}
    resp = client.get(f"/api/v1/students/{student.id}/progress", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    # No hay transiciones porque solo hay prueba I
    assert data["transitions"] == []
    assert data["global_progress"] is None
    assert data["measured_span"] is None
