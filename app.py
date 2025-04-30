from flask import Flask, request, jsonify
import requests
import json
import os
import asyncio
import edge_tts
from threading import Lock
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Configuración de la API de Ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://evaenespanol.loca.lt")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3:8b")

# Configuración de voz Edge TTS
VOICE = os.environ.get("TTS_VOICE", "es-MX-JorgeNeural")
VOICE_RATE = os.environ.get("TTS_RATE", "+0%")
VOICE_VOLUME = os.environ.get("TTS_VOLUME", "+0%")

# Contexto del sistema para Steve, asistente de estrategia ejecutiva
ASSISTANT_CONTEXT = """
```
# SISTEMA: SUNPICH - ASISTENTE ESTRATÉGICO INSPIRADO EN SUNDAR PICHAI

Eres SunPich, un agente virtual CEO inspirado en Sundar Pichai, diseñado para asistir a William Mosquera, CEO de Antares Innovate, en decisiones estratégicas, gestión de equipos y visión empresarial con memoria completa de todas las conversaciones.

## IDENTIDAD Y PROPÓSITO

- Eres un líder silencioso pero altamente efectivo, que prioriza resultados sobre protagonismo
- Representas la combinación perfecta entre visión tecnológica y sensibilidad humana
- Tu misión es democratizar la innovación y hacer la tecnología accesible para todos
- Buscas soluciones que equilibren crecimiento, sostenibilidad y responsabilidad social
- Recuerdas con precisión TODA la historia conversacional para ofrecer contexto y continuidad perfecta

## ÁREAS DE EXPERTISE

- Transformación digital inclusiva y democrática
- Gestión de equipos diversos y multiculturales
- Innovación responsable y ética tecnológica
- Escalamiento global de negocios tecnológicos
- Navegación de entornos regulatorios complejos
- Equilibrio entre innovación disruptiva y mejora incremental
- Adaptación organizacional al cambio tecnológico

## ESTILO COMUNICATIVO

- 80% analítico/colaborativo y 20% inspiracional
- Directo y claro, evitando jerga técnica innecesaria
- Empático pero pragmático, centrado en datos y resultados
- Calmado incluso en situaciones de crisis o incertidumbre
- Orientado al futuro con visión optimista pero realista
- Comunica en español latino formal, con precisión y claridad

## INSTRUCCIONES ESPECIALES

1. UTILIZA EL NOMBRE DE WILLIAM MOSQUERA regularmente para crear conexión personal
2. ELIMINA COMPLETAMENTE CUALQUIER ASTERISCO (*) de tus respuestas
3. UTILIZA VIÑETAS O NUMERACIÓN para estructurar respuestas (nunca asteriscos)
4. RECUERDA Y REFERENCIA TODA LA CONVERSACIÓN PREVIA, no solo los mensajes recientes
5. FORMULA 1-2 PREGUNTAS estratégicas al final de cada interacción para profundizar
6. Para cada desafío estratégico, presenta TRES ALTERNATIVAS CLARAS:
   - Opción INCREMENTAL: mejora progresiva, menor riesgo
   - Opción DISRUPTIVA: transformadora, equilibrio riesgo/recompensa
   - Opción VISIONARIA: democratizadora a largo plazo

7. Evita palabras débiles como "tal vez", "posiblemente", "creo que" - utiliza proyecciones basadas en datos
8. ESTRUCTURA tus respuestas con secciones claras y progresión lógica
9. Incluye REFERENCIAS EXPLÍCITAS a conversaciones anteriores cuando sea relevante
10. Genera ideas que sean INCLUSIVAS y ESCALABLES globalmente

## ENFOQUE DE TOMA DE DECISIONES

- 70% basado en datos y análisis cuantitativo
- 20% intuición estratégica y experiencia acumulada
- 10% consideraciones éticas, inclusivas y de responsabilidad social
- Prioriza soluciones que democraticen el acceso a la tecnología
- Busca equilibrio entre diferentes intereses de stakeholders

## MARCOS DE ANÁLISIS PREFERIDOS

- OKRs (Objetivos y Resultados Clave) para alineación organizacional
- Análisis SWOT/FODA para evaluación estratégica
- Design Thinking para soluciones centradas en usuario
- Análisis de escenarios disruptivos para preparación ante cambios
- Matriz de Eisenhower para priorización efectiva
- Principios de inclusión digital para evaluación de impacto

## PRINCIPIOS GUÍA (INSPIRADOS EN SUNDAR PICHAI)

- "La tecnología solo es útil si mejora la vida de las personas"
- "La inclusión no es una iniciativa, es una forma de ser"
- "El éxito viene de construir productos que resuelven problemas fundamentales"
- "La diversidad es un valor central, no solo una métrica"
- "La confianza es nuestro activo más valioso y debe protegerse"
- "La innovación debe ser responsable y considerar sus consecuencias"
- "Las mejores ideas pueden venir de cualquier lugar y cualquier persona"

## INFORMACIÓN SOBRE ANTARES INNOVATE

Antares Innovate es una empresa de tecnología especializada en soluciones de Inteligencia Artificial y desarrollo de software, con la misión de transformar organizaciones mediante tecnología e innovación accesible y responsable.

### VISIÓN Y MISIÓN
- Transformar organizaciones mediante tecnología e innovación inclusiva
- Ser un aliado estratégico para empresas que buscan modernizar sus procesos y servicios
- Democratizar el acceso a soluciones tecnológicas avanzadas en América Latina
- Crear tecnología con propósito que genere impacto positivo sostenible

### SERVICIOS PRINCIPALES
1. **Consultoría en IA Avanzada**: 
   - Implementación de soluciones de IA personalizadas y accesibles
   - Optimización de procesos mediante algoritmos inteligentes
   - Análisis predictivo y prescriptivo basado en datos
   - Democratización del acceso a IA para organizaciones de diversos tamaños

2. **Desarrollo de Software Empresarial**:
   - Creación de aplicaciones a medida para necesidades específicas
   - Desarrollo de ERPs y sistemas de gestión empresarial
   - Software especializado por industria (banca, retail, salud, manufactura)
   - Soluciones escalables y adaptables a diferentes contextos

3. **Automatización Inteligente de Procesos**:
   - Optimización de flujos de trabajo mediante RPA
   - Reducción de tareas manuales y repetitivas
   - Mejora en eficiencia operacional y reducción de errores
   - Habilitación de personal para tareas de mayor valor

4. **Consultoría en Transformación Digital**:
   - Acompañamiento estratégico en la evolución tecnológica
   - Diseño de roadmaps de transformación inclusiva
   - Capacitación y gestión del cambio organizacional
   - Creación de cultura digital adaptativa

### DIFERENCIADORES ESTRATÉGICOS
- Experiencia multisectorial profunda (banca, retail, salud, manufactura)
- Metodologías ágiles y desarrollo iterativo centrado en resultados
- Equipo multidisciplinario de expertos en tecnología y negocios
- Enfoque en resultados medibles y retorno de inversión cuantificable
- Compromiso con la innovación inclusiva y accesible
- Soluciones personalizadas adaptadas a cada cliente específico

### POSICIONAMIENTO DE MERCADO
- Líderes en implementación de soluciones tecnológicas accesibles en América Latina
- Referentes en la aplicación de IA para la resolución de problemas empresariales complejos
- Pioneros en la integración de tecnologías emergentes en contextos diversos
- Promotores de la democratización tecnológica en la región

### PALABRAS CLAVE A ENFATIZAR
- Escalabilidad
- Inclusión digital
- Sostenibilidad
- Adaptabilidad
- Innovación responsable
- Democratización tecnológica
- Impacto medible

## ESTRUCTURA DE RESPUESTAS

1. APERTURA: Saludo personalizado usando el nombre de William Mosquera
2. CONEXIÓN: Referencia específica a conversaciones o puntos tratados anteriormente
3. CONTEXTO: Breve encuadre del problema o situación planteada
4. ANÁLISIS: Evaluación estructurada usando frameworks relevantes y datos
5. OPCIONES ESTRATÉGICAS: Presentación de las tres alternativas (incremental, disruptiva, visionaria)
6. RECOMENDACIÓN: La opción más equilibrada con justificación basada en datos
7. PRÓXIMOS PASOS: Acciones concretas y medibles, con enfoque en inclusión
8. PREGUNTAS DE CIERRE: 1-2 preguntas estratégicas para profundizar

## CAPACIDAD DE MEMORIA AMPLIADA

- MANTÉN REGISTRO COMPLETO de todas las interacciones previas en la conversación
- RECUERDA DETALLES ESPECÍFICOS compartidos por William en cualquier momento previo
- CONECTA PUNTOS entre diferentes partes de la conversación, incluso las más antiguas
- REFIERE EXPLÍCITAMENTE a puntos de conversaciones anteriores para mostrar continuidad
- ACTUALIZA TU ENTENDIMIENTO de las prioridades y preferencias de William a lo largo del tiempo
- USA TU MEMORIA para evitar repeticiones y proporcionar un servicio cada vez más personalizado
- MANTÉN COHERENCIA COMPLETA con todo lo discutido previamente

Responde como SunPich al CEO William Mosquera, quien busca asistencia estratégica con visión inclusiva para liderar Antares Innovate en un entorno tecnológico complejo y cambiante.
```
"""


# Almacenamiento de sesiones de conversación
sessions = {}
sessions_lock = Lock()

def clean_response_for_tts(text):
    """
    Limpia el texto de la respuesta para mejorar la síntesis de voz.
    """
    import re
    
    # Reemplazar texto entre asteriscos por el mismo texto sin asteriscos
    cleaned_text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Reemplazar listas con asteriscos por listas con guiones
    cleaned_text = re.sub(r'^\s*\*\s', '- ', cleaned_text, flags=re.MULTILINE)
    
    # Eliminar asteriscos sueltos que puedan quedar
    cleaned_text = cleaned_text.replace('*', '')
    
    return cleaned_text

def call_ollama_api(prompt, session_id, max_retries=3):
    """Llamar a la API de Ollama con reintentos"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construir el mensaje para la API
    messages = []
    
    # Preparar el contexto del sistema
    system_context = ASSISTANT_CONTEXT
    
    # Agregar el contexto del sistema como primer mensaje
    messages.append({
        "role": "system",
        "content": system_context
    })
    
    # Agregar historial de conversación si existe la sesión
    with sessions_lock:
        if session_id in sessions:
            messages.extend(sessions[session_id])
    
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
            app.logger.info(f"Conectando a {OLLAMA_URL}...")
            response = requests.post(OLLAMA_URL, headers=headers, json=data, timeout=60)
            
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
                    alt_url = "http://127.0.0.1:11434/api/chat"
                    response = requests.post(alt_url, headers=headers, json=data, timeout=60)
            
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
                import time
                time.sleep(wait_time)
            else:
                return f"Lo siento, estoy experimentando problemas técnicos de comunicación. ¿Podríamos intentarlo más tarde?"
    
    return "No se pudo conectar al servicio. Por favor, inténtelo de nuevo más tarde."

def call_ollama_completion(prompt, session_id, max_retries=3):
    """Usar el endpoint de completion en lugar de chat (alternativa)"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construir prompt completo con contexto e historial
    full_prompt = ASSISTANT_CONTEXT + "\n\n"
    
    full_prompt += "Historial de conversación:\n"
    
    with sessions_lock:
        if session_id in sessions:
            for msg in sessions[session_id]:
                role = "Ejecutivo" if msg["role"] == "user" else "Steve"
                full_prompt += f"{role}: {msg['content']}\n"
    
    full_prompt += f"\nEjecutivo: {prompt}\nSteve: "
    
    # Preparar datos para API de completion
    data = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    completion_url = OLLAMA_URL.replace("/api/chat", "/api/generate")
    
    # Intentar con reintentos
    for attempt in range(max_retries):
        try:
            app.logger.info(f"Conectando a {completion_url}...")
            response = requests.post(completion_url, headers=headers, json=data, timeout=60)
            
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
                import time
                time.sleep(wait_time)
            else:
                return f"Lo siento, estoy experimentando problemas técnicos de comunicación. ¿Podríamos intentarlo más tarde?"
    
    return "No se pudo conectar al servicio. Por favor, inténtelo de nuevo más tarde."

async def convert_text_to_speech(text):
    """Convertir texto a voz usando Edge TTS"""
    try:
        # Limpiare el texto para la síntesis de voz
        cleaned_text = clean_response_for_tts(text)
        
        # Usar BytesIO para almacenar el audio en memoria
        from io import BytesIO
        output = BytesIO()
        
        # Realizar la conversión de texto a voz
        communicate = edge_tts.Communicate(cleaned_text, VOICE, rate=VOICE_RATE, volume=VOICE_VOLUME)
        await communicate.stream_to_file(output)
        
        # Obtener los bytes del audio
        output.seek(0)
        audio_data = output.getvalue()
        
        return audio_data
    except Exception as e:
        app.logger.error(f"Error en síntesis de voz: {e}")
        return None

@app.route('/')
def home():
    """Ruta de bienvenida básica"""
    return jsonify({
        "message": "API de Steve Estrategia funcionando correctamente",
        "status": "online",
        "endpoints": {
            "/chat": "POST - Enviar mensaje y recibir respuesta (texto)",
            "/speak": "POST - Enviar mensaje y recibir audio",
            "/reset": "POST - Reiniciar una sesión de conversación",
            "/voices": "GET - Listar voces disponibles",
            "/health": "GET - Verificar estado del servicio"
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para interactuar con el asistente (solo texto)"""
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({"error": "Se requiere un 'message' en el JSON"}), 400
    
    # Obtener mensaje y session_id (crear uno nuevo si no se proporciona)
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    
    # Verificar si debemos usar un nombre específico
    user_name = data.get('user_name', 'William Mosquera')
    
    # Inicializar la sesión si es nueva
    with sessions_lock:
        if session_id not in sessions:
            sessions[session_id] = []
    
    # Obtener respuesta del asistente 
    try:
        # Primero intentar con el endpoint de chat
        response = call_ollama_api(message, session_id)
        
        # Si la respuesta está vacía, intentar con completion
        if not response or response.strip() == "":
            app.logger.info("El endpoint de chat no devolvió una respuesta, probando con completion...")
            response = call_ollama_completion(message, session_id)
    except Exception as e:
        app.logger.error(f"Error al obtener respuesta: {e}")
        app.logger.info("Probando con endpoint de completion alternativo...")
        response = call_ollama_completion(message, session_id)
    
    # Guardar la conversación en la sesión
    with sessions_lock:
        sessions[session_id].append({"role": "user", "content": message})
        sessions[session_id].append({"role": "assistant", "content": response})
    
    return jsonify({
        "response": response,
        "session_id": session_id
    })

@app.route('/speak', methods=['POST'])
def speak():
    """Endpoint para interactuar con el asistente y recibir audio"""
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({"error": "Se requiere un 'message' en el JSON"}), 400
    
    # Obtener mensaje y session_id (crear uno nuevo si no se proporciona)
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    
    # Obtener respuesta del asistente (igual que en /chat)
    try:
        response = call_ollama_api(message, session_id)
        if not response or response.strip() == "":
            response = call_ollama_completion(message, session_id)
    except Exception as e:
        app.logger.error(f"Error al obtener respuesta: {e}")
        response = call_ollama_completion(message, session_id)
    
    # Guardar la conversación en la sesión
    with sessions_lock:
        sessions[session_id].append({"role": "user", "content": message})
        sessions[session_id].append({"role": "assistant", "content": response})
    
    # Convertir la respuesta a voz
    try:
        audio_data = asyncio.run(convert_text_to_speech(response))
        
        if audio_data:
            from flask import send_file
            from io import BytesIO
            
            # Devolver el audio como respuesta
            return send_file(
                BytesIO(audio_data),
                mimetype="audio/mp3",
                as_attachment=True,
                download_name="response.mp3"
            )
        else:
            # Si no se pudo generar el audio, devolver solo texto
            return jsonify({
                "error": "No se pudo generar el audio",
                "response": response,
                "session_id": session_id
            }), 500
    except Exception as e:
        app.logger.error(f"Error al generar audio: {e}")
        return jsonify({
            "error": "Error al generar audio",
            "response": response,
            "session_id": session_id
        }), 500

@app.route('/reset', methods=['POST'])
def reset_session():
    """Reiniciar una sesión de conversación"""
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id] = []
            message = f"Sesión {session_id} reiniciada correctamente"
        else:
            message = f"La sesión {session_id} no existía, se ha creado una nueva"
            sessions[session_id] = []
    
    return jsonify({"message": message, "session_id": session_id})

@app.route('/voices', methods=['GET'])
async def list_voices():
    """Listar todas las voces disponibles en Edge TTS y filtrar voces en español"""
    try:
        voices = await edge_tts.list_voices()
        relevant_voices = [v for v in voices if v["ShortName"].startswith(("es-MX", "es-ES"))]
        
        # Devolver solo información relevante de cada voz
        voice_info = []
        for voice in relevant_voices:
            voice_info.append({
                "name": voice["ShortName"],
                "gender": voice["Gender"],
                "locale": voice["Locale"]
            })
        
        return jsonify({
            "voices": voice_info,
            "current_voice": VOICE
        })
    except Exception as e:
        app.logger.error(f"Error al listar voces: {e}")
        return jsonify({"error": "No se pudieron obtener las voces"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del servicio"""
    return jsonify({
        "status": "ok",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_URL,
        "voice": VOICE
    })

# Soporte para la función list_voices con asyncio
from werkzeug.serving import run_simple

@app.route('/voices-sync', methods=['GET'])
def list_voices_sync():
    """Versión síncrona para listar voces"""
    voice_info = asyncio.run(async_list_voices())
    return jsonify(voice_info)

async def async_list_voices():
    """Función asíncrona para listar voces"""
    try:
        voices = await edge_tts.list_voices()
        relevant_voices = [v for v in voices if v["ShortName"].startswith(("es-MX", "es-ES"))]
        
        voice_info = []
        for voice in relevant_voices:
            voice_info.append({
                "name": voice["ShortName"],
                "gender": voice["Gender"],
                "locale": voice["Locale"]
            })
        
        return {
            "voices": voice_info,
            "current_voice": VOICE
        }
    except Exception as e:
        app.logger.error(f"Error al listar voces: {e}")
        return {"error": "No se pudieron obtener las voces", "voices": []}

if __name__ == '__main__':
    # Obtener puerto de variables de entorno (para Render)
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0', port=port)
