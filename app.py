# app.py

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from uuid import uuid4
import os

# Importar funciones de los módulos
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url
from modules.youtube_man import procesar_audio

app = Flask(__name__)
socketio = SocketIO(app)

def procesar_video(url_video, session_id):
    total_steps = 5
    current_step = 0

    try:
        # Paso 1: Validar y procesar el audio
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Procesando audio...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)

        # Aquí asumiríamos que el audio ya está disponible o se procesa de manera permitida
        audio_path, video_id, titulo_actual = procesar_audio(url_video)

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
        # Emitir evento de error
        socketio.emit('error', {'data': str(e)}, room=session_id)

# Rutas de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/procesar_video', methods=['POST'])
def procesar_video_endpoint():
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)
