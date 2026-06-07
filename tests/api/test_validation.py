import pytest
from flask import Flask, jsonify

from webapp.api.validation import (
    ChatRequest,
    RequestValidationError,
    UserRequest,
    request_json,
    validate_data,
    validate_json,
    validate_user_id,
)


def make_client():
    app = Flask(__name__)

    @app.errorhandler(RequestValidationError)
    def handle_validation_error(error):
        return jsonify({"errors": error.errors}), 422

    @app.post("/json")
    def json_route():
        return validate_json(ChatRequest)

    @app.get("/user-id")
    def user_id_route():
        return {"user_id": validate_user_id()}

    @app.post("/request-json")
    def request_json_route():
        return request_json()

    return app.test_client()


def test_request_json_returns_empty_dict_when_body_is_missing():
    response = make_client().post("/request-json")

    assert response.status_code == 200
    assert response.get_json() == {}


def test_validate_json_returns_validated_request_body():
    response = make_client().post("/json", json={"question": "  Hello  "})

    assert response.status_code == 200
    assert response.get_json() == {"question": "Hello"}


def test_validate_data_returns_validated_data():
    assert validate_data(UserRequest, {"user_id": "  user-1  "}) == {"user_id": "user-1"}


def test_validate_user_id_reads_user_id_header():
    response = make_client().get("/user-id", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == {"user_id": "user-1"}


def test_validate_data_raises_request_validation_error_for_invalid_data():
    with pytest.raises(RequestValidationError) as error:
        validate_data(ChatRequest, {"question": " "})

    assert error.value.errors[0]["loc"] == ("question",)
