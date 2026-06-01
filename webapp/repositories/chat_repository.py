from webapp.models.chat_domain import Chat


class ChatRepository:
    @staticmethod
    def create():
        return Chat.objects.create()
