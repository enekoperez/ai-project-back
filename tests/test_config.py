import importlib


def test_config_reads_required_environment_values(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "true")
    monkeypatch.setenv("AI_DB_CONNECTION_STRING", "mongodb://db")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant")
    monkeypatch.setenv("QDRANT_COLLECTION_NAME", "chunks")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    import webapp.config as config

    config = importlib.reload(config)

    assert config.Config.DEBUG is True
    assert config.Config.DB_CONNECTION_STRING == "mongodb://db"
    assert config.Config.QDRANT_URL == "http://qdrant"
    assert config.Config.QDRANT_COLLECTION_NAME == "chunks"
    assert config.Config.MISTRAL_API_KEY == "mistral-key"
    assert config.Config.GOOGLE_AI_API_KEY == "google-key"
    assert config.Config.OPENAI_API_KEY == "openai-key"


def test_config_uses_default_model_names(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("AI_DB_CONNECTION_STRING", "mongodb://db")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant")
    monkeypatch.setenv("QDRANT_COLLECTION_NAME", "chunks")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.delenv("DEFAULT_MISTRAL_CHAT_API_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_GOOGLE_AI_CHAT_API_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_OPENAI_CHAT_API_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_GOOGLE_AI_EMBEDDING_MODEL", raising=False)

    import webapp.config as config

    config = importlib.reload(config)

    assert config.Config.DEBUG is False
    assert config.Config.DEFAULT_MISTRAL_CHAT_API_MODEL == "mistral-small-2603"
    assert config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL == "gemini-3.1-flash-lite"
    assert config.Config.DEFAULT_OPENAI_CHAT_API_MODEL == "gpt-5.4-nano"
    assert config.Config.DEFAULT_GOOGLE_AI_EMBEDDING_MODEL == "gemini-embedding-2"
