from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.rag_service import RagService


class ChatService(BaseService):
    def __init__(self):
        super().__init__()
        self.rag_service = RagService()

    def ask(self, request_json):
        question = self._normalize_user_input(_input=request_json["question"])

        top_chunks = self.rag_service.get_top_chunks(question=question)

        chat_log, chat_api_response = self._call_llm_and_log(
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(chunks=top_chunks, question=question),
            is_rag=True,
        )
        # return chat_to_dict(db_obj=chat_log, response=chat_api_response)
        return self._chat_output(chat_log=chat_log, chat_api_response=chat_api_response, top_chunks=top_chunks)
