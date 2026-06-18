import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from webapp import config

_DENSE = "dense"
_BM25 = "bm25"


class QdrantRepository:

    def __init__(self, client=None, collection_name=None):
        self.client = client or QdrantClient(url=config.Config.QDRANT_URL)
        self.collection_name = collection_name or config.Config.QDRANT_COLLECTION_NAME

    def recreate_collection(self, vector_size):
        if self.client.collection_exists(collection_name=self.collection_name):
            self.client.delete_collection(collection_name=self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={_DENSE: VectorParams(size=vector_size, distance=Distance.COSINE)},
            # Qdrant computes IDF server-side, so we only send raw term-frequency sparse vectors.
            sparse_vectors_config={_BM25: SparseVectorParams(modifier=Modifier.IDF)},
        )

    def upsert_chunk(self, source_name, chunk_index, text, embedding, sparse):
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
                    vector={
                        _DENSE: embedding,
                        _BM25: SparseVector(indices=sparse["indices"], values=sparse["values"]),
                    },
                    payload={
                        "source_name": source_name,
                        "text": text,
                    },
                )
            ],
        )

    def has_dense_match(self, embedding, score_threshold):
        """True if any chunk clears the cosine floor — the semantic-relevance gate for abstention."""
        result = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            using=_DENSE,
            limit=1,
            score_threshold=score_threshold,
        )
        points = result.points if hasattr(result, "points") else result
        return bool(points)

    def query_chunks(self, embedding, sparse, limit, score_threshold):
        # Hybrid search: dense cosine + BM25 sparse, fused server-side by Reciprocal Rank Fusion.
        # The cosine floor gates the dense branch only; BM25 contributes lexical hits unfiltered.
        result = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=embedding, using=_DENSE, limit=limit, score_threshold=score_threshold),
                Prefetch(
                    query=SparseVector(indices=sparse["indices"], values=sparse["values"]),
                    using=_BM25,
                    limit=limit,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
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
