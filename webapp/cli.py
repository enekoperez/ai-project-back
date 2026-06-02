from webapp.services.rag_service import RagService


def init_cli(flask_app):
    @flask_app.cli.command("rag-sync")
    def rag_sync():
        """Re-sync the RAG store."""
        RagService().sync()
