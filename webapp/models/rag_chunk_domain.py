from mongoengine import Document, DateTimeField, FloatField, IntField, ListField, StringField

from webapp.datetime_utils import utc_now


class RagChunk(Document):
    updated_at = DateTimeField(default=utc_now)
    source_name = StringField()
    source_fingerprint = StringField()
    chunk_index = IntField()
    text = StringField()
    embedding = ListField(FloatField())
    model = StringField()

    meta = {'indexes': ['source_name', 'model']}
