from datetime import datetime

from mongoengine import DateTimeField, Document


class OcrLog(Document):
    created_at = DateTimeField(default=datetime.utcnow)
