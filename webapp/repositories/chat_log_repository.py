from webapp.models.chat_log_domain import ChatLog


class ChatLogRepository:
    @staticmethod
    def create(key):
        return ChatLog.objects.create(key=key)

    @staticmethod
    def like(chat_log_id):
        log = ChatLog.objects(id=chat_log_id).only("liked").first()
        if log and log.liked:
            ChatLog.objects(id=chat_log_id).update_one(set__liked=None)
            return {"chat_log_id": chat_log_id, "liked": None, "disliked": None}

        # else:
        ChatLog.objects(id=chat_log_id).update_one(set__liked=True, set__disliked=None)
        return {"chat_log_id": chat_log_id, "liked": True, "disliked": None}

    @staticmethod
    def dislike(chat_log_id):
        log = ChatLog.objects(id=chat_log_id).only("disliked").first()
        if log and log.disliked:
            ChatLog.objects(id=chat_log_id).update_one(set__disliked=None)
            return {"chat_log_id": chat_log_id, "liked": None, "disliked": None}

        # else:
        ChatLog.objects(id=chat_log_id).update_one(set__disliked=True, set__liked=None)
        return {"chat_log_id": chat_log_id, "liked": None, "disliked": True}
