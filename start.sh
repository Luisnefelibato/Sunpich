#!/bin/bash

# Script de inicio para SunPich API
echo "Iniciando SunPich API..."

# Cargar variables de entorno si existe .env
if [ -f .env ]; then
    echo "Cargando variables de entorno desde .env"
    export $(cat .env | grep -v '#' | xargs)
fi

# Usar Gunicorn como servidor WSGI
exec gunicorn --bind 0.0.0.0:${PORT:-5000} \
              --workers=2 \
              --threads=4 \
              --timeout=120 \
              --log-level=info \
              app:app
