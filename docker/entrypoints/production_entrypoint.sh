#!/bin/bash
set -e

echo "🚀 Iniciando PixelHub..."

# 1. Espera a la base de datos usando Python (esto funcionaba bien)
echo "⏳ Esperando a la DB..."
python -c "import socket, time, sys; host='${MARIADB_HOSTNAME:-db}'; port=${MARIADB_PORT:-3306}; [sys.exit(0) for _ in iter(lambda: socket.create_connection((host, port), timeout=1).close(), None) if time.sleep(1) or True]" || exit 1

# 2. Migraciones y Seeders
echo "🔄 Ejecutando migraciones..."
flask db upgrade

echo "🌱 Ejecutando Seeder original..."
# Si falla, no detiene el script (|| true)
python -m rosemary db:seed || true

# 4. Arrancar servidor
echo "🚀 Arrancando servidor..."
exec gunicorn --bind 0.0.0.0:5000 app:app
