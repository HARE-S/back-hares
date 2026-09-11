"""Implementación del CLI de carga de datos de prueba anónimos (BE-05).

Usado por `python -m app.importer` y por `scripts/seed_data.py`. La lógica
de impresión y de ejecución vive en un único lugar para no divergir.
"""
import argparse

from app import create_app
from app.extensions import db
from app.services.seed_service import SeedService


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cargar datos de prueba anónimos en la base de datos (BE-05)."
    )
    parser.add_argument(
        "--students",
        default=SeedService.DEFAULT_STUDENTS_CSV,
        help="Ruta al CSV de alumnado anónimo "
        f"(por defecto: {SeedService.DEFAULT_STUDENTS_CSV})",
    )
    parser.add_argument(
        "--tests",
        default=SeedService.DEFAULT_TESTS_CSV,
        help="Ruta al CSV del catálogo de pruebas "
        f"(por defecto: {SeedService.DEFAULT_TESTS_CSV})",
    )
    return parser


def run(args: argparse.Namespace) -> None:
    app = create_app()
    with app.app_context():
        service = SeedService(db.session)
        summary = service.seed(
            students_csv_path=args.students,
            tests_csv_path=args.tests,
        )

        students = summary["students"]
        tests = summary["tests"]
        books = summary["books"]
        results = summary["results"]

        print(
            "Carga de datos de prueba completada.\n"
            f"  Alumnos: {students['total']} filas "
            f"({students['students_created']} creados, "
            f"{students['students_updated']} actualizados)\n"
            f"  Centros: {students['centers_created']} creados\n"
            f"  Secciones: {students['sections_created']} creadas\n"
            f"  Matrículas: {students['enrollments_created']} creadas\n"
            f"  Pruebas: {tests['total']} procesadas "
            f"({tests['created']} creadas, {tests['updated']} actualizadas)\n"
            f"  Libros: {books['total']} en catálogo "
            f"({books['created']} creados, {books['existing']} ya existían)\n"
            f"  Resultados sintéticos: {results['created']} creados, "
            f"{results['skipped']} ya existían "
            f"(mínimo {results['min_results_per_student']} por alumno)"
        )


def main() -> None:
    run(build_arg_parser().parse_args())