import json
import re
import zlib
from collections import Counter

from loguru import logger

from webapp.prompts import rerank_prompt
from webapp.repositories.qdrant_repository import QdrantRepository
from webapp.services.ai_service import AiService
from webapp.services.doc_service import DocService

_EMBEDDING_DIMENSIONS = 768
_EMBEDDING_BATCH_SIZE = 50
_MAX_CHUNK_CHARS = 1600  # Text	- Supports up to 8,192 tokens.
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")  # Markdown heading: 1-6 '#' followed by the title.
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")  # BM25 tokenizer: lowercase alphanumeric runs.
_CHUNK_OVERLAP_CHARS = round(_MAX_CHUNK_CHARS * 0.15)  # Consecutive chunks repeat this much text so facts on a boundary survive in one piece.
_TOP_K = 5  # Retrieval size tradeoff: 3 is lean, 5 is better for multi-step help questions, 8 is broader but noisier.
_RERANK_CANDIDATES = 20  # Wider pool fetched from Qdrant; the reranker reorders it down to _TOP_K.
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
                sparse=self._sparse_encode(chunk["text"]),
            )

        logger.info("[rag.sync] end")
        return True

    @staticmethod
    def _sparse_encode(text):
        """Builds a BM25 term-frequency sparse vector; Qdrant applies IDF server-side.

        Token ids use crc32 (stable across runs, unlike Python's randomized hash) so a term
        maps to the same index at indexing and query time.
        """
        counts = Counter(zlib.crc32(token.encode("utf-8")) for token in _TOKEN_PATTERN.findall(text.lower()))
        return {"indices": list(counts.keys()), "values": list(counts.values())}

    @staticmethod
    def _batch(items, size):
        for index in range(0, len(items), size):
            yield items[index:index + size]

    @staticmethod
    def _chunk_markdown(text: str) -> list[str]:
        """Splits a markdown document into size-limited chunks, each prefixed with its heading path.

        Example: "# A\\n\\nHi\\n\\n## B\\n\\nYo" -> ["A\\n\\nHi", "A > B\\n\\nYo"]
        """
        text = text.strip()  # Removes whitespace from the start and end of the full text.
        if not text:  # If the text is empty after stripping, returns an empty list.
            return []

        response = []
        for heading_path, body in RagService._split_sections(text):
            for piece in RagService._split_body(body):
                # Prepends the heading path (e.g. "Football > Core Rules") so each chunk keeps its document context.
                response.append(f"{heading_path}\n\n{piece}" if heading_path else piece)
        return response

    @staticmethod
    def _split_sections(text: str) -> list[tuple[str, str]]:
        """Groups the document's text under its heading path, walking it line by line.

        Example: "# A\\n\\nHi\\n\\n## B\\n\\nYo" -> [("A", "Hi"), ("A > B", "Yo")]
        """
        sections = []
        titles_by_level = {}  # Current heading per level, e.g. {1: "Football", 2: "Core Rules"}.
        body_lines = []
        in_code_fence = False

        def flush() -> None:
            """Closes the section being accumulated: appends (heading path, body) to sections and clears body_lines.

            Example: titles_by_level={1: "A"}, body_lines=["Hi"] -> sections grows with ("A", "Hi")
            """
            body = "\n".join(body_lines).strip()
            if body:
                heading_path = " > ".join(titles_by_level[level] for level in sorted(titles_by_level))
                sections.append((heading_path, body))
            body_lines.clear()

        for line in text.splitlines():
            if line.lstrip().startswith("```"):  # Inside fenced code blocks a leading '#' is a comment, not a heading.
                in_code_fence = not in_code_fence
            heading = None if in_code_fence else _HEADING_PATTERN.match(line)
            if heading:
                flush()  # The accumulated body belongs to the previous heading path.
                level = len(heading.group(1))
                # A new heading replaces its level and resets every deeper level.
                titles_by_level = {lvl: title for lvl, title in titles_by_level.items() if lvl < level}
                titles_by_level[level] = heading.group(2)
            else:
                body_lines.append(line)
        flush()
        return sections

    @staticmethod
    def _split_body(body: str) -> list[str]:
        """Packs paragraphs into chunks of up to _MAX_CHUNK_CHARS, overlapping consecutive chunks.

        Example: "P1.\\n\\nP2." -> ["P1.\\n\\nP2."] (or ["P1. ...", "...tail P2."] if over the limit)
        """
        paragraphs = []
        # Paragraphs are separated by blank lines; filter(None, ...) drops whitespace-only pieces.
        for paragraph in filter(None, (p.strip() for p in re.split(r"\n\s*\n", body))):
            if len(paragraph) <= _MAX_CHUNK_CHARS:
                paragraphs.append(paragraph)
            else:
                paragraphs.extend(RagService._split_long_paragraph(paragraph))

        chunks = []
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}" if current else paragraph
            if len(candidate) <= _MAX_CHUNK_CHARS:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                    # The next chunk starts with the tail of this one so boundary facts appear whole in at least one chunk.
                    paragraph = f"{RagService._overlap_tail(current)}\n\n{paragraph}"
                current = paragraph
        if current:
            chunks.append(current)
        return chunks

    @staticmethod
    def _split_long_paragraph(paragraph: str) -> list[str]:
        """Splits an oversized paragraph at word boundaries, never mid-word.

        Example: "aaa bbb ccc" (limit 7) -> ["aaa bbb", "ccc"]
        """
        parts = []
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if len(candidate) <= _MAX_CHUNK_CHARS:
                current = candidate
            else:
                if current:
                    parts.append(current)
                current = word  # A single word longer than the limit stays whole as its own oversized part.
        if current:
            parts.append(current)
        return parts

    @staticmethod
    def _overlap_tail(text: str) -> str:
        """Returns the last ~_CHUNK_OVERLAP_CHARS of the text, cut on a word boundary.

        Example: "one two three four" (overlap 9) -> "hree four" -> "four"
        """
        if len(text) <= _CHUNK_OVERLAP_CHARS:
            return text
        tail = text[-_CHUNK_OVERLAP_CHARS:]
        space_index = tail.find(" ")  # Drops the first partial word so the overlap starts on a word boundary.
        return tail[space_index + 1:] if space_index != -1 else tail

    def get_top_chunks(self, question):
        question_embedding = self.ai_service.embed(
            texts=[self._prepare_query(query=question)],
            dimensions=_EMBEDDING_DIMENSIONS
        )[0]
        candidates = self.qdrant_repository.query_chunks(
            embedding=question_embedding,
            sparse=self._sparse_encode(question),
            limit=_RERANK_CANDIDATES,
            score_threshold=_MIN_SCORE,
        )
        return self._rerank(query=question, chunks=candidates)

    def _rerank(self, query, chunks):
        if len(chunks) <= _TOP_K:  # Nothing to refine — skip the LLM call.
            return chunks

        # A rerank failure must never break or empty retrieval: fall back to the hybrid order.
        try:
            response, *_ = self.ai_service.call_llm(
                system_prompt=rerank_prompt.build_system_prompt(),
                user_prompt=rerank_prompt.build_user_prompt(query=query, chunks=chunks),
                response_format=rerank_prompt.response_format(),
                is_rag=True,
                max_output_tokens=200,
            )
            indices = json.loads(response)["indices"]
        except Exception:
            logger.exception("[rag.rerank] rerank failed; using hybrid order")
            return chunks[:_TOP_K]

        seen = set()
        reranked = []
        for index in indices:
            if isinstance(index, int) and 0 <= index < len(chunks) and index not in seen:
                seen.add(index)
                reranked.append(chunks[index])
        # Reranking may only reorder, never shrink recall: backfill any candidates the LLM
        # dropped, in their original hybrid order, so we always return the full top _TOP_K.
        reranked.extend(chunk for index, chunk in enumerate(chunks) if index not in seen)
        return reranked[:_TOP_K]
