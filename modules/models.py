# modules/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Video(db.Model):
    """
    Clase Video que representa un video en la base de datos.
    Atributos:
        __tablename__ (str): Nombre de la tabla en la base de datos.
        url_video (db.Column): URL del video que actúa como ID principal.
        title1 (db.Column): Primer título del video.
        title2 (db.Column): Segundo título del video.
        title3 (db.Column): Tercer título del video.
        summary (db.Column): Resumen del video.
        transcription (db.Column): Transcripción completa del video.
    Métodos:
        __repr__: Representación en cadena del objeto Video.
    """
    __tablename__ = 'videos'
    url_video = db.Column(db.String(255), primary_key=True)  # URL del video como ID
    title1 = db.Column(db.String(255), nullable=False)
    title2 = db.Column(db.String(255), nullable=False)
    title3 = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    transcription = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Video {self.url_video} - {self.title1}>"
