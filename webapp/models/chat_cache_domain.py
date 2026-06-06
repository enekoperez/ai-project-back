from mongoengine import DictField, Document, StringField


class ChatCache(Document):
    key = DictField()
    name = StringField()

    meta = {
        "indexes": [
            {"fields": ["key"], "unique": True},
        ],
    }
