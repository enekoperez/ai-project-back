from webapp.dto.chat_dto import chat_to_dict
from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.repositories.chat_repository import ChatRepository
from webapp.services.ai_service import AiService
from webapp.services.base_service import BaseService


class ChatService(BaseService):
    def __init__(self):
        super().__init__()
        self.ai_service = AiService()
        self.chat_repository = ChatRepository()

    def ask(self, request_json):
        chat_obj = self.chat_repository.create()

        question = self._normalize_user_input(_input=request_json["question"])

        chat_api_response, *_ = self.ai_service.call_llm(
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(question=question),
            is_chat=True,
        )
        return chat_to_dict(db_obj=chat_obj, response=chat_api_response)
