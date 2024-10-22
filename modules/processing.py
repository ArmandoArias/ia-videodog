# modules/processing.py

import os
import json
import logging

from modules.models import db, Video
from modules.youtube_man import procesar_audio
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url

def procesar_video(url_video, session_id, socketio):
    """
    Función para procesar el video en segundo plano.
    """
    total_steps = 5
    current_step = 0
    logger = logging.getLogger(__name__)

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

        # Descargar el audio (suponiendo que esta función retorna audio_path, video_id y titulo_actual)
        audio_path, video_id, titulo_actual = procesar_audio(url_video)
        logger.info(f"Audio descargado: {audio_path}, Video ID: {video_id}, Título: {titulo_actual}")

        # Paso 2: Subir el audio a S3
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 2/5: Subiendo audio a S3...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logger.info(f"Paso {current_step}/{total_steps}: Subiendo audio a S3 para session_id: {session_id}")

        bucket_name = 'ia-libretos'  # Reemplaza con el nombre de tu bucket
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
        logger.info(f"Paso {current_step}/{total_steps}: Iniciando transcripción para session_id: {session_id}")

        job_name = f"transcripcion-{video_id}"
        iniciar_transcripcion(job_name, audio_uri)
        logger.info(f"Transcripción iniciada: {job_name}")

        # Paso 4: Obtener transcripción
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 4/5: Obteniendo transcripción...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logger.info(f"Paso {current_step}/{total_steps}: Obteniendo transcripción para session_id: {session_id}")

        # Suponiendo que obtener_transcripcion espera hasta que la transcripción esté completa
        transcripcion = obtener_transcripcion(job_name, session_id, socketio)
        logger.info(f"Transcripción obtenida: {transcripcion}")
        transcripcion_limpia = limpiar_texto(transcripcion)
        logger.info(f"Transcripción limpia: {transcripcion_limpia}")

        # Paso 5: Generar sugerencias
        current_step += 1
        socketio.emit('progreso', {
            'data': 'Paso 5/5: Generando sugerencias...',
            'step': current_step,
            'total_steps': total_steps
        }, room=session_id)
        logger.info(f"Paso {current_step}/{total_steps}: Generando sugerencias para session_id: {session_id}")

        sugerencias = generar_sugerencias_claude_optimizado(transcripcion_limpia, titulo_actual)
        logger.info(f"Sugerencias generadas: {sugerencias}")

        # Asegurarse de que 'sugerencias' es un diccionario
        if isinstance(sugerencias, str):
            try:
                sugerencias = json.loads(sugerencias)
                logger.debug("Sugerencias convertidas de cadena a diccionario.")
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar las sugerencias: {e}")
                sugerencias = {"error": "Error al generar sugerencias."}

        # Extraer campos de sugerencias
        title1 = sugerencias.get('Título Opción 1', 'N/A')
        title2 = sugerencias.get('Título Opción 2', 'N/A')
        title3 = sugerencias.get('Título Opción 3', 'N/A')
        summary = sugerencias.get('Resumen', 'N/A')

        # Verificar si el video ya existe
        existing_video = Video.query.get(url_video)
        if existing_video:
            logger.info(f"El video con URL {url_video} ya existe en la base de datos. Actualizando registros existentes.")
            existing_video.title1 = title1
            existing_video.title2 = title2
            existing_video.title3 = title3
            existing_video.summary = summary
            existing_video.transcription = transcripcion_limpia
        else:
            # Guardar datos en la base de datos
            video = Video(
                url_video=url_video,  # Usar la URL como ID
                title1=title1,
                title2=title2,
                title3=title3,
                summary=summary,
                transcription=transcripcion_limpia
            )
            db.session.add(video)
            logger.info(f"Video guardado en la base de datos: {video}")

        db.session.commit()  # Commit para guardar los cambios
        logger.info(f"Datos guardados correctamente para session_id: {session_id}")

        # Emitir evento de resultado final
        socketio.emit('resultado', {
            'sugerencias': sugerencias
        }, room=session_id)
        logger.info(f"Evento 'resultado' emitido correctamente para session_id: {session_id}")

    except Exception as e:
        logger.error(f"Error en procesar_video: {e}", exc_info=True)
        socketio.emit('error', {'error': str(e)}, room=session_id)
