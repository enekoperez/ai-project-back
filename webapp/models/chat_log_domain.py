from datetime import datetime

from mongoengine import DateTimeField, Document


class ChatLog(Document):
    created_at = DateTimeField(default=datetime.utcnow)
