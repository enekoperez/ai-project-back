from webapp.models.chat_log_domain import ChatLog


class ChatLogRepository:
    @staticmethod
    def create():
        return ChatLog.objects.create()
