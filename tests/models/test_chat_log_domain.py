from mongoengine import DictField, StringField

from webapp.models.chat_log_domain import ChatLog


def test_chat_log_model_has_created_at_default():
    field = ChatLog._fields["created_at"]

    assert field.default is not None


def test_chat_log_model_has_key_field():
    assert isinstance(ChatLog._fields["key"], DictField)


def test_chat_log_model_has_question_and_response_fields():
    assert isinstance(ChatLog._fields["user_question"], StringField)
    assert isinstance(ChatLog._fields["chat_api_response"], StringField)


def test_chat_log_model_has_feedback_fields():
    assert ChatLog._fields["liked"].default is None
    assert ChatLog._fields["disliked"].default is None
