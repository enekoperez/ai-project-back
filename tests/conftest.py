import sys
import types


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


_install_ai_dependency_stubs()
