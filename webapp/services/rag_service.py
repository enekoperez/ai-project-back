import math

from loguru import logger

from webapp import config
from webapp.repositories.rag_chunk_repository import RagChunkRepository
from webapp.services.ai_service import AiService
from webapp.services.doc_service import DocService

_MAX_CHUNK_CHARS = 1600  # Text	- Supports up to 8,192 tokens.
_TOP_K = 5  # Retrieval size tradeoff: 3 is lean, 5 is better for multi-step help questions, 8 is broader but noisier.
_MIN_SCORE = 0.6  # Cosine-similarity floor: 0.5 lenient, 0.6 balanced, 0.7 strict. Chunks below this are dropped.


class RagService:

    def __init__(self):
        self.ai_service = AiService()
        self.rag_chunk_repository = RagChunkRepository()
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

    def sync(self):  # TODO: Batch embedding
        model = config.Config.DEFAULT_GOOGLE_AI_EMBEDDING_MODEL

        # Get current source files from Cloud.
        source_files = self.doc_service.get_source_files()

        # Delete DB chunks for files that no longer exist in Cloud.
        source_names = {source_file["source_name"] for source_file in source_files}
        self.rag_chunk_repository.delete_source_names_not_in(source_names=source_names)

        # Keep one existing DB chunk per source_name to compare fingerprints.
        existing_rag_chunk_by_source_name = {}
        for rag_chunk in self.rag_chunk_repository.get_source_name_source_fingerprint_and_model():
            if rag_chunk.source_name not in existing_rag_chunk_by_source_name:
                existing_rag_chunk_by_source_name[rag_chunk.source_name] = rag_chunk

        # Download, chunk, embed, and save ONLY new or changed source files.
        for source_file in source_files:
            source_name = source_file["source_name"]
            existing_chunk = existing_rag_chunk_by_source_name.get(source_name)
            if (existing_chunk
                    and existing_chunk.source_fingerprint == source_file["source_fingerprint"]
                    and existing_chunk.model == model):
                continue

            text = self.doc_service.get_source_text(source_file=source_file)
            self.rag_chunk_repository.delete_chunks_by_source_name(source_name=source_name)
            if text:
                for index, chunk_text in enumerate(self._chunk_markdown(text=text)):
                    embedding, model = self.ai_service.embed(
                        text=self._prepare_document(title=source_name, content=chunk_text)
                    )
                    self.rag_chunk_repository.create(
                        source_name=source_name,
                        source_fingerprint=source_file["source_fingerprint"],
                        chunk_index=index,
                        text=chunk_text,
                        embedding=embedding,
                        model=model,
                    )

        logger.info("[rag.sync] end")
        return True

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
        question_embedding, model = self.ai_service.embed(text=self._prepare_query(query=question))

        scored_chunks = []
        for chunk in self.rag_chunk_repository.get_all_by_model(model=model):
            score = self._cosine_similarity(question_embedding, chunk.embedding)
            if score >= _MIN_SCORE:
                scored_chunks.append({"source_name": chunk.source_name, "text": chunk.text, "score": score})

        top_chunks = sorted(scored_chunks, key=lambda x: x["score"], reverse=True)[:_TOP_K]
        return top_chunks

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if not norm_a or not norm_b:
            return 0
        return dot / (norm_a * norm_b)
