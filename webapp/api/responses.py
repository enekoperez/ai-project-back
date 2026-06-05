from flask import jsonify


def success(data=None, status=200):
    return jsonify({
        "success": True,
        "data": data,
    }), status


def failure(code, message, status, details=None):
    error = {
        "code": code,
        "message": message,
    }
    if details is not None:
        error["details"] = details

    return jsonify({
        "success": False,
        "error": error,
    }), status
