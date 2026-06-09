from typing import List, Type

from flask import request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, constr
from werkzeug.exceptions import UnprocessableEntity

NonEmptyString = constr(strip_whitespace=True, min_length=1)


class RequestValidationError(UnprocessableEntity):
    description = "Invalid request"

    def __init__(self, errors):
        super().__init__(description=self.description)
        self.errors = errors


class _RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyRequest(_RequestModel):
    pass


class ChatRequest(_RequestModel):
    question: NonEmptyString


class UserRequest(_RequestModel):
    user_id: NonEmptyString


class OcrRequest(_RequestModel):
    file_url: NonEmptyString
    questions: List[NonEmptyString] = Field(min_length=1)


class LangSimpleRequest(_RequestModel):
    question: NonEmptyString


class ChatLogPathRequest(_RequestModel):
    chat_log_id: NonEmptyString


def request_json():
    return request.get_json(silent=True) or {}


def validate_json(model: Type[BaseModel]):
    return _validate(model, request_json()).model_dump(exclude_none=True)


def validate_data(model: Type[BaseModel], data):
    return _validate(model, data).model_dump(exclude_none=True)


def validate_user_id():
    return validate_data(UserRequest, {"user_id": request.headers.get("User-Id")})["user_id"]


def _validate(model: Type[BaseModel], data):
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise RequestValidationError(errors=error.errors()) from error
