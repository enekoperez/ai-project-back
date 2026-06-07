from flask import Flask

from webapp.api.responses import failure, success


def make_client():
    app = Flask(__name__)

    @app.get("/success")
    def success_route():
        return success({"id": "item-1"}, status=201)

    @app.get("/failure")
    def failure_route():
        return failure(
            code="validation_error",
            message="Invalid request",
            status=422,
            details=[{"loc": ["question"], "msg": "Field required"}],
        )

    return app.test_client()


def test_success_returns_json_payload_and_status():
    response = make_client().get("/success")

    assert response.status_code == 201
    assert response.get_json() == {
        "success": True,
        "data": {"id": "item-1"},
    }


def test_failure_returns_error_payload_and_status():
    response = make_client().get("/failure")

    assert response.status_code == 422
    assert response.get_json() == {
        "success": False,
        "error": {
            "code": "validation_error",
            "message": "Invalid request",
            "details": [{"loc": ["question"], "msg": "Field required"}],
        },
    }
