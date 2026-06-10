from loguru import logger

from webapp.repositories.qdrant_repository import QdrantRepository
from webapp.services.ai_service import AiService
from webapp.services.doc_service import DocService

_EMBEDDING_DIMENSIONS = 768
_EMBEDDING_BATCH_SIZE = 50
_MAX_CHUNK_CHARS = 1600  # Text	- Supports up to 8,192 tokens.
_TOP_K = 5  # Retrieval size tradeoff: 3 is lean, 5 is better for multi-step help questions, 8 is broader but noisier.
_MIN_SCORE = 0.6  # Cosine-similarity floor: 0.5 lenient, 0.6 balanced, 0.7 strict. Chunks below this are dropped.


class RagService:

    def __init__(self):
        self.ai_service = AiService()
        self.qdrant_repository = QdrantRepository()
        self.doc_service = DocService()

    # Generate embedding for a task's query. Use your correct task here:
    @staticmethod
    def _prepare_query(query):
        # return f"task: search result | query: {query}"  # Search query
        return f"task: question answering | query: {query}"  # Question answering
        # return f"task: fact checking | query: {query}"  # Fact checking
        # return f"task: code retrieval | query: {query}"  # Code retrieval

    # Generate embedding for document of an asymmetric retrieval task:
    @staticmethod
    def _prepare_document(content, title=None):
        if title is None:
            title = "none"
        return f"title: {title} | text: {content}"

    def sync(self):
        source_files = self.doc_service.get_source_files()

        chunks = []
        for source_file in source_files:
            source_name = source_file["source_name"]
            text = self.doc_service.get_source_text(source_file=source_file)
            if text:
                for index, chunk_text in enumerate(self._chunk_markdown(text=text)):
                    chunks.append({
                        "source_name": source_name,
                        "chunk_index": index,
                        "text": chunk_text,
                        "text_to_embed": self._prepare_document(title=source_name, content=chunk_text),
                    })

        embedded_chunks = []
        for batch in self._batch(chunks, size=_EMBEDDING_BATCH_SIZE):
            embeddings = self.ai_service.embed(
                texts=[chunk["text_to_embed"] for chunk in batch],
                dimensions=_EMBEDDING_DIMENSIONS,
            )

            for chunk, embedding in zip(batch, embeddings):
                embedded_chunks.append((chunk, embedding))

        self.qdrant_repository.recreate_collection(vector_size=_EMBEDDING_DIMENSIONS)

        for chunk, embedding in embedded_chunks:
            self.qdrant_repository.upsert_chunk(
                source_name=chunk["source_name"],
                chunk_index=chunk["chunk_index"],
                text=chunk["text"],
                embedding=embedding,
            )

        logger.info("[rag.sync] end")
        return True

    @staticmethod
    def _batch(items, size):
        for index in range(0, len(items), size):
            yield items[index:index + size]

    @staticmethod
    def _chunk_markdown(text):  # TODO: optimize
        text = text.strip()  # Removes whitespace from the start and end of the full text.
        if not text:  # If the text is empty after stripping, returns an empty list.
            return []

        response = []
        for i in range(0, len(text), _MAX_CHUNK_CHARS):  # Cuts the text into pieces of maximum _MAX_CHUNK_CHARS characters.
            response.append(text[i:i + _MAX_CHUNK_CHARS])
        # Returns those pieces as a list.
        return response

    def get_top_chunks(self, question):
        question_embedding = self.ai_service.embed(
            texts=[self._prepare_query(query=question)],
            dimensions=_EMBEDDING_DIMENSIONS
        )[0]
        top_chunks = self.qdrant_repository.query_chunks(
            embedding=question_embedding,
            limit=_TOP_K,
            score_threshold=_MIN_SCORE,
        )
        return top_chunks
