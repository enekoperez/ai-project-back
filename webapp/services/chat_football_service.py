import time

from webapp.prompts.chat_football_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.doc_service import DocService


class ChatFootballService(BaseService):
    def __init__(self):
        super().__init__()
        self.doc_service = DocService()
        self.key_2 = "chat_football"

    def chat_football_get_cache(self, user_id):  # Hasn't got an endpoint/caller
        _, display_name = self._create_chat_log_key_and_display_name(user_id=user_id, key_2=self.key_2)
        _, cache_create_time = self.ai_service.google_get_cache(display_name=display_name)
        return self._cache_create_time_response(cache_create_time=cache_create_time)

    def chat_football_refresh_cache(self, user_id):  # Hasn't got an endpoint/caller
        _, display_name = self._create_chat_log_key_and_display_name(user_id=user_id, key_2=self.key_2)
        self.ai_service.google_delete_cache(display_name=display_name)
        _, _, cache_create_time = self._create_chat_football_cache(display_name=display_name)
        return self._cache_create_time_response(cache_create_time=cache_create_time)

    # def get_chat()  # Hasn't got an endpoint/caller

    def chat(self, user_id, request_json):
        question = self._normalize_user_input(_input=request_json["question"])

        chat_log_key, display_name = self._create_chat_log_key_and_display_name(user_id=user_id, key_2=self.key_2)
        cache_name, cache_create_time = self.ai_service.google_get_cache(display_name=display_name)

        if cache_name:
            system_prompt = None
        else:
            system_prompt, cache_name, cache_create_time = self._create_chat_football_cache(display_name=display_name)

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

    def _create_chat_football_cache(self, display_name):
        #####
        # Mock cache creation latency so refresh/create cache calls visibly take longer.
        time.sleep(15)
        football_data = ""
        for source_file in self.doc_service.get_source_files():
            if source_file["source_name"] == "football.md":
                football_data = self.doc_service.get_source_text(source_file)
        #####

        system_prompt = build_system_prompt(football_data=football_data)
        cache_name, cache_create_time = self.ai_service.google_set_cache(display_name=display_name, system_instruction=system_prompt)
        return system_prompt, cache_name, cache_create_time
