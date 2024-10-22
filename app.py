# app.py

import eventlet
eventlet.monkey_patch()  # Debe llamarse antes de cualquier otra importación

import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy  # Importar SQLAlchemy
from flask_migrate import Migrate  # Importar Flask-Migrate
from dotenv import load_dotenv  # Importar dotenv para manejar variables de entorno
import logging
import json  # Importar json para manejar cadenas JSON
from uuid import uuid4
from flask_socketio import SocketIO, join_room  # Importar SocketIO

# Importar funciones de los módulos después de monkey_patch
from modules.youtube_man import procesar_audio
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url

# Cargar las variables de entorno desde .env
load_dotenv()

# Configuración de Logging
logging.basicConfig(
    level=logging.DEBUG,  # Nivel de logging más detallado
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Definir y configurar la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_secreto_aqui')  # Reemplaza con un secreto real
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')  # Asegúrate de definir DATABASE_URI en tu .env
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Inicializar Flask-Migrate
migrate = Migrate(app, db)

# Inicializar Flask-SocketIO
socketio = SocketIO(app, async_mode='eventlet')

# Definir modelo de la base de datos
class Video(db.Model):
    __tablename__ = 'videos'
    url_video = db.Column(db.String(255), primary_key=True)  # URL del video como ID
    title1 = db.Column(db.String(255), nullable=False)
    title2 = db.Column(db.String(255), nullable=False)
    title3 = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    transcription = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Video {self.url_video} - {self.title1}>"

# Crear las tablas de la base de datos (si no existen)
with app.app_context():
    db.create_all()

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

    Espera un JSON con 'url_video'.
    """
    data = request.get_json()
    url_video = data.get('url_video')
    if not url_video:
        logger.warning("No se proporcionó una URL de video.")
        return jsonify({'error': 'No se proporcionó una URL de video'}), 400

    # Validar y limpiar la URL en el backend
    url_limpia = limpiar_youtube_url(url_video)
    if not url_limpia:
        logger.warning(f"La URL proporcionada no es válida: {url_video}")
        return jsonify({'error': 'La URL proporcionada no es válida.'}), 400

    try:
        session_id = str(uuid4())  # Generar un nuevo session_id
        logger.debug(f"Generando nuevo session_id: {session_id}")
        # Iniciar la tarea en segundo plano
        socketio.start_background_task(procesar_video, url_limpia, session_id)
        return jsonify({'message': 'Procesamiento iniciado.', 'session_id': session_id}), 200
    except Exception as e:
        logger.error(f"Error en procesar_video_endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def procesar_video(url_video, session_id):
    """
    Función para procesar el video en segundo plano.
    """
    total_steps = 5
    current_step = 0

    try:
        logger.debug(f"Iniciando procesamiento del video con session_id: {session_id}")

        with app.app_context():  # Asegurar el contexto de la aplicación
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


# Manejo de eventos de SocketIO
@socketio.on('connect')
def handle_connect():
    logger.info('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Cliente desconectado')

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f'Cliente unido a la sala {session_id}')
    else:
        logger.warning('No se proporcionó un session_id para unirse a la sala.')

if __name__ == '__main__':
    # Ejecutar la aplicación sin el modo debug para evitar conflictos con Eventlet
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
