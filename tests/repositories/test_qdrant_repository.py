from types import SimpleNamespace
from unittest.mock import Mock

from webapp.repositories.qdrant_repository import QdrantRepository


def test_recreate_collection_deletes_existing_collection():
    client = Mock()
    client.collection_exists.return_value = True
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.recreate_collection(vector_size=768)

    client.collection_exists.assert_called_once_with(collection_name="rag_chunks")
    client.delete_collection.assert_called_once_with(collection_name="rag_chunks")
    client.create_collection.assert_called_once()
    kwargs = client.create_collection.call_args.kwargs
    assert kwargs["collection_name"] == "rag_chunks"
    assert kwargs["vectors_config"]["dense"].size == 768
    assert kwargs["sparse_vectors_config"]["bm25"].modifier == "Idf"


def test_recreate_collection_creates_missing_collection():
    client = Mock()
    client.collection_exists.return_value = False
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.recreate_collection(vector_size=768)

    client.delete_collection.assert_not_called()
    client.create_collection.assert_called_once()


def test_upsert_chunk_sends_dense_and_sparse_vectors_and_minimal_payload():
    client = Mock()
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.upsert_chunk(
        source_name="football.md",
        chunk_index=1,
        text="Football text",
        embedding=[0.1, 0.2],
        sparse={"indices": [10, 20], "values": [2, 1]},
    )

    client.upsert.assert_called_once()
    kwargs = client.upsert.call_args.kwargs
    assert kwargs["collection_name"] == "rag_chunks"
    assert kwargs["wait"] is True
    point = kwargs["points"][0]
    assert point.vector["dense"] == [0.1, 0.2]
    assert point.vector["bm25"].indices == [10, 20]
    assert point.vector["bm25"].values == [2, 1]
    assert point.payload == {
        "source_name": "football.md",
        "text": "Football text",
    }


def test_upsert_chunk_uses_stable_id_for_same_source_and_index():
    client = Mock()
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.upsert_chunk(
        source_name="football.md", chunk_index=1, text="a", embedding=[0.1], sparse={"indices": [], "values": []}
    )
    repository.upsert_chunk(
        source_name="football.md", chunk_index=1, text="a", embedding=[0.1], sparse={"indices": [], "values": []}
    )

    first_id = client.upsert.call_args_list[0].kwargs["points"][0].id
    second_id = client.upsert.call_args_list[1].kwargs["points"][0].id
    assert first_id == second_id


def test_has_dense_match_returns_true_when_a_chunk_clears_the_floor():
    client = Mock()
    client.query_points.return_value = SimpleNamespace(points=[
        SimpleNamespace(payload={"source_name": "football.md", "text": "Football text"}, score=0.7),
    ])
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    assert repository.has_dense_match(embedding=[0.1, 0.2], score_threshold=0.6) is True
    kwargs = client.query_points.call_args.kwargs
    assert kwargs["collection_name"] == "rag_chunks"
    assert kwargs["query"] == [0.1, 0.2]
    assert kwargs["using"] == "dense"
    assert kwargs["limit"] == 1
    assert kwargs["score_threshold"] == 0.6


def test_has_dense_match_returns_false_when_nothing_clears_the_floor():
    client = Mock()
    # Bare list (no .points wrapper), empty -> nothing relevant -> abstain.
    client.query_points.return_value = []
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    assert repository.has_dense_match(embedding=[0.1, 0.2], score_threshold=0.6) is False


def test_query_chunks_runs_hybrid_prefetch_with_rrf_fusion():
    client = Mock()
    client.query_points.return_value = SimpleNamespace(points=[
        SimpleNamespace(payload={"source_name": "football.md", "text": "Football text"}, score=0.5),
    ])
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    result = repository.query_chunks(
        embedding=[0.1, 0.2],
        sparse={"indices": [10, 20], "values": [2, 1]},
        limit=5,
        score_threshold=0.6,
    )

    assert result == [
        {"source_name": "football.md", "text": "Football text", "score": 0.5},
    ]
    client.query_points.assert_called_once()
    kwargs = client.query_points.call_args.kwargs
    assert kwargs["collection_name"] == "rag_chunks"
    assert kwargs["limit"] == 5
    assert kwargs["query"].fusion == "Rrf"

    dense_prefetch, sparse_prefetch = kwargs["prefetch"]
    # The cosine floor gates the dense branch only; the sparse branch contributes unfiltered.
    assert dense_prefetch.query == [0.1, 0.2]
    assert dense_prefetch.using == "dense"
    assert dense_prefetch.limit == 5
    assert dense_prefetch.score_threshold == 0.6
    assert sparse_prefetch.query.indices == [10, 20]
    assert sparse_prefetch.query.values == [2, 1]
    assert sparse_prefetch.using == "bm25"
    assert sparse_prefetch.limit == 5
    assert sparse_prefetch.score_threshold is None


def test_query_chunks_handles_bare_point_list():
    client = Mock()
    # Some client versions return the points list directly rather than a wrapper object.
    client.query_points.return_value = [
        SimpleNamespace(payload=None, score=0.5),
    ]
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    assert repository.query_chunks(
        embedding=[0.1], sparse={"indices": [], "values": []}, limit=5, score_threshold=0.6
    ) == [
        {"source_name": None, "text": None, "score": 0.5},
    ]
