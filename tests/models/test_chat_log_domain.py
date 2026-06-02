from webapp.models.chat_log_domain import ChatLog


def test_chat_log_model_has_created_at_default():
    field = ChatLog._fields["created_at"]

    assert field.default is not None


def test_chat_log_model_has_feedback_fields():
    assert ChatLog._fields["liked"].default is None
    assert ChatLog._fields["disliked"].default is None
