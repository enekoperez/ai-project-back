from flask import Blueprint, jsonify

from webapp.services.rag_service import RagService

rag = Blueprint("rag", __name__)
rag_service = RagService()


@rag.route("sync", methods=["POST"])
def sync():
    # TODO: move RAG sync to a CLI command instead of exposing it as an HTTP endpoint.
    response = rag_service.sync()
    return jsonify({"synced": response}), 200
