from datetime import datetime, timedelta

from webapp.models.chat_log_domain import ChatLog


class ChatLogRepository:
    @staticmethod
    def create(key, user_question, chat_api_response):
        return ChatLog.objects.create(
            key=key,
            user_question=user_question,
            chat_api_response=chat_api_response,
        )

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

    def get_history(self, key, max_history_minutes=60, max_history_turns=10) -> list:
        cutoff = datetime.utcnow() - timedelta(minutes=max_history_minutes)
        logs = (
            ChatLog.objects(key=key, created_at__gte=cutoff, expired__ne=True)
            .order_by('-created_at')
            .only('user_question', 'chat_api_response', 'created_at')
            .limit(max_history_turns)
        )
        history = []
        for log in reversed(list(logs)):
            chat_log_id = str(log.id)
            history.append({'chat_log_id': chat_log_id, 'role': 'user', 'text': log.user_question, 'created_at': log.created_at})
            history.append({'chat_log_id': chat_log_id, 'role': 'model', 'text': log.chat_api_response, 'created_at': log.created_at})
        return history
