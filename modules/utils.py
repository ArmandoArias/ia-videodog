# modules/utils.py

import re

def limpiar_youtube_url(url):
    """
    Limpia y valida una URL de YouTube, extrayendo el ID del video y devolviendo una URL estándar.

    Parámetros:
    - url (str): URL proporcionada por el usuario.

    Retorna:
    - str: URL limpia en formato 'https://www.youtube.com/watch?v=VIDEO_ID' si es válida.
    - None: Si la URL no es válida.
    """
    regex = r'^(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})(?:\S+)?$'
    match = re.match(regex, url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/watch?v={video_id}'
    else:
        return None
