from src.models import db
from datetime import datetime

class ResearchItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    item_type = db.Column(db.String(50), nullable=False) # e.g., 'research', 'article', 'book'
    subject = db.Column(db.String(100))
    abstract = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(255)) # Comma-separated keywords
    file_path = db.Column(db.String(255), nullable=False) # Path to the uploaded file (e.g., PDF)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ResearchItem {self.title}>"

