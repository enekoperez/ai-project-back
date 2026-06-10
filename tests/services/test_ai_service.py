from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai.errors import ClientError
from mistralai.client.errors.sdkerror import SDKError

from webapp import config
from webapp.services.ai_service import AiService, UnsupportedGoogleMimeTypeError


def make_service():
    return AiService()


def make_part(text=None, thought=None, function_call=None):
    return SimpleNamespace(text=text, thought=thought, function_call=function_call)


def make_google_response(parts, text="answer"):
    return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))], text=text)


def disable_sleep(monkeypatch):
    monkeypatch.setattr("webapp.services.ai_service.time.sleep", Mock())


# call_llm dispatcher

def test_call_llm_returns_first_provider_success():
    service = make_service()
    service._call_google = Mock(return_value=("resp", "model-g", 1.0, "thoughts", []))

    response, model, temperature, thoughts, tool_calls, duration_ms = service.call_llm("sys", "user")

    assert (response, model, temperature, thoughts, tool_calls) == ("resp", "model-g", 1.0, "thoughts", [])
    assert isinstance(duration_ms, int)
    service._call_google.assert_called_once()


def test_call_llm_retries_provider_until_success(monkeypatch):
    disable_sleep(monkeypatch)
    service = make_service()
    service._call_google = Mock(side_effect=[RuntimeError("boom"), RuntimeError("boom"), ("resp", "m", 1.0, None, [])])

    response, *_ = service.call_llm("sys", "user")

    assert response == "resp"
    assert service._call_google.call_count == 3


def test_call_llm_falls_back_to_next_provider_after_retries(monkeypatch):
    disable_sleep(monkeypatch)
    service = make_service()
    service._call_google = Mock(side_effect=RuntimeError("boom"))
    service._call_mistral = Mock(return_value=("resp-m", "m", 0.0, None, []))
    service._call_openai = Mock()

    response, *_ = service.call_llm("sys", "user")

    assert response == "resp-m"
    assert service._call_google.call_count == 3
    service._call_mistral.assert_called_once()
    service._call_openai.assert_not_called()


def test_call_llm_chat_only_uses_google(monkeypatch):
    disable_sleep(monkeypatch)
    service = make_service()
    service._call_google = Mock(side_effect=RuntimeError("boom"))
    service._call_mistral = Mock()
    service._call_openai = Mock()

    with pytest.raises(RuntimeError, match="All AI providers unavailable") as exc_info:
        service.call_llm("sys", "user", is_chat=True)

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert service._call_google.call_count == 3
    service._call_mistral.assert_not_called()
    service._call_openai.assert_not_called()


def test_call_llm_rag_only_uses_google(monkeypatch):
    disable_sleep(monkeypatch)
    service = make_service()
    service._call_google = Mock(side_effect=RuntimeError("boom"))
    service._call_mistral = Mock()

    with pytest.raises(RuntimeError, match="All AI providers unavailable"):
        service.call_llm("sys", "user", is_rag=True)

    service._call_mistral.assert_not_called()


def test_call_llm_skips_google_without_retry_on_unsupported_mime_type(monkeypatch):
    sleep = Mock()
    monkeypatch.setattr("webapp.services.ai_service.time.sleep", sleep)
    service = make_service()
    service._call_google = Mock(side_effect=UnsupportedGoogleMimeTypeError("docx"))
    service._call_mistral = Mock(return_value=("resp-m", "m", 0.0, None, []))

    response, *_ = service.call_llm("sys", "user")

    assert response == "resp-m"
    service._call_google.assert_called_once()
    sleep.assert_not_called()


# embed

def test_embed_returns_empty_list_without_calling_client():
    service = make_service()
    service.google_ai_client.models.embed_content = Mock()

    assert service.embed([], dimensions=768) == []
    service.google_ai_client.models.embed_content.assert_not_called()


def test_embed_returns_embedding_values():
    service = make_service()
    result = SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1, 0.2]), SimpleNamespace(values=[0.3, 0.4])])
    service.google_ai_client.models.embed_content = Mock(return_value=result)

    assert service.embed(["one", "two"], dimensions=768) == [[0.1, 0.2], [0.3, 0.4]]
    kwargs = service.google_ai_client.models.embed_content.call_args.kwargs
    assert kwargs["model"] == config.Config.DEFAULT_GOOGLE_AI_EMBEDDING_MODEL
    assert kwargs["config"] == {"output_dimensionality": 768}


# _call_google

def test_call_google_returns_text_and_thoughts():
    service = make_service()
    response = make_google_response(
        parts=[make_part(text="pondering", thought=True), make_part(text="final")],
        text="final",
    )
    service.google_ai_client.models.generate_content = Mock(return_value=response)

    text, model, temperature, thoughts, tool_calls = service._call_google("sys", "user")

    assert text == "final"
    assert model == config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL
    assert temperature == 1.0
    assert thoughts == "pondering"
    assert tool_calls == []
    request = service.google_ai_client.models.generate_content.call_args.kwargs
    assert request["config"]["system_instruction"] == "sys"
    assert request["contents"][-1].parts[-1].text == "user"


def test_call_google_rag_lowers_temperature():
    service = make_service()
    service.google_ai_client.models.generate_content = Mock(
        return_value=make_google_response(parts=[make_part(text="final")], text="final")
    )

    _, _, temperature, _, _ = service._call_google("sys", "user", is_rag=True)

    assert temperature == 0.2


def test_call_google_chat_replays_history():
    service = make_service()
    service.google_ai_client.models.generate_content = Mock(
        return_value=make_google_response(parts=[make_part(text="final")], text="final")
    )
    history = [{"role": "user", "text": "hi"}, {"role": "model", "text": "hello"}]

    _, _, temperature, _, _ = service._call_google("sys", "user", is_chat=True, history=history)

    assert temperature == 1.0
    contents = service.google_ai_client.models.generate_content.call_args.kwargs["contents"]
    assert [(content.role, content.parts[0].text) for content in contents] == [
        ("user", "hi"), ("model", "hello"), ("user", "user"),
    ]


def test_call_google_passes_response_format_document_and_max_tokens():
    service = make_service()
    service.google_ai_client.models.generate_content = Mock(
        return_value=make_google_response(parts=[make_part(text="final")], text="final")
    )

    service._call_google(
        "sys", "user",
        response_format={"type": "object"},
        document_data={"url": "http://doc.pdf", "extension": "pdf"},
        max_output_tokens=512,
    )

    request = service.google_ai_client.models.generate_content.call_args.kwargs
    assert request["config"]["response_mime_type"] == "application/json"
    assert request["config"]["response_schema"] == {"type": "object"}
    assert request["config"]["max_output_tokens"] == 512
    document_part = request["contents"][-1].parts[0]
    assert (document_part.file_uri, document_part.mime_type) == ("http://doc.pdf", "application/pdf")


def test_call_google_dispatches_tool_calls_then_returns_answer():
    service = make_service()
    tool_turn = make_google_response(
        parts=[make_part(function_call=SimpleNamespace(name="get_weather", args={"city": "Bilbao"}))]
    )
    final_turn = make_google_response(parts=[make_part(text="sunny")], text="sunny")
    service.google_ai_client.models.generate_content = Mock(side_effect=[tool_turn, final_turn])
    get_weather = Mock(return_value={"temp": 20})

    text, _, _, _, tool_calls = service._call_google(
        "sys", "user",
        tool_declarations=[{"name": "get_weather"}],
        tool_dispatch={"get_weather": get_weather},
    )

    assert text == "sunny"
    assert tool_calls == [{"tool_hop": 0, "name": "get_weather", "args": {"city": "Bilbao"}}]
    get_weather.assert_called_once_with(city="Bilbao")
    assert service.google_ai_client.models.generate_content.call_count == 2
    # second request must carry the tool-call turn and the tool response back to the model
    second_contents = service.google_ai_client.models.generate_content.call_args_list[1].kwargs["contents"]
    assert second_contents[-2] is tool_turn.candidates[0].content
    assert second_contents[-1].parts[0].response == {"temp": 20}


def test_call_google_raises_when_tool_hop_limit_exceeded():
    service = make_service()
    tool_turn = make_google_response(
        parts=[make_part(function_call=SimpleNamespace(name="get_weather", args={}))]
    )
    service.google_ai_client.models.generate_content = Mock(return_value=tool_turn)

    with pytest.raises(RuntimeError, match="Tool hop limit exceeded"):
        service._call_google("sys", "user", tool_dispatch={"get_weather": Mock(return_value={})})

    assert service.google_ai_client.models.generate_content.call_count == 5


def test_call_google_raises_for_unsupported_extension():
    service = make_service()
    service.google_ai_client.models.generate_content = Mock()

    with pytest.raises(UnsupportedGoogleMimeTypeError):
        service._call_google("sys", "user", document_data={"url": "http://doc", "extension": "docx"})

    service.google_ai_client.models.generate_content.assert_not_called()


def test_call_google_uses_cached_content_instead_of_system_instruction():
    service = make_service()
    service.google_ai_client.models.generate_content = Mock(
        return_value=make_google_response(parts=[make_part(text="final")], text="final")
    )

    service._call_google("sys", "user", cache_name="caches/abc", tool_declarations=[{"name": "tool"}])

    request_config = service.google_ai_client.models.generate_content.call_args.kwargs["config"]
    assert request_config["cached_content"] == "caches/abc"
    assert "system_instruction" not in request_config
    assert "tools" not in request_config


# _call_mistral

def make_mistral_response(content="extracted"):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_call_mistral_sends_document_url_block():
    service = make_service()
    service.mistral_client.chat.complete = Mock(return_value=make_mistral_response())

    text, model, temperature, thoughts, tool_calls = service._call_mistral(
        "sys", "user", document_data={"url": "http://doc.pdf", "extension": "pdf"}
    )

    assert (text, thoughts, tool_calls) == ("extracted", None, [])
    assert temperature == 0.0
    messages = service.mistral_client.chat.complete.call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "sys"}
    assert messages[1]["content"][0] == {"type": "document_url", "document_url": "http://doc.pdf"}
    assert messages[1]["content"][1] == {"type": "text", "text": "user"}


def test_call_mistral_sends_image_url_block_for_images():
    service = make_service()
    service.mistral_client.chat.complete = Mock(return_value=make_mistral_response())

    service._call_mistral("sys", "user", document_data={"url": "http://pic.jpg", "extension": "jpg"})

    messages = service.mistral_client.chat.complete.call_args.kwargs["messages"]
    assert messages[1]["content"][0] == {"type": "image_url", "image_url": "http://pic.jpg"}


def test_call_mistral_wraps_response_format_as_strict_json_schema():
    service = make_service()
    service.mistral_client.chat.complete = Mock(return_value=make_mistral_response())

    service._call_mistral("sys", "user", response_format={"type": "object", "properties": {}})

    response_format = service.mistral_client.chat.complete.call_args.kwargs["response_format"]
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["additionalProperties"] is False


def test_call_mistral_wraps_sdk_error():
    service = make_service()
    service.mistral_client.chat.complete = Mock(side_effect=SDKError("down"))

    with pytest.raises(RuntimeError, match="Mistral service unavailable"):
        service._call_mistral("sys", "user")


# _call_openai

def test_call_openai_sends_file_block_and_text():
    service = make_service()
    service.openai_client.responses.create = Mock(return_value=SimpleNamespace(output_text="out"))

    text, model, temperature, thoughts, tool_calls = service._call_openai(
        "sys", "user", document_data={"url": "http://doc.pdf", "extension": "pdf"}
    )

    assert (text, thoughts, tool_calls) == ("out", None, [])
    assert temperature == 0.0
    kwargs = service.openai_client.responses.create.call_args.kwargs
    assert kwargs["instructions"] == "sys"
    content = kwargs["input"][0]["content"]
    assert content[0] == {"type": "input_file", "file_url": "http://doc.pdf"}
    assert content[1] == {"type": "input_text", "text": "user"}


def test_call_openai_sends_image_block_for_images():
    service = make_service()
    service.openai_client.responses.create = Mock(return_value=SimpleNamespace(output_text="out"))

    service._call_openai("sys", "user", document_data={"url": "http://pic.png", "extension": "png"})

    content = service.openai_client.responses.create.call_args.kwargs["input"][0]["content"]
    assert content[0] == {"type": "input_image", "image_url": "http://pic.png"}


def test_call_openai_wraps_response_format_as_strict_json_schema():
    service = make_service()
    service.openai_client.responses.create = Mock(return_value=SimpleNamespace(output_text="out"))

    service._call_openai("sys", "user", response_format={"type": "object", "properties": {}})

    text_format = service.openai_client.responses.create.call_args.kwargs["text"]["format"]
    assert text_format["strict"] is True
    assert text_format["schema"]["additionalProperties"] is False


# Google cache helpers

def test_google_get_cache_returns_name_and_create_time():
    service = make_service()
    service.google_ai_client.caches.get = Mock(return_value=SimpleNamespace(name="caches/abc", create_time="t1"))

    assert service.google_get_cache(cache_name="caches/abc") == ("caches/abc", "t1")
    service.google_ai_client.caches.get.assert_called_once_with(name="caches/abc")


def test_google_get_cache_returns_none_when_not_found():
    service = make_service()
    service.google_ai_client.caches.get = Mock(side_effect=ClientError(status="NOT_FOUND"))

    assert service.google_get_cache(cache_name="caches/abc") == (None, None)


def test_google_get_cache_raises_on_other_client_error():
    service = make_service()
    service.google_ai_client.caches.get = Mock(side_effect=ClientError(status="PERMISSION_DENIED"))

    with pytest.raises(RuntimeError, match="Cache error"):
        service.google_get_cache(cache_name="caches/abc")


def test_google_get_cache_skips_lookup_for_falsy_name():
    service = make_service()
    service.google_ai_client.caches.get = Mock()

    assert service.google_get_cache(cache_name=None) == (None, None)
    service.google_ai_client.caches.get.assert_not_called()


def test_google_delete_cache_deletes_existing_cache():
    service = make_service()
    service.google_ai_client.caches.get = Mock(return_value=SimpleNamespace(name="caches/abc", create_time="t1"))
    service.google_ai_client.caches.delete = Mock()

    assert service.google_delete_cache(cache_name="caches/abc") is True
    service.google_ai_client.caches.delete.assert_called_once_with(name="caches/abc")


def test_google_delete_cache_returns_false_when_missing():
    service = make_service()
    service.google_ai_client.caches.get = Mock(side_effect=ClientError(status="NOT_FOUND"))
    service.google_ai_client.caches.delete = Mock()

    assert service.google_delete_cache(cache_name="caches/abc") is False
    service.google_ai_client.caches.delete.assert_not_called()


def test_google_set_cache_creates_cache_with_ttl_and_tools():
    service = make_service()
    service.google_ai_client.caches.create = Mock(return_value=SimpleNamespace(name="caches/new", create_time="t2"))

    name, create_time = service.google_set_cache("sys", ttl_seconds=120, tool_declarations=[{"name": "tool"}])

    assert (name, create_time) == ("caches/new", "t2")
    cache_config = service.google_ai_client.caches.create.call_args.kwargs["config"]
    assert cache_config["system_instruction"] == "sys"
    assert cache_config["ttl"] == "120s"
    assert "tools" in cache_config


def test_google_set_cache_returns_none_for_invalid_argument():
    service = make_service()
    service.google_ai_client.caches.create = Mock(side_effect=ClientError(status="INVALID_ARGUMENT"))

    assert service.google_set_cache("sys") == (None, None)


def test_google_set_cache_raises_on_other_client_error():
    service = make_service()
    service.google_ai_client.caches.create = Mock(side_effect=ClientError(status="PERMISSION_DENIED"))

    with pytest.raises(RuntimeError, match="Cache error"):
        service.google_set_cache("sys")
