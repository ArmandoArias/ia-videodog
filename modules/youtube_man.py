# modules/youtube_man.py

import os
import yt_dlp

# Definir la carpeta de audios
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio del módulo
AUDIO_DIR = os.path.join(ROOT_DIR, '..', 'audios')  # Carpeta 'audios' en el directorio principal

# Asegurarse de que la carpeta de audios exista
os.makedirs(AUDIO_DIR, exist_ok=True)

def procesar_audio(url_video):
    video_id = url_video.split('=')[-1]
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url_video, download=True)
            video_id = info_dict.get('id', None)
            titulo_actual = info_dict.get('title', 'Título Desconocido')

        audio_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"El archivo de audio no fue creado correctamente: {audio_path}")

        print(f"Audio descargado correctamente: {audio_path}")
        return audio_path, video_id, titulo_actual

    except yt_dlp.utils.DownloadError as e:
        print(f"Error de descarga con yt-dlp: {e}")
        raise Exception("Error al descargar el audio.")

    except Exception as e:
        print(f"Error inesperado al descargar el audio: {e}")
        raise Exception("Error inesperado al descargar el audio.")
    return audio_path, video_id, titulo_actual
