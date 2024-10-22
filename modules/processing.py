import os
import json
import logging
from flask_socketio import SocketIO
from modules.models import db, Video
from modules.youtube_man import procesar_audio
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado

logger = logging.getLogger(__name__)

def procesar_video(url_video, session_id, socketio: SocketIO):
    """
    Función para procesar el video en segundo plano.
    """
    total_steps = 5
    current_step = 0

    try:
        logger.debug(f"Iniciando procesamiento del video con session_id: {session_id}")

        # Paso 1: Descargar el audio
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 1/5: Descargando audio...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logger.info(f"Paso {current_step}/{total_steps}: Descargando audio para session_id: {session_id}")

        # Descargar el audio
        audio_path, video_id, titulo_actual = procesar_audio(url_video)
        logger.info(f"Audio descargado: {audio_path}, Video ID: {video_id}, Título: {titulo_actual}")

        # Paso 2: Subir el audio a S3
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 2/5: Subiendo audio a S3...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        bucket_name = 'ia-libretos'
        s3_key = f'audios/{os.path.basename(audio_path)}'
        audio_uri = subir_audio_s3(audio_path, bucket_name, s3_key)
        logger.info(f"Audio subido a S3: {audio_uri}")

        # Paso 3: Iniciar transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 3/5: Iniciando transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        job_name = f"transcripcion-{video_id}"
        iniciar_transcripcion(job_name, audio_uri)

        # Paso 4: Obtener transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 4/5: Obteniendo transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        transcripcion = obtener_transcripcion(job_name, session_id, socketio)
        transcripcion_limpia = limpiar_texto(transcripcion)

        # Paso 5: Generar sugerencias
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 5/5: Generando sugerencias...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        sugerencias = generar_sugerencias_claude_optimizado(transcripcion_limpia, titulo_actual)

        # Verificar si el video ya existe
        existing_video = Video.query.get(url_video)
        if existing_video:
            existing_video.title1 = sugerencias.get('Título Opción 1', 'N/A')
            existing_video.title2 = sugerencias.get('Título Opción 2', 'N/A')
            existing_video.title3 = sugerencias.get('Título Opción 3', 'N/A')
            existing_video.summary = sugerencias.get('Resumen', 'N/A')
            existing_video.transcription = transcripcion_limpia
        else:
            video = Video(
                url_video=url_video,
                title1=sugerencias.get('Título Opción 1', 'N/A'),
                title2=sugerencias.get('Título Opción 2', 'N/A'),
                title3=sugerencias.get('Título Opción 3', 'N/A'),
                summary=sugerencias.get('Resumen', 'N/A'),
                transcription=transcripcion_limpia
            )
            db.session.add(video)

        db.session.commit()

        socketio.emit('resultado', {
            'sugerencias': sugerencias
        }, room=session_id)

    except Exception as e:
        logger.error(f"Error en procesar_video: {e}", exc_info=True)
        socketio.emit('error', {'error': str(e)}, room=session_id)

def procesar_video_with_context(app, url_video, session_id, socketio):
    """
    Función envolvente para procesar el video dentro del contexto de la app.
    """
    with app.app_context():
        procesar_video(url_video, session_id, socketio)
