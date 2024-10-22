# modules/aws_services.py

import os
import boto3
import logging
from botocore.exceptions import ClientError

# Configuración de AWS
transcribe = boto3.client('transcribe', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

def subir_audio_s3(audio_path, bucket_name, s3_key):
    """
    Sube un archivo de audio a un bucket de S3 si no existe ya.

    Parámetros:
    - audio_path (str): Ruta local del archivo de audio.
    - bucket_name (str): Nombre del bucket de S3.
    - s3_key (str): Clave (ruta) en S3 donde se almacenará el archivo.

    Retorna:
    - str: URI del archivo en S3.

    Lanza:
    - FileNotFoundError: Si el archivo local no existe.
    - Exception: Si ocurre un error al subir el archivo a S3.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"El archivo de audio no fue encontrado: {audio_path}")

    if verificar_audio_s3(bucket_name, s3_key):
        return f"s3://{bucket_name}/{s3_key}"

    try:
        s3.upload_file(audio_path, bucket_name, s3_key)
        logging.info(f"Audio subido a S3: {s3_key}")
        return f"s3://{bucket_name}/{s3_key}"
    except ClientError as e:
        logging.error(f"Error al subir el archivo a S3: {e}")
        raise Exception("Error al subir el archivo a S3.") from e

def verificar_audio_s3(bucket_name, s3_key):
    """
    Verifica si un archivo existe en un bucket de S3.

    Parámetros:
    - bucket_name (str): Nombre del bucket de S3.
    - s3_key (str): Clave (ruta) del archivo en S3.

    Retorna:
    - bool: True si el archivo existe, False si no existe.

    Lanza:
    - Exception: Si ocurre un error al verificar el archivo en S3.
    """
    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        logging.info(f"El archivo ya está subido a S3: {s3_key}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logging.error(f"Error al verificar en S3: {e}")
            raise Exception("Error al verificar el archivo en S3.") from e

def iniciar_transcripcion(job_name, audio_uri):
    El flujo del método es el siguiente:
    1. Verifica si ya existe un trabajo de transcripción con el nombre dado.
    2. Si el trabajo ya existe y está completado, retorna la transcripción existente.
    3. Si el trabajo no existe, intenta iniciar un nuevo trabajo de transcripción con los parámetros proporcionados.
    4. Si ocurre un error al iniciar el trabajo de transcripción, lanza una excepción con un mensaje de error.
    Ejemplo de uso:
    >>> iniciar_transcripcion('mi_trabajo', 's3://mi-bucket/mi-audio.mp3')
    """
    Inicia un trabajo de transcripción en AWS Transcribe si no existe ya.

    Parámetros:
    - job_name (str): Nombre del trabajo de transcripción.
    - audio_uri (str): URI del archivo de audio en S3.

    Retorna:
    - dict: Respuesta del servicio Transcribe.

    Lanza:
    - Exception: Si ocurre un error al iniciar el trabajo de transcripción.
    """
    transcripcion_existente = verificar_transcripcion_existente(job_name)
    if transcripcion_existente:
        logging.info(f"El trabajo de transcripción '{job_name}' ya existe y está completado.")
        return transcripcion_existente
    else:
        try:
            response = transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_uri},
                MediaFormat='mp3',
                IdentifyLanguage=True,
                LanguageOptions=['en-US', 'es-ES']
            )
            logging.info(f"Trabajo de transcripción iniciado: {job_name}")
            return response
        except ClientError as e:
            logging.error(f"Error al iniciar el trabajo de transcripción: {e}")
            raise Exception("Error al iniciar el trabajo de transcripción.") from e

def verificar_transcripcion_existente(job_name):
    """
    Verifica si un trabajo de transcripción ya existe y está completado.

    Parámetros:
    - job_name (str): Nombre del trabajo de transcripción.

    Retorna:
    - dict: Estado del trabajo si está completado.
    - None: Si el trabajo no existe o no está completado.

    Lanza:
    - Exception: Si ocurre un error al verificar el trabajo de transcripción.
    """
    try:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status['TranscriptionJob']['TranscriptionJobStatus']
        if job_status == 'COMPLETED':
            return status
        else:
            return None
    except transcribe.exceptions.BadRequestException:
        return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NotFoundException':
            return None
        else:
            logging.error(f"Error al verificar la transcripción existente: {e}")
            raise Exception("Error al verificar la transcripción existente.") from e
