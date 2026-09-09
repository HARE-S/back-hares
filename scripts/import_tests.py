import argparse
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.services.catalog_service import CatalogService


def main():
    parser = argparse.ArgumentParser(
        description="Importar catálogo de pruebas de comprensión lectora desde archivo CSV (BE-12)."
    )
    parser.add_argument(
        "--file",
        "-f",
        default="data/seeds/tests.csv",
        help="Ruta al archivo CSV con las pruebas (por defecto: data/seeds/tests.csv)",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        csv_path = args.file
        if not os.path.isfile(csv_path):
            print(f"Error: no se encontró el archivo '{csv_path}'", file=sys.stderr)
            sys.exit(1)

        print(f"Iniciando importación desde: {csv_path}...")
        service = CatalogService(db.session)
        try:
            result = service.import_tests_from_csv(csv_path)
            print(
                f"Importación completada con éxito: "
                f"{result['total']} pruebas procesadas "
                f"({result['created']} creadas, {result['updated']} actualizadas)."
            )
        except Exception as e:
            print(f"Error durante la importación: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
