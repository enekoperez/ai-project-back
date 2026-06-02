from unittest.mock import Mock

from webapp.repositories.rag_chunk_repository import RagChunkRepository


def test_create_delegates_to_model(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.create.return_value = "created-rag-chunk"
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().create(
        source_name="football.md",
        source_fingerprint="123:456",
        chunk_index=1,
        text="Football text",
        embedding=[0.1, 0.2],
        model="embedding-model",
    ) == "created-rag-chunk"
    rag_chunk_model.objects.create.assert_called_once_with(
        source_name="football.md",
        source_fingerprint="123:456",
        chunk_index=1,
        text="Football text",
        embedding=[0.1, 0.2],
        model="embedding-model",
    )


def test_get_all_by_model_delegates_to_model(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.return_value = ["chunk"]
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().get_all_by_model(model="embedding-model") == ["chunk"]
    rag_chunk_model.objects.assert_called_once_with(model="embedding-model")


def test_get_source_name_source_fingerprint_and_model_delegates_to_model(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.only.return_value.all.return_value = ["source"]
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().get_source_name_source_fingerprint_and_model() == ["source"]
    rag_chunk_model.objects.only.assert_called_once_with("source_name", "source_fingerprint", "model")
    rag_chunk_model.objects.only.return_value.all.assert_called_once_with()


def test_delete_source_names_not_in_deletes_missing_sources(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.return_value.delete.return_value = 2
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().delete_source_names_not_in(source_names={"football.md"}) == 2
    rag_chunk_model.objects.assert_called_once_with(source_name__nin=["football.md"])
    rag_chunk_model.objects.return_value.delete.assert_called_once_with()


def test_delete_source_names_not_in_deletes_all_when_no_sources(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.delete.return_value = 3
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().delete_source_names_not_in(source_names=set()) == 3
    rag_chunk_model.objects.delete.assert_called_once_with()


def test_delete_chunks_by_source_name_delegates_to_model(monkeypatch):
    rag_chunk_model = Mock()
    rag_chunk_model.objects.return_value.delete.return_value = 1
    monkeypatch.setattr("webapp.repositories.rag_chunk_repository.RagChunk", rag_chunk_model)

    assert RagChunkRepository().delete_chunks_by_source_name(source_name="football.md") == 1
    rag_chunk_model.objects.assert_called_once_with(source_name="football.md")
    rag_chunk_model.objects.return_value.delete.assert_called_once_with()
