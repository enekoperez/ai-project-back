import os
import sys
import types


def _install_test_environment_defaults():
    os.environ.setdefault("FLASK_DEBUG", "false")
    os.environ.setdefault("AI_DB_CONNECTION_STRING", "mongodb://localhost:27017/test_ai_db")
    os.environ.setdefault("QDRANT_URL", "http://127.0.0.1:6333")
    os.environ.setdefault("QDRANT_COLLECTION_NAME", "rag_chunks")
    os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-api-key")
    os.environ.setdefault("GOOGLE_AI_API_KEY", "test-google-ai-api-key")
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-api-key")


def _install_ai_dependency_stubs():
    google_module = types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")
    genai_errors_module = types.ModuleType("google.genai.errors")
    genai_types_module = types.ModuleType("google.genai.types")

    class ClientError(Exception):
        def __init__(self, status=None):
            super().__init__(status)
            self.status = status

    class _Client:
        def __init__(self, *args, **kwargs):
            self.models = types.SimpleNamespace()
            self.caches = types.SimpleNamespace()

    def _typed_config(**kwargs):
        return kwargs

    genai_types_module.FunctionDeclaration = _typed_config
    genai_types_module.Schema = _typed_config
    genai_types_module.Type = types.SimpleNamespace(OBJECT="OBJECT", STRING="STRING")

    genai_errors_module.ClientError = ClientError
    genai_module.Client = _Client
    genai_module.errors = genai_errors_module
    genai_module.types = genai_types_module
    google_module.genai = genai_module

    mistral_module = types.ModuleType("mistralai")
    mistral_client_module = types.ModuleType("mistralai.client")
    mistral_errors_module = types.ModuleType("mistralai.client.errors")
    mistral_sdkerror_module = types.ModuleType("mistralai.client.errors.sdkerror")

    class Mistral:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace()

    class SDKError(Exception):
        pass

    mistral_client_module.Mistral = Mistral
    mistral_sdkerror_module.SDKError = SDKError

    openai_module = types.ModuleType("openai")
    openai_types_module = types.ModuleType("openai.types")
    openai_responses_module = types.ModuleType("openai.types.responses")

    class OpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = types.SimpleNamespace()

    openai_module.OpenAI = OpenAI

    for name in (
        "EasyInputMessageParam",
        "ResponseInputTextContentParam",
        "ResponseInputFileContentParam",
        "ResponseInputImageContentParam",
        "ResponseFormatTextJSONSchemaConfigParam",
    ):
        setattr(openai_responses_module, name, dict)

    sys.modules.setdefault("google", google_module)
    sys.modules.setdefault("google.genai", genai_module)
    sys.modules.setdefault("google.genai.errors", genai_errors_module)
    sys.modules.setdefault("google.genai.types", genai_types_module)
    sys.modules.setdefault("mistralai", mistral_module)
    sys.modules.setdefault("mistralai.client", mistral_client_module)
    sys.modules.setdefault("mistralai.client.errors", mistral_errors_module)
    sys.modules.setdefault("mistralai.client.errors.sdkerror", mistral_sdkerror_module)
    sys.modules.setdefault("openai", openai_module)
    sys.modules.setdefault("openai.types", openai_types_module)
    sys.modules.setdefault("openai.types.responses", openai_responses_module)


def _install_qdrant_dependency_stubs():
    try:
        import qdrant_client  # noqa: F401
        import qdrant_client.models  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    qdrant_client_module = types.ModuleType("qdrant_client")
    qdrant_models_module = types.ModuleType("qdrant_client.models")

    class QdrantClient:
        def __init__(self, *args, **kwargs):
            pass

    class _Distance:
        COSINE = "Cosine"

    class PointStruct:
        def __init__(self, id, vector, payload):
            self.id = id
            self.vector = vector
            self.payload = payload

    class VectorParams:
        def __init__(self, size, distance):
            self.size = size
            self.distance = distance

    qdrant_client_module.QdrantClient = QdrantClient
    qdrant_models_module.Distance = _Distance
    qdrant_models_module.PointStruct = PointStruct
    qdrant_models_module.VectorParams = VectorParams

    sys.modules.setdefault("qdrant_client", qdrant_client_module)
    sys.modules.setdefault("qdrant_client.models", qdrant_models_module)


_install_test_environment_defaults()
_install_ai_dependency_stubs()
_install_qdrant_dependency_stubs()
