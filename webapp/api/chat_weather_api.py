from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import ChatRequest, validate_json, validate_user_id
from webapp.services.chat_weather_service import ChatWeatherService

chat_weather = Blueprint("chat_weather", __name__)
chat_weather_service = ChatWeatherService()


@chat_weather.route("", methods=["POST"])
def create_chat():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_weather_service.chat(user_id, request_json)
    return success(response, status=201)


@chat_weather.route("", methods=["GET"])
def get_chat():
    user_id = validate_user_id()
    response = chat_weather_service.get_chat(user_id=user_id)
    return success(response)
