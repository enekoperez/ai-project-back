from unittest.mock import Mock

from webapp.services import rag_service as rag_service_module
from webapp.services.rag_service import RagService


def make_service(ai_service=None, repository=None, doc_service=None):
    service = RagService.__new__(RagService)
    service.ai_service = ai_service or Mock()
    service.rag_chunk_repository = repository or Mock()
    service.doc_service = doc_service or Mock()
    return service


def test_init_creates_dependencies(monkeypatch):
    ai_service = Mock()
    repository = Mock()
    doc_service = Mock()
    monkeypatch.setattr("webapp.services.rag_service.AiService", Mock(return_value=ai_service))
    monkeypatch.setattr("webapp.services.rag_service.RagChunkRepository", Mock(return_value=repository))
    monkeypatch.setattr("webapp.services.rag_service.DocService", Mock(return_value=doc_service))

    service = RagService()

    assert service.ai_service == ai_service
    assert service.rag_chunk_repository == repository
    assert service.doc_service == doc_service


def test_prepare_query_and_document():
    assert RagService._prepare_query("How many players?") == (
        "task: question answering | query: How many players?"
    )
    assert RagService._prepare_document(content="Football text") == "title: none | text: Football text"
    assert RagService._prepare_document(content="Football text", title="football.md") == (
        "title: football.md | text: Football text"
    )


def test_sync_embeds_new_or_changed_source_files(monkeypatch):
    monkeypatch.setattr(rag_service_module.config.Config, "DEFAULT_GOOGLE_AI_EMBEDDING_MODEL", "embedding-model")
    ai_service = Mock()
    ai_service.embed.return_value = ([0.1, 0.2], "embedding-model")
    repository = Mock()
    repository.get_source_name_source_fingerprint_and_model.return_value = [
        Mock(source_name="basketball.md", source_fingerprint="same", model="embedding-model")
    ]
    doc_service = Mock()
    doc_service.get_source_files.return_value = [
        {"source_name": "basketball.md", "source_fingerprint": "same"},
        {"source_name": "football.md", "source_fingerprint": "new"},
    ]
    doc_service.get_source_text.return_value = " Football chunk one. " + ("x" * 1700)
    service = make_service(ai_service=ai_service, repository=repository, doc_service=doc_service)

    assert service.sync() is True

    repository.delete_source_names_not_in.assert_called_once_with(
        source_names={"basketball.md", "football.md"}
    )
    doc_service.get_source_text.assert_called_once_with(
        source_file={"source_name": "football.md", "source_fingerprint": "new"}
    )
    repository.delete_chunks_by_source_name.assert_called_once_with(source_name="football.md")
    assert ai_service.embed.call_count == 2
    assert repository.create.call_count == 2


def test_chunk_markdown_returns_empty_list_for_blank_text():
    assert RagService._chunk_markdown("   ") == []


def test_chunk_markdown_splits_text_into_max_sized_chunks():
    chunks = RagService._chunk_markdown("a" * 1601)

    assert chunks == ["a" * 1600, "a"]


def test_get_top_chunks_filters_scores_and_sorts_top_matches():
    ai_service = Mock()
    ai_service.embed.return_value = ([1.0, 0.0], "embedding-model")
    repository = Mock()
    repository.get_all_by_model.return_value = [
        Mock(source_name="low.md", text="Low", embedding=[0.0, 1.0]),
        Mock(source_name="best.md", text="Best", embedding=[1.0, 0.0]),
        Mock(source_name="middle.md", text="Middle", embedding=[0.8, 0.6]),
        Mock(source_name="also.md", text="Also", embedding=[0.7, 0.7]),
    ]
    service = make_service(ai_service=ai_service, repository=repository)

    assert service.get_top_chunks(question="What sport?") == [
        {"source_name": "best.md", "text": "Best", "score": 1.0},
        {"source_name": "middle.md", "text": "Middle", "score": 0.8},
        {"source_name": "also.md", "text": "Also", "score": 0.7071067811865476},
    ]
    ai_service.embed.assert_called_once_with(
        text="task: question answering | query: What sport?"
    )
    repository.get_all_by_model.assert_called_once_with(model="embedding-model")


def test_cosine_similarity_returns_zero_for_zero_vectors():
    assert RagService._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0
