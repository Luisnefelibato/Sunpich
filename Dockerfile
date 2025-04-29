FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Exponer el puerto que utilizará la aplicación
EXPOSE $PORT

# Comando para ejecutar la aplicación
CMD gunicorn --bind 0.0.0.0:$PORT app:app