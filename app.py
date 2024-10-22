# app.py

import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room
from uuid import uuid4
import logging

# Importar funciones de los módulos
from modules.youtube_downloader import descargar_audio  # Asegúrate de que este es el nombre correcto
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
socketio = SocketIO(app)

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
        # Paso 1: Descargar el audio
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Descargando audio...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        audio_path, video_id, titulo_actual = descargar_audio(url_video)

        # Paso 2: Subir el audio a S3
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Subiendo audio a S3...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        bucket_name = 'ia-libretos'  # Reemplaza con el nombre de tu bucket
        s3_key = f'audios/{os.path.basename(audio_path)}'
        audio_uri = subir_audio_s3(audio_path, bucket_name, s3_key)

        # Paso 3: Iniciar transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Iniciando transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        job_name = f"transcripcion-{video_id}"
        iniciar_transcripcion(job_name, audio_uri)

        # Paso 4: Obtener transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Obteniendo transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        transcripcion = obtener_transcripcion(job_name, session_id, socketio)
        transcripcion_limpia = limpiar_texto(transcripcion)

        # Paso 5: Generar sugerencias
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Generando sugerencias...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        sugerencias = generar_sugerencias_claude_optimizado(transcripcion_limpia, titulo_actual)

        # Emitir evento de resultado final
        socketio.emit('resultado', {
            'sugerencias': sugerencias
        }, room=session_id)

    except Exception as e:
        logging.error(f"Error en procesar_video: {e}")
        # Emitir evento de error
        socketio.emit('error', {'data': str(e)}, room=session_id)

# Rutas de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process')
def process():
    return render_template('process.html')

@app.route('/procesar_video', methods=['POST'])
def procesar_video_endpoint():
    """
    Endpoint para procesar un video de YouTube.

    Espera un JSON con 'url_video' y opcionalmente 'session_id'.
    """
    data = request.get_json()
    url_video = data.get('url_video')
    if not url_video:
        return jsonify({'error': 'No se proporcionó una URL de video'}), 400

    # Validar y limpiar la URL en el backend
    url_limpia = limpiar_youtube_url(url_video)
    if not url_limpia:
        return jsonify({'error': 'La URL proporcionada no es válida.'}), 400

    try:
        session_id = data.get('session_id')
        if not session_id:
            session_id = str(uuid4())

        # Iniciar la tarea en segundo plano
        socketio.start_background_task(procesar_video, url_limpia, session_id)

        return jsonify({'message': 'Procesamiento iniciado.', 'session_id': session_id}), 200
    except Exception as e:
        logging.error(f"Error en procesar_video_endpoint: {e}")
        return jsonify({'error': str(e)}), 500

# Manejo de eventos de SocketIO
@socketio.on('connect')
def handle_connect():
    logging.info('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Cliente desconectado')

@socketio.on('join')
def handle_join(data):
    session_id = data
    join_room(session_id)
    logging.info(f'Cliente unido a la sala {session_id}')

if __name__ == '__main__':
    socketio.run(app, debug=True)
