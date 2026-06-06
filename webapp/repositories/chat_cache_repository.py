from webapp.models.chat_cache_domain import ChatCache


class ChatCacheRepository:
    @staticmethod
    def get_name(key):
        chat_cache = ChatCache.objects(key=key).only('name').first()
        if chat_cache:
            return chat_cache.name
        return None

    @staticmethod
    def upsert_name(key, name):
        return ChatCache.objects(key=key).update_one(set__name=name, upsert=True)
