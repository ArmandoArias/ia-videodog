# app.py

import eventlet
eventlet.monkey_patch()  # Debe llamarse antes de cualquier otra importación

import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room
from uuid import uuid4
import logging

# Importar funciones de los módulos después de monkey_patch
from modules.youtube_man import procesar_audio
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url

# Configuración de Logging
logging.basicConfig(
    level=logging.DEBUG,  # Nivel de logging más detallado
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_secreto_aqui'  # Reemplaza con un secreto real
socketio = SocketIO(app, async_mode='eventlet')  # Especificar el modo asíncrono

def procesar_video(url_video, session_id):
    """
    Procesa un video de YouTube: descarga audio, sube a S3, transcribe y genera sugerencias.

    Parámetros:
    - url_video (str): URL limpia del video de YouTube.
    - session_id (str): ID de sesión para emitir eventos a través de SocketIO.
    """
    total_steps = 5
    current_step = 0

    try:
        logging.debug(f"Iniciando procesamiento del video con session_id: {session_id}")
        
        # Paso 1: Descargar el audio
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Descargando audio...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logging.info(f"Paso {current_step}/{total_steps}: Descargando audio para session_id: {session_id}")

        audio_path, video_id, titulo_actual = procesar_audio(url_video)
        logging.info(f"Audio descargado: {audio_path}, Video ID: {video_id}, Título: {titulo_actual}")

        # Paso 2: Subir el audio a S3
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Subiendo audio a S3...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logging.info(f"Paso {current_step}/{total_steps}: Subiendo audio a S3 para session_id: {session_id}")

        bucket_name = 'ia-libretos'  # Reemplaza con el nombre de tu bucket
        s3_key = f'audios/{os.path.basename(audio_path)}'
        audio_uri = subir_audio_s3(audio_path, bucket_name, s3_key)
        logging.info(f"Audio subido a S3: {audio_uri}")

        # Paso 3: Iniciar transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Iniciando transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logging.info(f"Paso {current_step}/{total_steps}: Iniciando transcripción para session_id: {session_id}")

        job_name = f"transcripcion-{video_id}"
        iniciar_transcripcion(job_name, audio_uri)
        logging.info(f"Transcripción iniciada: {job_name}")

        # Paso 4: Obtener transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Obteniendo transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logging.info(f"Paso {current_step}/{total_steps}: Obteniendo transcripción para session_id: {session_id}")

        transcripcion = obtener_transcripcion(job_name, session_id, socketio)
        logging.info(f"Transcripción obtenida: {transcripcion}")
        transcripcion_limpia = limpiar_texto(transcripcion)
        logging.info(f"Transcripción limpia: {transcripcion_limpia}")

        # Paso 5: Generar sugerencias
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Generando sugerencias...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logging.info(f"Paso {current_step}/{total_steps}: Generando sugerencias para session_id: {session_id}")

        sugerencias = generar_sugerencias_claude_optimizado(transcripcion_limpia, titulo_actual)
        logging.info(f"Sugerencias generadas: {sugerencias}")

        # Emitir evento de resultado final
        socketio.emit('resultado', {
            'sugerencias': sugerencias
        }, room=session_id)
        logging.info(f"Evento 'resultado' emitido correctamente para session_id: {session_id}")

    except Exception as e:
        logging.error(f"Error en procesar_video: {e}", exc_info=True)
        # Emitir evento de error
        socketio.emit('error', {'data': str(e)}, room=session_id)

# Rutas de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process')
def process_route():
    return render_template('process.html')

@app.route('/procesar_video', methods=['POST'])
def procesar_video_endpoint():
    """
    Endpoint para procesar un video de YouTube.

    Espera un JSON con 'url_video'.
    """
    data = request.get_json()
    url_video = data.get('url_video')
    if not url_video:
        logging.warning("No se proporcionó una URL de video.")
        return jsonify({'error': 'No se proporcionó una URL de video'}), 400

    # Validar y limpiar la URL en el backend
    url_limpia = limpiar_youtube_url(url_video)
    if not url_limpia:
        logging.warning(f"La URL proporcionada no es válida: {url_video}")
        return jsonify({'error': 'La URL proporcionada no es válida.'}), 400

    try:
        session_id = str(uuid4())  # Generar un nuevo session_id
        logging.debug(f"Generando nuevo session_id: {session_id}")
        # Iniciar la tarea en segundo plano
        socketio.start_background_task(procesar_video, url_limpia, session_id)
        return jsonify({'message': 'Procesamiento iniciado.', 'session_id': session_id}), 200
    except Exception as e:
        logging.error(f"Error en procesar_video_endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Manejo de eventos de SocketIO
@socketio.on('connect')
def handle_connect():
    logging.info('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Cliente desconectado')

@socketio.on('join')
def handle_join(session_id):
    join_room(session_id)
    logging.info(f'Cliente unido a la sala {session_id}')

if __name__ == '__main__':
    socketio.run(app, debug=True)
