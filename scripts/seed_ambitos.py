"""Script para sembrar los Ámbitos (Centros) del ecosistema Peñascal."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.center import Center

PENASCAL_AMBITOS = [
    "Belategi",
    "Bolueta",
    "Boluetabarri-Climatización",
    "Boluetabarri-Hostelería",
    "Boluetabarri-Madera",
    "Boluetabarri-Moda",
    "Markina",
    "Montaño",
    "Tolosa",
]


def seed_ambitos():
    """Crea los centros/ámbitos canónicos de Peñascal si no existen."""
    app = create_app()
    with app.app_context():
        created = 0
        for name in PENASCAL_AMBITOS:
            existing = Center.query.filter_by(name=name, disabled_at=None).first()
            if not existing:
                center = Center(name=name, origin="manual")
                db.session.add(center)
                created += 1
        db.session.commit()
        print(f"✅ Ámbitos de Peñascal sincronizados ({created} nuevos creados).")


if __name__ == "__main__":
    seed_ambitos()
