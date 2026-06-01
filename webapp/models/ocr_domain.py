from datetime import datetime

from mongoengine import DateTimeField, Document


class Ocr(Document):
    created_at = DateTimeField(default=datetime.utcnow)
