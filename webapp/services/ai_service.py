import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from loguru import logger
from mistralai.client import Mistral
from mistralai.client.errors.sdkerror import SDKError
from openai import OpenAI
from openai.types.responses import EasyInputMessageParam, ResponseInputTextContentParam, ResponseInputFileContentParam, \
    ResponseInputImageContentParam, ResponseFormatTextJSONSchemaConfigParam

from webapp import config


class UnsupportedGoogleMimeTypeError(Exception):
    """Raised when a file extension has no Google MIME type mapping."""


_MAX_RETRIES = 3
_RETRY_DELAY_S = 3
_HOP_RANGE = 5  # TODO: 5 ?????


class AiService:

    def __init__(self):
        self.image_extensions = ['jpg', 'jpeg', 'png']
        self.google_mime_types_mapping = {
            # Text file types
            'html': 'text/html',
            'css': 'text/css',
            'txt': 'text/plain',
            'xml': 'text/xml',
            'csv': 'text/csv',
            'rtf': 'text/rtf',
            'js': 'text/javascript',
            # Application file types
            'json': 'application/json',
            'pdf': 'application/pdf',
            # Image file types
            'bmp': 'image/bmp',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
        }
        self.mistral_client = Mistral(api_key=config.Config.MISTRAL_API_KEY)
        self.google_ai_client = genai.Client(api_key=config.Config.GOOGLE_AI_API_KEY)
        self.openai_client = OpenAI(api_key=config.Config.OPENAI_API_KEY)

    def embed(self, text, dimensions: int = 768):  # dimensions: 768, 1536, or 3072
        model = config.Config.DEFAULT_GOOGLE_AI_EMBEDDING_MODEL
        result = self.google_ai_client.models.embed_content(
            model=model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=dimensions),
        )
        return result.embeddings[0].values, model

    def _providers(self, is_chat, is_rag):
        if is_chat or is_rag:
            return [self._call_google]
        return [self._call_google, self._call_mistral, self._call_openai]

    def call_llm(self, system_prompt, user_prompt,
                 response_format=None,
                 document_data=None,  # {'url': ..., 'extension': ...}
                 max_output_tokens=None,
                 is_chat=False,
                 is_rag=False,
                 history=None,
                 cache_name=None,
                 tool_declarations=None,  # list[types.FunctionDeclaration]
                 tool_dispatch=None,  # {name: callable}
                 ):
        starting_time = time.time()
        kwargs = {k: v for k, v in locals().items() if k != 'self'}  # forward method's params to provider, except self
        last_exc = None
        for provider in self._providers(is_chat=is_chat, is_rag=is_rag):
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    response, model, temperature, thoughts, tool_calls = provider(**kwargs)
                    duration_ms = int((time.time() - starting_time) * 1000)
                    return response, model, temperature, thoughts, tool_calls, duration_ms
                except Exception as e:
                    logger.exception("AI provider call failed")
                    if isinstance(e, UnsupportedGoogleMimeTypeError):  # Extension not supported by this provider — skip.
                        break
                    last_exc = e
                    if attempt < _MAX_RETRIES:
                        time.sleep(_RETRY_DELAY_S)
        raise RuntimeError('All AI providers unavailable') from last_exc

    def _call_mistral(self, system_prompt, user_prompt,
                      response_format=None,
                      document_data=None,  # {'url': ..., 'extension': ...}
                      **_,  # absorbs unsupported kwargs from call_llm dispatcher
                      ):
        model = config.Config.DEFAULT_MISTRAL_CHAT_API_MODEL
        temperature = 0.0  # Deterministic extraction

        user_content = []
        if document_data:  # Append the appropriate content block based on file type
            document_url = document_data['url']
            if document_data['extension'] in self.image_extensions:
                user_content.append({"type": "image_url", "image_url": document_url})
            else:
                user_content.append({"type": "document_url", "document_url": document_url})
        user_content.append({"type": "text", "text": user_prompt})

        kwargs = {
            'model': model,
            'messages': [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            'temperature': temperature,
        }
        if response_format:
            kwargs['response_format'] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction",
                    "strict": True,
                    "schema": {**response_format, 'additionalProperties': False}
                }
            }

        try:
            response = self.mistral_client.chat.complete(**kwargs)
            return response.choices[0].message.content, model, temperature, None, []
        except SDKError as e:
            raise RuntimeError('Mistral service unavailable') from e

    def _call_google(self, system_prompt, user_prompt,
                     response_format=None,
                     document_data=None,  # {'url': ..., 'extension': ...}
                     max_output_tokens=None,
                     is_chat=False,
                     is_rag=False,
                     history=None,
                     cache_name=None,
                     tool_declarations=None,  # list[types.FunctionDeclaration]
                     tool_dispatch=None,  # {name: callable}
                     **_,  # absorbs unsupported kwargs from call_llm dispatcher
                     ):
        model = config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL

        # thinking_level = types.ThinkingLevel.MEDIUM
        if is_chat:
            temperature = 1.0  # Google recommendation: For all Gemini 3 models, we strongly recommend ... 1.0
            thinking_level = types.ThinkingLevel.MINIMAL
        elif is_rag:
            temperature = 0.2  # retrieval-grounded answer: stay close to the help context
            thinking_level = types.ThinkingLevel.MINIMAL
        else:
            temperature = 1.0  # Google recommendation: For all Gemini 3 models, we strongly recommend ... 1.0
            thinking_level = types.ThinkingLevel.MEDIUM

        config_kwargs = {}
        if cache_name:
            # cache already holds system_instruction + tool_declarations (if any), set at cache creation
            config_kwargs['cached_content'] = cache_name
        else:
            config_kwargs['system_instruction'] = system_prompt
            if tool_declarations:
                config_kwargs['tools'] = [types.Tool(function_declarations=tool_declarations)]
        config_kwargs['temperature'] = temperature
        config_kwargs['thinking_config'] = types.ThinkingConfig(
            thinking_level=thinking_level,  # 'HIGH' should set as 'DYNAMIC'
            include_thoughts=True
        )

        if response_format:
            config_kwargs['response_mime_type'] = 'application/json'
            config_kwargs['response_schema'] = response_format
        if document_data:
            config_kwargs['media_resolution'] = types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
        if max_output_tokens:
            config_kwargs['max_output_tokens'] = max_output_tokens

        contents = []
        for turn in (history or []):
            contents.append(types.Content(role=turn['role'], parts=[types.Part.from_text(text=turn['text'])]))

        current_parts = []
        if document_data:
            extension = document_data['extension']
            if extension not in self.google_mime_types_mapping:
                raise UnsupportedGoogleMimeTypeError(f"Unsupported extension for Google: {extension}")
            current_parts.append(
                types.Part.from_uri(
                    file_uri=document_data['url'],
                    mime_type=self.google_mime_types_mapping[extension]
                ),
            )
        current_parts.append(types.Part.from_text(text=user_prompt))

        contents.append(types.Content(role='user', parts=current_parts))

        thought_parts, tool_calls = [], []
        for _hop in range(_HOP_RANGE):
            response = self.google_ai_client.models.generate_content(
                model=model,
                config=types.GenerateContentConfig(**config_kwargs),
                contents=contents
            )

            for part in response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    thought_parts.append(part.text)

            # collect every tool call the model requested in this turn (0, 1, or many for parallel)
            function_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]
            if not function_calls or not tool_dispatch:
                break  # final answer arrived; exit loop

            # echo the model's tool-call turn back into history so the next call sees the full pairing
            contents.append(response.candidates[0].content)  # types.Content(role='user', parts=[function_call, text, thought, ...]
            tool_response_parts = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}  # vars/params to send/use with tool/method/function
                tool_calls.append({'hop': _hop, 'name': fc.name, 'args': args})
                result = tool_dispatch[fc.name](**args)  # run the local Python function
                tool_response_parts.append(types.Part.from_function_response(name=fc.name, response=result))  # wrap result, tag with name so Gemini matches it
            # all tool results go back as one user-role turn (Gemini convention)
            contents.append(types.Content(role='user', parts=tool_response_parts))
        else:
            # loop exhausted without a final answer — model still wanted more tool calls
            raise RuntimeError('Tool hop limit exceeded')

        thoughts = '\n'.join(thought_parts) or None

        return response.text, model, temperature, thoughts, tool_calls

    def google_get_cache(self, cache_name):
        if cache_name:
            try:
                cache = self.google_ai_client.caches.get(name=cache_name)
            except genai_errors.ClientError as e:
                if e.status == 'NOT_FOUND':
                    logger.info("Google cache not found")
                    # Usually the cache expired or was deleted; chat falls back to creating a new cache
                    cache = None
                else:
                    raise RuntimeError('Cache error') from e
            if cache:
                return cache.name, cache.create_time
        return None, None

    def google_delete_cache(self, cache_name):
        cache_name, _ = self.google_get_cache(cache_name=cache_name)
        if cache_name:
            self.google_ai_client.caches.delete(name=cache_name)
            return True
        return False

    def google_set_cache(self, system_instruction, ttl_seconds: int = 600, tool_declarations=None):
        try:
            cache_config_kwargs = {
                'system_instruction': system_instruction,
                # 'contents': [video_file],
                'ttl': f"{ttl_seconds}s",
            }
            if tool_declarations:
                cache_config_kwargs['tools'] = [types.Tool(function_declarations=tool_declarations)]
            cache = self.google_ai_client.caches.create(
                model=config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL,
                config=types.CreateCachedContentConfig(**cache_config_kwargs)
            )
            return cache.name, cache.create_time
        except genai_errors.ClientError as e:
            if e.status == 'INVALID_ARGUMENT':
                logger.info("Google cache invalid argument")
                # Usually the content is too small to cache (Google enforces a min token count); chat falls back to uncached
                return None, None
            raise RuntimeError('Cache error') from e

    def _call_openai(self, system_prompt, user_prompt,
                     response_format=None,
                     document_data=None,  # {'url': ..., 'extension': ...}
                     **_,  # absorbs unsupported kwargs from call_llm dispatcher
                     ):
        model = config.Config.DEFAULT_OPENAI_CHAT_API_MODEL
        temperature = 0.0  # Deterministic extraction

        content: list = []
        if document_data:  # Append the appropriate content block based on file type
            document_url = document_data['url']
            if document_data['extension'] in self.image_extensions:
                content.append(ResponseInputImageContentParam(type="input_image", image_url=document_url))
            else:
                content.append(ResponseInputFileContentParam(type="input_file", file_url=document_url))
        content.append(ResponseInputTextContentParam(type="input_text", text=user_prompt))

        kwargs = {
            'model': model,
            'instructions': system_prompt,
            'input': [EasyInputMessageParam(role="user", content=content)],
            'temperature': temperature,
        }
        if response_format:
            kwargs['text'] = {"format": ResponseFormatTextJSONSchemaConfigParam(
                type="json_schema",
                name="extraction",
                strict=True,
                schema={**response_format, 'additionalProperties': False},
            )}

        response = self.openai_client.responses.create(**kwargs)
        return response.output_text, model, temperature, None, []
