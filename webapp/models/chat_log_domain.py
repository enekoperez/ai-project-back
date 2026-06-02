from datetime import datetime

from mongoengine import BooleanField, DateTimeField, Document


class ChatLog(Document):
    created_at = DateTimeField(default=datetime.utcnow)
    liked = BooleanField()
    disliked = BooleanField()
