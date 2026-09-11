"""Carga de datos de prueba anónimos (BE-05). Equivalente a `python -m app.importer`."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.importer.cli import main  # noqa: E402


if __name__ == "__main__":
    main()