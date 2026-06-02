from datetime import datetime

from mongoengine import BooleanField, DateTimeField, DictField, Document, StringField


class ChatLog(Document):
    created_at = DateTimeField(default=datetime.utcnow)

    key = DictField()
    user_question = StringField()
    chat_api_response = StringField()

    liked = BooleanField()
    disliked = BooleanField()

    expired = BooleanField()
