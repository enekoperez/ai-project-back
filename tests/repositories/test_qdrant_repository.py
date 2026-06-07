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
    assert client.create_collection.call_args.kwargs["collection_name"] == "rag_chunks"
    assert client.create_collection.call_args.kwargs["vectors_config"].size == 768


def test_recreate_collection_creates_missing_collection():
    client = Mock()
    client.collection_exists.return_value = False
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.recreate_collection(vector_size=768)

    client.delete_collection.assert_not_called()
    client.create_collection.assert_called_once()


def test_upsert_chunk_sends_vector_and_minimal_payload():
    client = Mock()
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    repository.upsert_chunk(
        source_name="football.md",
        chunk_index=1,
        text="Football text",
        embedding=[0.1, 0.2],
    )

    client.upsert.assert_called_once()
    kwargs = client.upsert.call_args.kwargs
    assert kwargs["collection_name"] == "rag_chunks"
    assert kwargs["wait"] is True
    point = kwargs["points"][0]
    assert point.vector == [0.1, 0.2]
    assert point.payload == {
        "source_name": "football.md",
        "text": "Football text",
    }


def test_query_chunks_maps_qdrant_points_to_prompt_chunks():
    client = Mock()
    client.query_points.return_value = SimpleNamespace(points=[
        SimpleNamespace(payload={"source_name": "football.md", "text": "Football text"}, score=0.9),
    ])
    repository = QdrantRepository(client=client, collection_name="rag_chunks")

    assert repository.query_chunks(embedding=[0.1, 0.2], limit=5, score_threshold=0.6) == [
        {"source_name": "football.md", "text": "Football text", "score": 0.9},
    ]
    client.query_points.assert_called_once_with(
        collection_name="rag_chunks",
        query=[0.1, 0.2],
        limit=5,
        score_threshold=0.6,
    )
