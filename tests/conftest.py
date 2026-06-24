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
    os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")


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

    class _Part:
        def __init__(self, text=None, thought=None, function_call=None, **kwargs):
            self.text = text
            self.thought = thought
            self.function_call = function_call
            for key, value in kwargs.items():
                setattr(self, key, value)

        @classmethod
        def from_text(cls, text):
            return cls(text=text)

        @classmethod
        def from_uri(cls, file_uri, mime_type):
            return cls(file_uri=file_uri, mime_type=mime_type)

        @classmethod
        def from_function_response(cls, name, response):
            return cls(name=name, response=response)

    class _Content:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []

    genai_types_module.FunctionDeclaration = _typed_config
    genai_types_module.Schema = _typed_config
    genai_types_module.Type = types.SimpleNamespace(OBJECT="OBJECT", STRING="STRING")
    genai_types_module.Part = _Part
    genai_types_module.Content = _Content
    genai_types_module.Tool = _typed_config
    genai_types_module.ThinkingConfig = _typed_config
    genai_types_module.GenerateContentConfig = _typed_config
    genai_types_module.EmbedContentConfig = _typed_config
    genai_types_module.CreateCachedContentConfig = _typed_config
    genai_types_module.ThinkingLevel = types.SimpleNamespace(MINIMAL="MINIMAL", MEDIUM="MEDIUM")
    genai_types_module.MediaResolution = types.SimpleNamespace(
        MEDIA_RESOLUTION_MEDIUM="MEDIA_RESOLUTION_MEDIUM"
    )

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

    class SparseVectorParams:
        def __init__(self, modifier=None):
            self.modifier = modifier

    class SparseVector:
        def __init__(self, indices, values):
            self.indices = indices
            self.values = values

    class Prefetch:
        def __init__(self, query=None, using=None, limit=None, score_threshold=None):
            self.query = query
            self.using = using
            self.limit = limit
            self.score_threshold = score_threshold

    class FusionQuery:
        def __init__(self, fusion=None):
            self.fusion = fusion

    class _Fusion:
        RRF = "Rrf"

    class _Modifier:
        IDF = "Idf"

    qdrant_client_module.QdrantClient = QdrantClient
    qdrant_models_module.Distance = _Distance
    qdrant_models_module.PointStruct = PointStruct
    qdrant_models_module.VectorParams = VectorParams
    qdrant_models_module.SparseVectorParams = SparseVectorParams
    qdrant_models_module.SparseVector = SparseVector
    qdrant_models_module.Prefetch = Prefetch
    qdrant_models_module.FusionQuery = FusionQuery
    qdrant_models_module.Fusion = _Fusion
    qdrant_models_module.Modifier = _Modifier

    sys.modules.setdefault("qdrant_client", qdrant_client_module)
    sys.modules.setdefault("qdrant_client.models", qdrant_models_module)


_install_test_environment_defaults()
_install_ai_dependency_stubs()
_install_qdrant_dependency_stubs()
