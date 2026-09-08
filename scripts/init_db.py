import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.utils.uuidv7 import SQL_CREATE_UUIDV7_FUNCTION


def init_database():
    app = create_app()
    with app.app_context():
        print("Conectando a la base de datos...")
        try:
            # Si el motor es PostgreSQL, registramos la función uuidv7 en la base de datos
            engine_name = db.engine.dialect.name
            print(f"Dialecto de base de datos detectado: {engine_name}")

            if engine_name == "postgresql":
                print("Registrando función SQL uuidv7() en PostgreSQL...")
                db.session.execute(text(SQL_CREATE_UUIDV7_FUNCTION))
                db.session.commit()
                print("Función uuidv7() registrada exitosamente.")

            print("Creando tablas si no existen...")
            db.create_all()

            # Inspeccionar tablas creadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tablas sincronizadas ({len(tables)}): {', '.join(tables)}")

        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    init_database()
