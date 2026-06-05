from mongoengine import BooleanField, DateTimeField, DictField, Document, StringField

from webapp.datetime_utils import utc_now


class ChatLog(Document):
    created_at = DateTimeField(default=utc_now)

    key = DictField()
    user_question = StringField()
    chat_api_response = StringField()

    liked = BooleanField()
    disliked = BooleanField()

    expired = BooleanField()
