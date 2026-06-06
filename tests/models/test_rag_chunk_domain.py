from mongoengine import DateTimeField, IntField, ListField, StringField

from webapp.models.rag_chunk_domain import RagChunk


def test_rag_chunk_model_has_fields():
    assert isinstance(RagChunk._fields["updated_at"], DateTimeField)
    assert isinstance(RagChunk._fields["source_name"], StringField)
    assert isinstance(RagChunk._fields["source_fingerprint"], StringField)
    assert isinstance(RagChunk._fields["chunk_index"], IntField)
    assert isinstance(RagChunk._fields["text"], StringField)
    assert isinstance(RagChunk._fields["embedding"], ListField)
    assert isinstance(RagChunk._fields["model"], StringField)


def test_rag_chunk_model_indexes_repository_filters():
    assert {"fields": ["source_name"]} in RagChunk._meta["indexes"]
    assert {"fields": ["model"]} in RagChunk._meta["indexes"]
