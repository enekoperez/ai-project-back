from datetime import datetime

from mongoengine import BooleanField, DateTimeField, DictField, Document


class ChatLog(Document):
    created_at = DateTimeField(default=datetime.utcnow)

    key = DictField()

    liked = BooleanField()
    disliked = BooleanField()
