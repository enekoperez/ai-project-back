import json

from webapp.repositories.chat_log_repository import ChatLogRepository
from webapp.services.ai_service import AiService

_MAX_USER_QUESTION_CHARS = 3000
_MAX_OUTPUT_TOKENS = 6_666  # 6,666 tokens * $1.50/M = ~0.01$ max output cost per call


class BaseService:
    def __init__(self):
        self.chat_log_repository = ChatLogRepository()
        self.ai_service = AiService()

    def _normalize_user_input(self, _input):
        if isinstance(_input, list):
            return [self._normalize_user_input(item) for item in _input]
        if _input is None:
            return ""
        return str(_input).strip()[:_MAX_USER_QUESTION_CHARS]

    @staticmethod
    def _create_chat_log_key(user_id, key_2=None):
        chat_log_key = {'user_id': user_id}
        if key_2:
            chat_log_key['key_2'] = key_2
        return chat_log_key

    @staticmethod
    def _try_json_loads(s):
        try:
            return json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return s

    @staticmethod
    def _to_iso(dt):
        return dt.isoformat() if dt else None

    @staticmethod
    def _to_millis(dt):
        return int(dt.timestamp() * 1000) if dt else None

    def get_chat_history(self, user_id, key_2=None):
        chat_log_key = self._create_chat_log_key(user_id=user_id, key_2=key_2)
        history = self.chat_log_repository.get_history(key=chat_log_key)
        for entry in history:
            created_at = entry['created_at']
            entry['created_at'] = self._to_iso(created_at)
            entry['created_at_utc_in_millis'] = self._to_millis(created_at)
            if entry['role'] == 'model':
                entry['text'] = self._try_json_loads(entry['text'])
        return history

    def _call_llm_and_log(self, user_question, chat_log_key,
                          system_prompt, user_prompt,
                          is_chat=False, is_rag=False,
                          tool_declarations=None, tool_dispatch=None,
                          cache_name=None):
        if is_chat == is_rag:  # Exactly one mode must be selected: chat XOR RAG.
            raise ValueError("Exactly one of is_chat or is_rag must be true.")

        chat_api_response, *_ = self.ai_service.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            is_chat=is_chat,
            is_rag=is_rag,
            history=self.chat_log_repository.get_history(key=chat_log_key),
            tool_declarations=tool_declarations,
            tool_dispatch=tool_dispatch,
            cache_name=cache_name,
        )

        chat_log = self.chat_log_repository.create(
            key=chat_log_key,
            user_question=user_question,
            chat_api_response=chat_api_response,
        )
        return chat_log, chat_api_response

    def _chat_output(self, chat_log, chat_api_response, cache_create_time=None, top_chunks=None):
        response = {
            "chat_log_id": str(chat_log.id),
            "chat_api_response": self._try_json_loads(chat_api_response),
            "date": self._to_iso(chat_log.created_at),
            "date_utc_in_millis": self._to_millis(chat_log.created_at),
            "source_names": [],
            # "source_names_and_scores": [],  # scores are Qdrant RRF ranks (not cosine/confidence); hidden to avoid misreads
            **self._cache_create_time_response(cache_create_time=cache_create_time),
        }
        if top_chunks:
            response.update({
                "source_names": [c["source_name"] for c in top_chunks],
                # "source_names_and_scores": [
                #     {"source_name": c["source_name"], "score": round(c["score"], 3)}
                #     for c in top_chunks
                # ],
            })
        return response

    def _cache_create_time_response(self, cache_create_time):
        response = {
            "cache_create_time": self._to_iso(cache_create_time),
            "cache_create_time_utc_in_millis": self._to_millis(cache_create_time),
        }
        return response
