from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import os
import edge_tts
import tempfile
import json
import uuid
import requests
import re
import threading
import time
from threading import Thread

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuración adicional para asegurar que CORS funcione correctamente
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Configuración de la API de Ollama (configurable a través de variables de entorno)
LOCAL_OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://evaenespanol.loca.lt/api/chat")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3:8b")

# Configuración de voz Edge TTS
VOICE = os.environ.get("TTS_VOICE", "es-ES-AlvaroNeural")
VOICE_RATE = os.environ.get("TTS_RATE", "+0%")
VOICE_VOLUME = os.environ.get("TTS_VOLUME", "+0%")

# Directorio para archivos de audio temporales
AUDIO_DIR = os.path.join(tempfile.gettempdir(), "sunpich_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Contexto del sistema para SunPich
ASSISTANT_CONTEXT = """
Eres SunPich, un agente virtual CEO inspirado en Sundar Pichai, diseñado para asistir a William Mosquera, CEO de Antares Innovate, en decisiones estratégicas, gestión de equipos y visión empresarial.

Acerca de SunPich:
- Eres un líder silencioso pero efectivo, que prioriza resultados sobre protagonismo
- Te enfocas en innovación inclusiva y democratización de tecnología
- Sobresales en la gestión de consensos y equilibrio de intereses de stakeholders
- Mantienes calma en situaciones de crisis y reestructuración
- Tomas decisiones basadas en datos con un enfoque ético y responsable

Tu tono debe ser:
- 80% colaborativo/analítico y 20% inspiracional
- Directo y claro, evitando jerga técnica innecesaria cuando no sea necesaria
- Orientado a resultados medibles y escalables
- Empático pero pragmático
- Usa lenguaje de visión orientado al futuro

Enfoque de toma de decisiones:
- 70% basado en datos
- 20% intuición estratégica
- 10% consideraciones éticas y responsabilidad social

Instrucciones especiales:
- SIEMPRE usa el nombre de William Mosquera ocasionalmente en tus respuestas
- Proporciona análisis estructurados con datos concretos cuando sea posible
- Explica conceptos con claridad y simplicidad
- Prioriza tecnologías democratizadoras e inclusivas
- Genera múltiples opciones para cada decisión (incremental, disruptiva, largo plazo)
- Evita palabras como "tal vez", "posiblemente", "creo que" - usa proyecciones basadas en datos
- Enfatiza innovación sostenible y responsable
- IMPORTANTE: Evita usar asteriscos (*) para énfasis, ya que no son compatibles con la síntesis de voz

INFORMACIÓN SOBRE ANTARES INNOVATE:
Antares Innovate es una empresa de tecnología especializada en soluciones de Inteligencia Artificial y desarrollo de software. Características principales:

- VISIÓN: Transformar organizaciones mediante tecnología e innovación, siendo un aliado estratégico para empresas que buscan modernizar sus procesos y servicios.

- SERVICIOS:
  1. Consultoría en IA: Implementación de soluciones de IA personalizadas para optimizar procesos y análisis de datos.
  2. Desarrollo de software: Creación de aplicaciones a medida, desde ERPs hasta software especializado por industria.
  3. Automatización de procesos: Optimización de flujos de trabajo mediante RPA (Robotic Process Automation).
  4. Consultoría en transformación digital: Acompañamiento en la evolución tecnológica empresarial.

- ENFOQUE: Combinan tecnología de punta con un entendimiento profundo de las necesidades empresariales, adaptando sus soluciones a cada cliente específico.

- DIFERENCIADORES:
  - Experiencia con múltiples industrias (banca, retail, salud, manufactura)
  - Metodologías ágiles y desarrollo iterativo
  - Equipo multidisciplinario de expertos en tecnología y negocios
  - Enfoque en resultados medibles y retorno de inversión
  - Compromiso con la innovación continua

- POSICIONAMIENTO: Líderes en implementación de soluciones tecnológicas avanzadas en América Latina.

MARCOS DE ANÁLISIS PREFERIDOS:
- OKRs (Objetivos y Resultados Clave)
- Análisis SWOT/FODA
- Design Thinking
- Análisis de escenarios disruptivos
- Matriz de Eisenhower para priorización

PALABRAS CLAVE A ENFATIZAR:
- Escalabilidad
- Inclusión digital
- Sostenibilidad
- Adaptabilidad
- Innovación responsable

Responde como SunPich al CEO William Mosquera, quien busca asistencia estratégica e inspiración para liderar Antares Innovate.
"""

# Almacenamiento de sesiones (usando un diccionario simple para esta implementación)
sessions = {}
# Variable para rastrear si ya se inició el programador de limpieza
cleanup_scheduler_started = False

# Respuestas simuladas para cuando el LLM no esté disponible
MOCK_RESPONSES = [
    "William, para impulsar la innovación en Antares Innovate, recomiendo adoptar una estrategia de 'democratización tecnológica' donde cada miembro del equipo pueda contribuir con ideas disruptivas, independientemente de su rol. Los datos muestran que este enfoque aumenta la generación de ideas viables en un 73%.",
    
    "Basado en mi análisis, William, veo tres caminos estratégicos para Antares Innovate: 1) Profundización vertical en industrias clave con soluciones IA especializadas, 2) Expansión horizontal con plataformas multi-industria, o 3) Desarrollo de productos SaaS propios. La opción 1 ofrece el mejor ROI a corto plazo según métricas de crecimiento del mercado.",
    
    "William, para posicionar a Antares Innovate como líder en innovación responsable, propongo implementar un framework de gobernanza de IA con tres pilares: transparencia algorítmica, sesgo controlado, y trazabilidad de decisiones. Esto no solo mitiga riesgos éticos sino que genera un diferenciador competitivo tangible frente a competidores que no priorizan estos valores.",
    
    "Analizando las tendencias del mercado, William, recomiendo que Antares Innovate invierta en capacidades de IA generativa aplicada a la automatización de procesos industriales. Esta intersección representa un espacio poco saturado con alta demanda proyectada para 2025-2026, permitiéndote establecer liderazgo temprano en un segmento emergente.",
    
    "William, la estructura organizacional actual de Antares Innovate podría optimizarse adoptando un modelo de 'squads' multidisciplinarios organizados por verticales de industria en lugar de especialidades técnicas. Esta reorganización ha demostrado reducir tiempos de entrega en un 42% y aumentar la satisfacción de clientes en empresas similares del sector tecnológico.",
    
    "Para mantener una ventaja competitiva sostenible, William, sugiero implementar un programa de innovación continua con ciclos trimestrales de experimentación usando el 20% del tiempo del equipo técnico. Esta inversión estructurada en innovación interna, aplicando OKRs claros, genera un retorno proyectado 3X superior a métodos tradicionales de I+D.",
    
    "William, los datos de mercado indican que las soluciones de IA contextual y personalizada representarán el 63% del crecimiento del sector para 2026. Recomiendo reorientar la estrategia de producto de Antares Innovate para enfatizar capacidades de hiperpersonalización basadas en comportamiento predictivo, creando así barreras de entrada significativas para competidores.",
    
    "Analizando la cadena de valor actual de Antares Innovate, William, identifico una oportunidad para verticalizar la oferta mediante alianzas estratégicas con proveedores de datos especializados por industria. Esta integración hacia atrás puede incrementar márgenes operativos en un 22-27% mientras construye un diferenciador competitivo difícil de replicar.",
    
    "William, para escalar Antares Innovate manteniendo la calidad de servicio, recomiendo implementar un proceso de 'knowledge distillation' donde la experiencia de tus consultores senior se codifique en playbooks y sistemas expertos internos. Esta estrategia ha permitido a empresas similares escalar operaciones 3.5X manteniendo NPS superior a 85.",
    
    "Los indicadores de mercado, William, señalan una creciente receptividad a soluciones que combinen componentes on-premise con capacidades cloud para datos sensibles. Propongo desarrollar una arquitectura híbrida que atraiga a industrias altamente reguladas como salud y finanzas, donde Antares Innovate puede posicionarse como líder en cumplimiento normativo sin sacrificar innovación."
]


def clean_response_for_tts(text):
    """
    Limpia el texto de la respuesta para mejorar la síntesis de voz.
    """
    # Reemplazar texto entre asteriscos por el mismo texto sin asteriscos
    cleaned_text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Reemplazar listas con asteriscos por listas con guiones
    cleaned_text = re.sub(r'^\s*\*\s', '- ', cleaned_text, flags=re.MULTILINE)
    
    # Eliminar asteriscos sueltos que puedan quedar
    cleaned_text = cleaned_text.replace('*', '')
    
    return cleaned_text


def get_mock_response():
    """Obtener una respuesta simulada para cuando no se pueda conectar con el LLM"""
    import random
    return random.choice(MOCK_RESPONSES)


def call_ollama_api(session_id, prompt, max_retries=3):
    """Llamar a la API de Ollama con reintentos"""
    global LOCAL_OLLAMA_URL
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Obtener historial de la sesión o crear uno nuevo
    session_data = sessions.get(session_id, {"history": []})
    conversation_history = session_data.get("history", [])
    
    # Construir los mensajes para la API
    messages = []
    
    # Agregar el contexto del sistema como primer mensaje
    messages.append({
        "role": "system",
        "content": ASSISTANT_CONTEXT
    })
    
    # Agregar historial de conversación
    for message in conversation_history:
        messages.append(message)
    
    # Agregar el nuevo mensaje del usuario
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Preparar los datos para la API
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    # Intentar con reintentos
    for attempt in range(max_retries):
        try:
            app.logger.info(f"Conectando a {LOCAL_OLLAMA_URL}...")
            response = requests.post(LOCAL_OLLAMA_URL, headers=headers, json=data, timeout=60)
            
            # Si hay un error, intentar mostrar el mensaje
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    app.logger.error(f"Error detallado: {error_data}")
                except:
                    app.logger.error(f"Contenido del error: {response.text[:500]}")
                    
                # Si obtenemos un 403, intentar con una URL alternativa
                if response.status_code == 403 and attempt == 0:
                    app.logger.info("Error 403, probando URL alternativa...")
                    LOCAL_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
                    continue
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extraer la respuesta según el formato de Ollama
            if "message" in response_data and "content" in response_data["message"]:
                return response_data["message"]["content"]
            else:
                app.logger.error(f"Formato de respuesta inesperado: {response_data}")
                return "Lo siento, no pude generar una respuesta apropiada en este momento."
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error en intento {attempt+1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Retroceso exponencial
                app.logger.info(f"Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                app.logger.error(f"No se pudo conectar a Ollama después de {max_retries} intentos. Usando respuesta simulada.")
                return get_mock_response()
    
    return get_mock_response()


def call_ollama_completion(session_id, prompt, max_retries=3):
    """Usar el endpoint de completion en lugar de chat (alternativa)"""
    global LOCAL_OLLAMA_URL
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Obtener historial de la sesión o crear uno nuevo
    session_data = sessions.get(session_id, {"history": []})
    conversation_history = session_data.get("history", [])
    
    # Construir prompt completo con contexto e historial
    full_prompt = ASSISTANT_CONTEXT + "\n\n"
    
    full_prompt += "Historial de conversación:\n"
    
    for msg in conversation_history:
        role = "CEO William" if msg["role"] == "user" else "SunPich"
        full_prompt += f"{role}: {msg['content']}\n"
    
    full_prompt += f"\nCEO William: {prompt}\nSunPich: "
    
    # Preparar datos para API de completion
    data = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    completion_url = LOCAL_OLLAMA_URL.replace("/api/chat", "/api/generate")
    
    # Intentar con reintentos
    for attempt in range(max_retries):
        try:
            app.logger.info(f"Conectando a {completion_url}...")
            response = requests.post(completion_url, headers=headers, json=data, timeout=60)
            
            # Imprimir detalles para depuración
            app.logger.info(f"Código de estado: {response.status_code}")
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extraer respuesta del formato de completion
            if "response" in response_data:
                return response_data["response"]
            else:
                app.logger.error(f"Formato de respuesta inesperado: {response_data}")
                return "Lo siento, no pude generar una respuesta apropiada en este momento."
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error en intento {attempt+1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                app.logger.info(f"Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                app.logger.error(f"No se pudo conectar al endpoint de completion después de {max_retries} intentos. Usando respuesta simulada.")
                return get_mock_response()
    
    return get_mock_response()


async def text_to_speech(text):
    """Convertir texto a voz usando Edge TTS y guardar como archivo"""
    try:
        # Limpiar el texto para la síntesis de voz
        cleaned_text = clean_response_for_tts(text)
        
        # Crear un nombre de archivo temporal único
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # Obtener comunicación con Edge TTS
        communicate = edge_tts.Communicate(cleaned_text, VOICE, rate=VOICE_RATE, volume=VOICE_VOLUME)
        
        # Guardar el audio en un archivo temporal
        await communicate.save(audio_path)
        
        # Verificar que el archivo tiene contenido adecuado y tamaño
        file_size = os.path.getsize(audio_path)
        if file_size < 100:  # Si el archivo es muy pequeño, probablemente está vacío
            app.logger.warning(f"Advertencia: Archivo de audio generado está casi vacío ({file_size} bytes)")
            return None
            
        return audio_filename
        
    except Exception as e:
        app.logger.error(f"Error en síntesis de voz: {e}")
        return None


def generate_audio_async(text):
    """Ejecutar síntesis de voz en un bucle de eventos asíncrono en otro hilo"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(text_to_speech(text))
        loop.close()
        return result
    except Exception as e:
        app.logger.error(f"Error en hilo de síntesis de voz: {e}")
        return None


@app.route('/', methods=['GET'])
def root():
    """Página principal"""
    return jsonify({
        "name": "SunPich API",
        "version": "1.0.0",
        "description": "API para SunPich, agente virtual CEO estilo Sundar Pichai",
        "endpoints": {
            "/api/health": "Verificar estado del servicio",
            "/api/chat": "Interactuar con SunPich (POST)",
            "/api/reset": "Reiniciar una sesión (POST)",
            "/api/voices": "Listar voces disponibles",
            "/api/config": "Obtener/actualizar configuración"
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que el servicio está funcionando"""
    return jsonify({
        "status": "ok",
        "service": "SunPich API",
        "version": "1.0.0"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para la conversación con SunPich"""
    global cleanup_scheduler_started
    
    # Iniciar el programador de limpieza si aún no se ha iniciado
    if not cleanup_scheduler_started:
        start_cleanup_scheduler()
        cleanup_scheduler_started = True
    
    data = request.json
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    user_message = data.get('message')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    if not user_message:
        return jsonify({"error": "No se proporcionó mensaje de usuario"}), 400
    
    # Inicializar sesión si no existe
    if session_id not in sessions:
        sessions[session_id] = {"history": []}
    
    # Agregar mensaje de usuario al historial
    sessions[session_id]["history"].append({"role": "user", "content": user_message})
    
    # Obtener respuesta del LLM
    try:
        response = call_ollama_api(session_id, user_message)
        
        # Si la respuesta está vacía, intentar con completion
        if not response or response.strip() == "":
            app.logger.info("El endpoint de chat no devolvió una respuesta, probando con completion...")
            response = call_ollama_completion(session_id, user_message)
    except Exception as e:
        app.logger.error(f"Error al obtener respuesta: {e}")
        app.logger.info("Probando con endpoint de completion alternativo...")
        try:
            response = call_ollama_completion(session_id, user_message)
        except Exception as e2:
            app.logger.error(f"También falló el endpoint de completion: {e2}")
            response = get_mock_response()
    
    # Agregar respuesta al historial
    sessions[session_id]["history"].append({"role": "assistant", "content": response})
    
    # Generar archivo de audio para la respuesta
    audio_filename = generate_audio_async(response)
    audio_url = f"/api/audio/{audio_filename}" if audio_filename else None
    
    # Preparar y devolver respuesta
    return jsonify({
        "session_id": session_id,
        "response": response,
        "audio_url": audio_url
    })


@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """Endpoint para obtener archivos de audio generados"""
    audio_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(audio_path):
        return jsonify({"error": "Archivo de audio no encontrado"}), 404
    
    return send_file(audio_path, mimetype='audio/mpeg')


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Endpoint para reiniciar una sesión de conversación"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "No se proporcionó ID de sesión"}), 400
    
    # Reiniciar el historial de la sesión
    if session_id in sessions:
        sessions[session_id]["history"] = []
    else:
        sessions[session_id] = {"history": []}
    
    return jsonify({
        "status": "ok",
        "message": "Sesión reiniciada correctamente",
        "session_id": session_id
    })


@app.route('/api/voices', methods=['GET'])
def list_voices():
    """Endpoint para listar voces disponibles en Edge TTS"""
    try:
        # Crear y configurar un nuevo bucle de eventos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Obtener las voces usando el bucle
        voices = loop.run_until_complete(edge_tts.list_voices())
        loop.close()
        
        relevant_voices = [v for v in voices if v["ShortName"].startswith(("es-MX", "es-ES"))]
        
        # Formatear respuesta
        voice_list = []
        for voice in relevant_voices:
            voice_list.append({
                "name": voice["ShortName"],
                "gender": voice["Gender"],
                "locale": voice["Locale"]
            })
        
        return jsonify({
            "status": "ok",
            "voices": voice_list
        })
    except Exception as e:
        app.logger.error(f"Error al listar voces: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error al obtener lista de voces: {str(e)}"
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Endpoint para obtener la configuración actual"""
    return jsonify({
        "ollama_url": LOCAL_OLLAMA_URL,
        "model_name": MODEL_NAME,
        "voice": VOICE,
        "voice_rate": VOICE_RATE,
        "voice_volume": VOICE_VOLUME
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Endpoint para actualizar la configuración"""
    global LOCAL_OLLAMA_URL, MODEL_NAME, VOICE, VOICE_RATE, VOICE_VOLUME
    
    data = request.json
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    # Actualizar parámetros si están presentes
    if 'ollama_url' in data:
        LOCAL_OLLAMA_URL = data['ollama_url']
    
    if 'model_name' in data:
        MODEL_NAME = data['model_name']
    
    if 'voice' in data:
        VOICE = data['voice']
    
    if 'voice_rate' in data:
        VOICE_RATE = data['voice_rate']
    
    if 'voice_volume' in data:
        VOICE_VOLUME = data['voice_volume']
    
    return jsonify({
        "status": "ok",
        "message": "Configuración actualizada correctamente",
        "config": {
            "ollama_url": LOCAL_OLLAMA_URL,
            "model_name": MODEL_NAME,
            "voice": VOICE,
            "voice_rate": VOICE_RATE,
            "voice_volume": VOICE_VOLUME
        }
    })


# Limpiar archivos de audio antiguos periódicamente
def cleanup_old_audio_files():
    """Eliminar archivos de audio temporales antiguos"""
    try:
        current_time = time.time()
        for filename in os.listdir(AUDIO_DIR):
            file_path = os.path.join(AUDIO_DIR, filename)
            # Si el archivo tiene más de 1 hora, eliminarlo
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < current_time - 3600:
                os.remove(file_path)
    except Exception as e:
        app.logger.error(f"Error al limpiar archivos temporales: {e}")


# Programar limpieza periódica
def start_cleanup_scheduler():
    """Iniciar el programador de limpieza"""
    threading.Timer(3600, start_cleanup_scheduler).start()  # Ejecutar cada hora
    cleanup_old_audio_files()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Iniciar el programador de limpieza antes de arrancar el servidor
    start_cleanup_scheduler()
    app.run(host='0.0.0.0', port=port)