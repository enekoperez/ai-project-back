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
    ai_service.embed.return_value = [
        [0.1, 0.2],
        [0.1, 0.2],
        [0.1, 0.2],
        [0.1, 0.2],
    ]
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
    ai_service.embed.assert_called_once()
    assert len(ai_service.embed.call_args.kwargs["texts"]) == 4
    assert ai_service.embed.call_args.kwargs["dimensions"] == 768
    assert qdrant_repository.upsert_chunk.call_count == 4


def test_chunk_markdown_returns_empty_list_for_blank_text():
    assert RagService._chunk_markdown("   ") == []


def test_chunk_markdown_keeps_unbreakable_word_whole():
    chunks = RagService._chunk_markdown("a" * 1601)

    assert chunks == ["a" * 1601]


def test_chunk_markdown_prefixes_chunks_with_heading_path():
    text = "# A\n\nHi\n\n## B\n\nYo\n\n### C\n\nDeep\n\n## D\n\nBack up"

    assert RagService._chunk_markdown(text) == [
        "A\n\nHi",
        "A > B\n\nYo",
        "A > B > C\n\nDeep",
        "A > D\n\nBack up",
    ]


def test_chunk_markdown_ignores_headings_inside_code_fences():
    text = "# A\n\n```python\n# not a heading\nprint(1)\n```"

    assert RagService._chunk_markdown(text) == ["A\n\n```python\n# not a heading\nprint(1)\n```"]


def test_chunk_markdown_without_headings_has_no_prefix():
    assert RagService._chunk_markdown("Just plain text.") == ["Just plain text."]


def test_chunk_markdown_skips_heading_with_empty_body():
    assert RagService._chunk_markdown("# A\n## B\n\nText") == ["A > B\n\nText"]


def test_split_body_packs_paragraphs_with_overlap():
    paragraph = ("word " * 120).strip()  # 599 chars: three fit in 1600 only as 2 + 2.
    body = "\n\n".join([paragraph] * 4)

    chunks = RagService._split_body(body)

    assert len(chunks) == 2
    assert all(len(chunk) <= 1600 for chunk in chunks)
    assert chunks[0] == f"{paragraph}\n\n{paragraph}"
    # The second chunk starts with the overlap tail of the first one.
    assert chunks[1].startswith("word word")
    assert chunks[1].endswith(paragraph)


def test_split_long_paragraph_splits_at_word_boundaries():
    paragraph = ("word " * 500).strip()  # 2499 chars, above the 1600 limit.

    parts = RagService._split_long_paragraph(paragraph)

    assert len(parts) == 2
    assert all(len(part) <= 1600 for part in parts)
    assert " ".join(parts) == paragraph  # No characters lost, no mid-word cuts.


def test_split_long_paragraph_keeps_oversized_first_word_whole():
    assert RagService._split_long_paragraph("x" * 1700 + " end") == ["x" * 1700, "end"]


def test_overlap_tail_returns_short_text_whole():
    assert RagService._overlap_tail("short text") == "short text"


def test_overlap_tail_cuts_on_word_boundary():
    tail = RagService._overlap_tail(("word " * 100).strip())  # 499 chars.

    assert len(tail) <= 240
    assert tail.startswith("word")  # The leading partial word is dropped.


def test_overlap_tail_returns_raw_tail_when_no_space():
    assert RagService._overlap_tail("b" * 1500) == "b" * 240


def test_sync_skips_sources_with_empty_text():
    ai_service = Mock()
    qdrant_repository = Mock()
    doc_service = Mock()
    doc_service.get_source_files.return_value = [{"source_name": "empty.md"}]
    doc_service.get_source_text.return_value = ""
    service = make_service(
        ai_service=ai_service,
        qdrant_repository=qdrant_repository,
        doc_service=doc_service,
    )

    assert service.sync() is True

    ai_service.embed.assert_not_called()
    qdrant_repository.recreate_collection.assert_called_once_with(vector_size=768)
    qdrant_repository.upsert_chunk.assert_not_called()


def test_get_top_chunks_filters_scores_and_sorts_top_matches():
    ai_service = Mock()
    ai_service.embed.return_value = [[1.0, 0.0]]
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
        texts=["task: question answering | query: What sport?"],
        dimensions=768,
    )
    qdrant_repository.query_chunks.assert_called_once_with(
        embedding=[1.0, 0.0],
        limit=5,
        score_threshold=0.6,
    )
