#!/bin/bash
set -e

echo "🔄 Iniciando HARES Backend..."

# Esperar a que la BD esté lista
echo "⏳ Esperando a que PostgreSQL esté disponible..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "  PostgreSQL no está listo, esperando..."
  sleep 2
done
echo "✓ PostgreSQL está disponible"

# Inicializar BD
echo "🗄️  Inicializando base de datos..."
python scripts/init_db.py || echo "⚠️  Base de datos ya inicializada"

# Cargar datos de prueba
echo "📊 Cargando datos de prueba..."
python scripts/seed_data.py || echo "⚠️  Datos de prueba ya cargados"

# Crear usuario admin (si no existe)
echo "👤 Creando usuario admin..."
HASH='pbkdf2:sha256:1000000$xmvSphqtKHGXZGkI$b6ee1fedf5d11f804a229f4a6e770558930e043ca3c2d77cd4e87367b1ff33e6'
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  INSERT INTO users (id, email, name, lastname, password_hash, area, role, created_at, updated_at)
  VALUES (gen_random_uuid(), 'admin@grupopenascal.com', 'Admin', 'HARES', '$HASH', 'Administración', 'superadmin', NOW(), NOW())
  ON CONFLICT (email) DO NOTHING;
" 2>/dev/null && echo "✓ Admin disponible: admin@grupopenascal.com" || true

echo "✓ Inicialización completada"
echo "🚀 Iniciando servidor gunicorn..."

# Ejecutar gunicorn
exec gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
