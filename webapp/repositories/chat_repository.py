from webapp.models.chat_domain import Chat


class ChatRepository:
    @staticmethod
    def create():
        return Chat.objects.create()

    @staticmethod
    def get_all():
        return Chat.objects.order_by("-created_at")
