FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para archivos de audio temporales
RUN mkdir -p /tmp/sunpich_audio && chmod 777 /tmp/sunpich_audio

# Variables de entorno por defecto
ENV PORT=5000
ENV OLLAMA_URL="https://evaenespanol.loca.lt/api/chat"
ENV MODEL_NAME="llama3:8b"
ENV TTS_VOICE="es-ES-AlvaroNeural"
ENV TTS_RATE="+0%"
ENV TTS_VOLUME="+0%"

# Exponer el puerto
EXPOSE $PORT

# Script de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
