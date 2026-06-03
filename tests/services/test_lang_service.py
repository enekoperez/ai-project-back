from webapp.services.lang_service import LangService


def test_simple_returns_agent_response(monkeypatch):
    agent = type(
        "Agent",
        (),
        {
            "invoke": lambda self, payload: {
                "messages": [
                    type("Message", (), {"content_blocks": [{"type": "text", "text": "Answer"}]})()
                ]
            }
        },
    )()
    create_agent = lambda **kwargs: agent
    monkeypatch.setattr("webapp.services.lang_service.create_agent", create_agent)

    response = LangService().call_simple({"question": "What's the weather in Bilbao?"})

    assert response == {"message": [{"type": "text", "text": "Answer"}]}


def test_complex_returns_message():
    response = LangService().call_complex()

    assert response == {"message": "Hello world from COMPLEX"}
