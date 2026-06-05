from webapp.repositories.chat_log_repository import ChatLogRepository


class ChatService:
    def __init__(self):
        self.chat_log_repository = ChatLogRepository()

    def like(self, chat_log_id):
        return self.chat_log_repository.like(chat_log_id=chat_log_id)

    def dislike(self, chat_log_id):
        return self.chat_log_repository.dislike(chat_log_id=chat_log_id)
