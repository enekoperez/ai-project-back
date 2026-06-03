from webapp.services.lang_service import LangService


def test_simple_returns_message():
    response = LangService().call_simple()

    assert response == {"message": "Hello world from SIMPLE"}


def test_complex_returns_message():
    response = LangService().call_complex()

    assert response == {"message": "Hello world from COMPLEX"}
