from datetime import datetime

from mongoengine import Document, DateTimeField, FloatField, IntField, ListField, StringField


class RagChunk(Document):
    updated_at = DateTimeField(default=datetime.utcnow)
    source_name = StringField()
    source_fingerprint = StringField()
    chunk_index = IntField()
    text = StringField()
    embedding = ListField(FloatField())
    model = StringField()

    meta = {'indexes': ['source_name', 'model']}
