from datetime import datetime

from mongoengine import DateTimeField, Document


class Chat(Document):
    created_at = DateTimeField(default=datetime.utcnow)
