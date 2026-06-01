from webapp.models.chat import Chat


class ChatRepository:
    def create(self):
        return Chat.objects.create()

    def get_all(self):
        return Chat.objects.order_by("-created_at")
