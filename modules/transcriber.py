# modules/transcriber.py

import time
from flask_socketio import SocketIO
import requests
import json
import re
import logging

from .aws_services import transcribe

def obtener_transcripcion(job_name, session_id, socketio: SocketIO):
    """
    Obtiene la transcripción de un trabajo de transcripción en AWS Transcribe.

    Parámetros:
    - job_name (str): Nombre del trabajo de transcripción.
    - session_id (str): ID de sesión para emitir eventos a través de SocketIO.
    - socketio (SocketIO): Instancia de SocketIO para emitir eventos.

    Retorna:
    - str: Texto transcrito.
    """
    while True:
        try:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'COMPLETED':
                transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                response = requests.get(transcript_file_uri)
                transcript_json = response.json()
                transcripcion = transcript_json['results']['transcripts'][0]['transcript']
                return transcripcion

            elif job_status == 'FAILED':
                raise Exception("La transcripción falló.")

            else:
                # Emitir evento de progreso
                socketio.emit('progreso_transcripcion', {'data': 'Transcribiendo... Por favor espera.'}, room=session_id)

            socketio.sleep(5)  # Usa socketio.sleep con Gevent

        except Exception as e:
            logging.error(f"Error al obtener la transcripción: {e}")
            raise e

def limpiar_texto(texto):
    """
    Limpia el texto de la transcripción eliminando caracteres no deseados y espacios extra.

    Parámetros:
    - texto (str): Texto a limpiar.

    Retorna:
    - str: Texto limpio.
    """
    texto_limpio = re.sub(r'[^\w\sáéíóúÁÉÍÓÚñÑüÜ]', '', texto)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
    return texto_limpio.strip()
