from webapp.dto.chat_dto import chat_to_dict
from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.repositories.chat_log_repository import ChatLogRepository
from webapp.services.ai_service import AiService
from webapp.services.base_service import BaseService
from webapp.services.rag_service import RagService


class ChatService(BaseService):
    def __init__(self):
        super().__init__()
        self.ai_service = AiService()
        self.chat_log_repository = ChatLogRepository()
        self.rag_service = RagService()

    def ask(self, request_json):
        chat_log = self.chat_log_repository.create()

        question = self._normalize_user_input(_input=request_json["question"])

        chat_api_response, *_ = self.ai_service.call_llm(
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(chunks=self.rag_service.get_top_chunks(question=question), question=question),
            # max_output_tokens=_MAX_OUTPUT_TOKENS,
            is_rag=True,
        )
        return chat_to_dict(db_obj=chat_log, response=chat_api_response)
