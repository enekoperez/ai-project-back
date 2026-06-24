from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from webapp.config import Config


def _rate_limit_key() -> str:
    # Prefer the caller-supplied identity; fall back to the client IP.
    return request.headers.get("User-Id") or get_remote_address()


limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=Config.RATELIMIT_STORAGE_URI,
    in_memory_fallback_enabled=True,  # fall back to in-memory limiting if the storage backend is down
    application_limits=["20 per hour"],  # 20 requests per hour per user, across the entire app
)

# 10 per hour per user, shared across the general, football and weather chat endpoints combined
chat_limit = limiter.shared_limit("10 per hour", scope="chat_limit")
