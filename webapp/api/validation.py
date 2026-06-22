from typing import Annotated, Any, List

from flask import request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError
from werkzeug.exceptions import UnprocessableEntity

#: A trimmed string that must contain at least one non-whitespace character.
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RequestValidationError(UnprocessableEntity):
    """Raised when a request payload fails Pydantic validation.

    Carries the structured Pydantic errors so the error handler can return
    them in the response body alongside an HTTP 422 status.
    """

    description = "Invalid request"

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__(description=self.description)
        self.errors = errors


class _RequestModel(BaseModel):
    """Base for request models; rejects any field not declared on the model."""

    model_config = ConfigDict(extra="forbid")


class EmptyRequest(_RequestModel):
    """A request that must carry no body fields."""


class ChatRequest(_RequestModel):
    """Body of a chat request."""

    question: NonEmptyString


class UserRequest(_RequestModel):
    """The caller identity carried in the ``User-Id`` header."""

    user_id: NonEmptyString


class OcrRequest(_RequestModel):
    """Body of an OCR request: a document URL and 1-10 questions to answer."""

    file_url: NonEmptyString
    questions: List[NonEmptyString] = Field(min_length=1, max_length=10)


class ChatLogPathRequest(_RequestModel):
    """The chat log identifier taken from the request path."""

    chat_log_id: NonEmptyString


def request_json() -> dict[str, Any]:
    """Return the parsed JSON body, or an empty dict if absent or malformed."""
    return request.get_json(silent=True) or {}


def validate_json(model: type[_RequestModel]) -> dict[str, Any]:
    """Validate the request JSON body against ``model`` and return it as a dict."""
    return _validate(model, request_json()).model_dump(exclude_none=True)


def validate_data(model: type[_RequestModel], data: Any) -> dict[str, Any]:
    """Validate arbitrary ``data`` against ``model`` and return it as a dict."""
    return _validate(model, data).model_dump(exclude_none=True)


def validate_user_id() -> str:
    """Validate the ``User-Id`` request header and return it."""
    return validate_data(UserRequest, {"user_id": request.headers.get("User-Id")})["user_id"]


def _validate(model: type[_RequestModel], data: Any) -> _RequestModel:
    """Validate ``data`` against ``model``, raising ``RequestValidationError`` on failure."""
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise RequestValidationError(errors=error.errors()) from error
