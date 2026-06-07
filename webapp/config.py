from os import environ

from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = environ["FLASK_DEBUG"].lower() == "true"  # env bool
    # TEST = False

    DB_CONNECTION_STRING = environ["AI_DB_CONNECTION_STRING"]
    QDRANT_URL = environ["QDRANT_URL"]
    QDRANT_COLLECTION_NAME = environ["QDRANT_COLLECTION_NAME"]

    MISTRAL_API_KEY = environ["MISTRAL_API_KEY"]
    GOOGLE_AI_API_KEY = environ["GOOGLE_AI_API_KEY"]
    OPENAI_API_KEY = environ["OPENAI_API_KEY"]

    DEFAULT_MISTRAL_CHAT_API_MODEL = environ.get("DEFAULT_MISTRAL_CHAT_API_MODEL", "mistral-small-2603")
    DEFAULT_GOOGLE_AI_CHAT_API_MODEL = environ.get("DEFAULT_GOOGLE_AI_CHAT_API_MODEL", "gemini-3.1-flash-lite")
    DEFAULT_OPENAI_CHAT_API_MODEL = environ.get("DEFAULT_OPENAI_CHAT_API_MODEL", "gpt-5.4-nano")
    DEFAULT_GOOGLE_AI_EMBEDDING_MODEL = environ.get("DEFAULT_GOOGLE_AI_EMBEDDING_MODEL", "gemini-embedding-2")
