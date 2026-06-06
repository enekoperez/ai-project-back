import time

from webapp.prompts.chat_football_prompt import build_system_prompt, build_user_prompt
from webapp.repositories.chat_cache_repository import ChatCacheRepository
from webapp.services.base_service import BaseService
from webapp.services.doc_service import DocService


class ChatFootballService(BaseService):
    def __init__(self):
        super().__init__()
        self.chat_cache_repository = ChatCacheRepository()
        self.doc_service = DocService()
        self.key_2 = "chat_football"

    def chat(self, user_id, request_json):
        question = self._normalize_user_input(_input=request_json["question"])

        chat_log_key = self._create_chat_log_key(user_id=user_id, key_2=self.key_2)

        chat_cache_name = self.chat_cache_repository.get_name(key=chat_log_key)
        cache_name, cache_create_time = self.ai_service.google_get_cache(cache_name=chat_cache_name)

        if cache_name:
            system_prompt = None
        else:
            system_prompt, cache_name, cache_create_time = self._create_cache(chat_log_key=chat_log_key)

        user_prompt = build_user_prompt(question=question)

        chat_log, chat_api_response = self._call_llm_and_log(
            user_question=question,
            chat_log_key=chat_log_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            is_chat=True,
            cache_name=cache_name,
        )
        return self._chat_output(chat_log=chat_log, chat_api_response=chat_api_response, cache_create_time=cache_create_time)

    def get_chat(self, user_id):
        return self.get_chat_history(user_id=user_id, key_2=self.key_2)

    def get_cache(self, user_id):
        chat_log_key = self._create_chat_log_key(user_id=user_id, key_2=self.key_2)
        chat_cache_name = self.chat_cache_repository.get_name(key=chat_log_key)
        _, cache_create_time = self.ai_service.google_get_cache(cache_name=chat_cache_name)
        return self._cache_create_time_response(cache_create_time=cache_create_time)

    def refresh_cache(self, user_id):
        chat_log_key = self._create_chat_log_key(user_id=user_id, key_2=self.key_2)
        chat_cache_name = self.chat_cache_repository.get_name(key=chat_log_key)
        self.ai_service.google_delete_cache(cache_name=chat_cache_name)
        _, _, cache_create_time = self._create_cache(chat_log_key=chat_log_key)
        return self._cache_create_time_response(cache_create_time=cache_create_time)

    def _create_cache(self, chat_log_key):
        #####
        # Mock cache creation latency so refresh/create cache calls visibly take longer.
        time.sleep(15)
        football_data = ""
        for source_file in self.doc_service.get_source_files():
            if source_file["source_name"] == "football.md":
                football_data = self.doc_service.get_source_text(source_file)
        #####

        system_prompt = build_system_prompt(football_data=football_data)
        cache_name, cache_create_time = self.ai_service.google_set_cache(system_instruction=system_prompt)
        self.chat_cache_repository.upsert_name(key=chat_log_key, name=cache_name)
        return system_prompt, cache_name, cache_create_time
