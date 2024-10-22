# app.py

import eventlet
eventlet.monkey_patch()  # Debe llamarse antes de cualquier otra importación

import os
from flask import Flask, render_template, request, jsonify
from flask_migrate import Migrate  # Importar Flask-Migrate
from dotenv import load_dotenv  # Importar dotenv para manejar variables de entorno
import logging
from uuid import uuid4
from flask_socketio import SocketIO, join_room  # Importar SocketIO

# Importar funciones de los módulos después de monkey_patch
from modules.youtube_man import procesar_audio
from modules.aws_services import subir_audio_s3, iniciar_transcripcion
from modules.transcriber import obtener_transcripcion, limpiar_texto
from modules.bedrock_generator import generar_sugerencias_claude_optimizado
from modules.utils import limpiar_youtube_url
from modules.processing import procesar_video  # Importar la función procesar_video

from modules.models import db, Video  # Importar el modelo y db

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
db.init_app(app)

# Inicializar Flask-Migrate
migrate = Migrate(app, db)

# Inicializar Flask-SocketIO
socketio = SocketIO(app, async_mode='eventlet')

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
        # Verificar si el video ya existe en la base de datos
        existing_video = Video.query.get(url_limpia)
        session_id = str(uuid4())  # Generar un nuevo session_id
        logger.debug(f"Generando nuevo session_id: {session_id}")

        if existing_video:
            logger.info(f"El video con URL {url_limpia} ya existe en la base de datos.")
            sugerencias = {
                'Título Opción 1': existing_video.title1,
                'Título Opción 2': existing_video.title2,
                'Título Opción 3': existing_video.title3,
                'Resumen': existing_video.summary
            }
            return jsonify({
                'message': 'Video ya procesado. Mostrando resultados.',
                'sugerencias': sugerencias,
                'session_id': session_id
            }), 200
        else:
            # Iniciar la tarea en segundo plano dentro del contexto de la aplicación
            socketio.start_background_task(procesar_video_with_context, url_limpia, session_id)
            return jsonify({'message': 'Procesamiento iniciado.', 'session_id': session_id}), 200
    except Exception as e:
        logger.error(f"Error en procesar_video_endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def procesar_video_with_context(url_video, session_id):
    """
    Función envolvente que ejecuta 'procesar_video' dentro del contexto de la aplicación.
    """
    with app.app_context():
        procesar_video(url_video, session_id, socketio)

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
