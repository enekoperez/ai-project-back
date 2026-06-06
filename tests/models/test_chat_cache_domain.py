from mongoengine import DictField, StringField

from webapp.models.chat_cache_domain import ChatCache


def test_chat_cache_model_has_key_and_name_fields():
    assert isinstance(ChatCache._fields["key"], DictField)
    assert isinstance(ChatCache._fields["name"], StringField)


def test_chat_cache_model_indexes_key_lookup():
    assert {"fields": ["key"], "unique": True} in ChatCache._meta["indexes"]
