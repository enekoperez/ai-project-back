def assert_success_response(response, data):
    assert response.get_json() == {
        "success": True,
        "data": data,
    }


def assert_error_code(response, code):
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == code
