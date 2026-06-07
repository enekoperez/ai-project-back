import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from webapp import config


class QdrantRepository:

    def __init__(self, client=None, collection_name=None):
        self.client = client or QdrantClient(url=config.Config.QDRANT_URL)
        self.collection_name = collection_name or config.Config.QDRANT_COLLECTION_NAME

    def recreate_collection(self, vector_size):
        if self.client.collection_exists(collection_name=self.collection_name):
            self.client.delete_collection(collection_name=self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert_chunk(self, source_name, chunk_index, text, embedding):
        point_id = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{source_name}:{chunk_index}",
        ))
        return self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "source_name": source_name,
                        "text": text,
                    },
                )
            ],
        )

    def query_chunks(self, embedding, limit, score_threshold):
        result = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
            score_threshold=score_threshold,
        )
        points = result.points if hasattr(result, "points") else result
        chunks = []
        for point in points:
            payload = point.payload or {}
            chunks.append({
                "source_name": payload.get("source_name"),
                "text": payload.get("text"),
                "score": point.score,
            })
        return chunks
