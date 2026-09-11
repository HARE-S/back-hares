import argparse
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.services.seed_service import SeedService


def main():
    parser = argparse.ArgumentParser(
        description="Cargar datos de prueba anónimos en la base de datos (BE-05)."
    )
    parser.add_argument(
        "--students",
        default=SeedService.DEFAULT_STUDENTS_CSV,
        help="Ruta al CSV de alumnado anónimo (por defecto: data/seeds/import_data.csv)",
    )
    parser.add_argument(
        "--tests",
        default=SeedService.DEFAULT_TESTS_CSV,
        help="Ruta al CSV del catálogo de pruebas (por defecto: data/seeds/tests.csv)",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        service = SeedService(db.session)
        try:
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
                # Alumnos
                f"  Alumnos: {students['total']} filas "
                f"({students['students_created']} creados, {students['students_updated']} actualizados)\n"
                f"  Centros: {students['centers_created']} creados\n"
                f"  Secciones: {students['sections_created']} creadas\n"
                f"  Matrículas: {students['enrollments_created']} creadas\n"
                # Pruebas
                f"  Pruebas: {tests['total']} procesadas "
                f"({tests['created']} creadas, {tests['updated']} actualizadas)\n"
                # Libros
                f"  Libros: {books['total']} en catálogo ({books['created']} creados, {books['existing']} ya existían)\n"
                # Resultados
                f"  Resultados sintéticos: {results['created']} creados, "
                f"{results['skipped']} ya existían (mínimo {results['min_results_per_student']} por alumno)"
            )
        except Exception as e:
            print(f"Error durante la carga de datos: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()