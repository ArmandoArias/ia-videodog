# modules/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
