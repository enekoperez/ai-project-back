from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.rag_service import RagService


class ChatService(BaseService):
    def __init__(self):
        super().__init__()
        self.rag_service = RagService()

    def chat(self, user_id, request_json):
        question = self._normalize_user_input(_input=request_json["question"])

        chat_log_key, _ = self._create_chat_log_key_and_display_name(user_id=user_id)
        top_chunks = self.rag_service.get_top_chunks(question=question)

        chat_log, chat_api_response = self._call_llm_and_log(
            user_question=question,
            chat_log_key=chat_log_key,
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(chunks=top_chunks, question=question),
            is_rag=True,
        )
        # return chat_to_dict(db_obj=chat_log, response=chat_api_response)
        return self._chat_output(chat_log=chat_log, chat_api_response=chat_api_response, top_chunks=top_chunks)

    def get_chat(self, user_id):
        return self.get_chat_history(user_id=user_id)

    def like(self, chat_log_id):
        return self.chat_log_repository.like(chat_log_id=chat_log_id)

    def dislike(self, chat_log_id):
        return self.chat_log_repository.dislike(chat_log_id=chat_log_id)
