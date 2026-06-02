from webapp.models.rag_chunk_domain import RagChunk


class RagChunkRepository:

    def create(self, source_name, source_fingerprint, chunk_index, text, embedding, model):
        return RagChunk.objects.create(
            source_name=source_name,
            source_fingerprint=source_fingerprint,
            chunk_index=chunk_index,
            text=text,
            embedding=embedding,
            model=model,
        )

    def get_all_by_model(self, model):
        return RagChunk.objects(model=model)

    def get_source_name_source_fingerprint_and_model(self):
        return RagChunk.objects.only("source_name", "source_fingerprint", "model").all()

    def delete_source_names_not_in(self, source_names):
        if source_names:
            return RagChunk.objects(source_name__nin=list(source_names)).delete()
        return RagChunk.objects.delete()

    def delete_chunks_by_source_name(self, source_name):
        return RagChunk.objects(source_name=source_name).delete()
