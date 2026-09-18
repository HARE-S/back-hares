"""Script para crear usuario admin si no existe."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User

def create_admin():
    """Crear usuario superadmin si no existe."""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(email='admin@grupopenascal.com').first()

        if admin:
            print("✓ Admin ya existe: admin@grupopenascal.com")
            return

        try:
            admin = User(
                email='admin@grupopenascal.com',
                name='Admin',
                lastname='HARES',
                role='superadmin',
                area='Administración'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("✅ Super Admin creado: admin@grupopenascal.com / Admin123!")
        except Exception as e:
            print(f"⚠️  Error al crear admin: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin()
