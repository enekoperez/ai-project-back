from webapp.dto.chat import chat_to_dict
from webapp.repositories.chat import ChatRepository


class ChatService:
    def __init__(self):
        self.chat_repository = ChatRepository()

    def create(self):
        return chat_to_dict(self.chat_repository.create())

    def get_all(self):
        return [chat_to_dict(chat) for chat in self.chat_repository.get_all()]
