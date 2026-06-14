from werkzeug.exceptions import Forbidden

from webapp.repositories.chat_log_repository import ChatLogRepository


class ChatService:
    def __init__(self):
        self.chat_log_repository = ChatLogRepository()

    def _raise_if_not_owner(self, chat_log_id, user_id):
        if self.chat_log_repository.get_chat_log_by_user_id(chat_log_id, user_id) is None:
            raise Forbidden()

    def like(self, chat_log_id, user_id):
        self._raise_if_not_owner(chat_log_id, user_id)
        return self.chat_log_repository.like(chat_log_id=chat_log_id)

    def dislike(self, chat_log_id, user_id):
        self._raise_if_not_owner(chat_log_id, user_id)
        return self.chat_log_repository.dislike(chat_log_id=chat_log_id)
