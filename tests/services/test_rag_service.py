from unittest.mock import Mock

from webapp.services.rag_service import RagService


def make_service(ai_service=None, qdrant_repository=None, doc_service=None):
    service = RagService.__new__(RagService)
    service.ai_service = ai_service or Mock()
    service.qdrant_repository = qdrant_repository or Mock()
    service.doc_service = doc_service or Mock()
    return service


def test_init_creates_dependencies(monkeypatch):
    ai_service = Mock()
    qdrant_repository = Mock()
    doc_service = Mock()
    monkeypatch.setattr("webapp.services.rag_service.AiService", Mock(return_value=ai_service))
    monkeypatch.setattr("webapp.services.rag_service.QdrantRepository", Mock(return_value=qdrant_repository))
    monkeypatch.setattr("webapp.services.rag_service.DocService", Mock(return_value=doc_service))

    service = RagService()

    assert service.ai_service == ai_service
    assert service.qdrant_repository == qdrant_repository
    assert service.doc_service == doc_service


def test_prepare_query_and_document():
    assert RagService._prepare_query("How many players?") == (
        "task: question answering | query: How many players?"
    )
    assert RagService._prepare_document(content="Football text") == "title: none | text: Football text"
    assert RagService._prepare_document(content="Football text", title="football.md") == (
        "title: football.md | text: Football text"
    )


def test_sync_rebuilds_qdrant_from_source_files():
    ai_service = Mock()
    ai_service.embed.return_value = [0.1, 0.2]
    qdrant_repository = Mock()
    doc_service = Mock()
    doc_service.get_source_files.return_value = [
        {"source_name": "basketball.md"},
        {"source_name": "football.md"},
    ]
    doc_service.get_source_text.return_value = " Football chunk one. " + ("x" * 1700)
    service = make_service(
        ai_service=ai_service,
        qdrant_repository=qdrant_repository,
        doc_service=doc_service,
    )

    assert service.sync() is True

    qdrant_repository.recreate_collection.assert_called_once_with(vector_size=768)
    assert doc_service.get_source_text.call_count == 2
    assert ai_service.embed.call_count == 4
    assert qdrant_repository.upsert_chunk.call_count == 4


def test_chunk_markdown_returns_empty_list_for_blank_text():
    assert RagService._chunk_markdown("   ") == []


def test_chunk_markdown_splits_text_into_max_sized_chunks():
    chunks = RagService._chunk_markdown("a" * 1601)

    assert chunks == ["a" * 1600, "a"]


def test_get_top_chunks_filters_scores_and_sorts_top_matches():
    ai_service = Mock()
    ai_service.embed.return_value = [1.0, 0.0]
    qdrant_repository = Mock()
    qdrant_repository.query_chunks.return_value = [
        {"source_name": "best.md", "text": "Best", "score": 1.0},
        {"source_name": "middle.md", "text": "Middle", "score": 0.8},
    ]
    service = make_service(ai_service=ai_service, qdrant_repository=qdrant_repository)

    assert service.get_top_chunks(question="What sport?") == [
        {"source_name": "best.md", "text": "Best", "score": 1.0},
        {"source_name": "middle.md", "text": "Middle", "score": 0.8},
    ]
    ai_service.embed.assert_called_once_with(
        text="task: question answering | query: What sport?",
        dimensions=768,
    )
    qdrant_repository.query_chunks.assert_called_once_with(
        embedding=[1.0, 0.0],
        limit=5,
        score_threshold=0.6,
    )
