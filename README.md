# AI Project

[![Tests](https://github.com/enekoperez/ai-project/actions/workflows/tests.yml/badge.svg)](https://github.com/enekoperez/ai-project/actions/workflows/tests.yml)

An AI backend service built with Flask, MongoDB, and multiple LLM providers. It combines retrieval-augmented chat, domain-specific assistants, tool calling, OCR-style document extraction, persistent conversation history, feedback logging, Docker deployment, and automated CI checks.

> Portfolio note: this README is structured to show both the product value and the engineering decisions behind the project.

## Demo

- Live API: `TODO`
- Screenshots: `TODO`
- API collection: `TODO`

## Why This Project Matters

This project demonstrates how to build an AI application as a maintainable backend service rather than a one-off prompt wrapper. The code separates HTTP validation, service orchestration, provider integrations, prompts, persistence, and retrieval logic so each part can be tested and evolved independently.

Core capabilities:

- General RAG chat over markdown knowledge sources.
- Football assistant with Gemini cached context for reusable domain knowledge.
- Weather assistant using Gemini function calling and the Open-Meteo API.
- OCR/question extraction over remote PDF files with structured JSON output.
- Chat history persisted in MongoDB and replayed into future conversations.
- Like/dislike feedback endpoints for assistant responses.
- Dockerized production runtime with Gunicorn and gevent.
- CI for linting, tests, coverage, Docker image validation, dependency updates, and security scanning.

## Tech Stack

- Python, Flask, Gunicorn, gevent
- MongoDB with MongoEngine
- Pydantic request validation
- Google Gemini, Mistral, and OpenAI provider integrations
- LangChain-related dependencies for AI workflows
- pytest, pytest-cov, Ruff
- Docker, GitHub Actions, Semgrep, Dependabot

## Architecture

The application is organized around a small Flask API surface and a service layer that owns the AI behavior.

```text
webapp/
  api/             HTTP blueprints, validation, response formatting
  services/        AI orchestration, RAG, OCR, chat, domain assistants
  repositories/    MongoDB persistence access
  models/          MongoEngine document models
  prompts/         Prompt builders per assistant/task
  tools/           Model-callable tools, such as weather lookup
  rag_docs/        Markdown knowledge sources used for RAG
  run.py           Flask app factory and runtime entrypoint
  cli.py           Flask CLI commands
```

Request flow:

1. A Flask blueprint receives the request.
2. Pydantic validation rejects malformed JSON, unknown fields, and missing headers.
3. The service layer normalizes user input, builds prompts, retrieves history or RAG context, and calls the AI provider abstraction.
4. Provider responses are saved to MongoDB with timestamps and metadata.
5. API responses return consistent JSON payloads with IDs, timestamps, model output, cache metadata, or source scores where relevant.

## Main Features

### General RAG Chat

`ChatGeneralService` retrieves relevant chunks from the RAG store, injects them into the prompt, and asks Gemini for a grounded answer. Source names and similarity scores are returned with the response so the caller can inspect what context was used.

RAG indexing is handled by the Flask CLI:

```bash
flask --app webapp.run rag-sync
```

The sync process fingerprints source files, removes stale chunks, embeds changed documents, and stores vectors in MongoDB.

### Football Assistant

The football assistant uses a dedicated prompt and football knowledge source. It also uses Gemini cached content so repeated user interactions can reuse the same domain context.

Cache endpoints allow the client to inspect or refresh the cached context.

### Weather Assistant

The weather assistant exposes a model-callable `get_weather` tool. Gemini can request weather data during a conversation, and the backend resolves the city and fetches current conditions from Open-Meteo.

### OCR Extraction

The OCR endpoint accepts a remote PDF URL and a list of questions. The service asks an AI provider to extract all values matching each question and requests a structured JSON response.

### Feedback and History

Chat logs are persisted with user questions, model responses, timestamps, and feedback fields. The service replays recent conversation turns into future chat requests and supports toggling like/dislike feedback per chat log.

## API Overview

All chat endpoints that depend on user history expect a `User-Id` header.

### Health Check

```http
GET /
```

### General RAG Chat

```http
POST /ai/chat/general/
Content-Type: application/json
User-Id: demo-user

{
  "question": "What should I know about the available sports documents?"
}
```

```http
GET /ai/chat/general/
User-Id: demo-user
```

### Football Chat

```http
POST /ai/chat/football/
Content-Type: application/json
User-Id: demo-user

{
  "question": "Summarize the key football information."
}
```

```http
GET /ai/chat/football/
User-Id: demo-user
```

```http
GET /ai/chat/football/cache
User-Id: demo-user
```

```http
PUT /ai/chat/football/cache
Content-Type: application/json
User-Id: demo-user

{}
```

### Weather Chat

```http
POST /ai/chat/weather/
Content-Type: application/json
User-Id: demo-user

{
  "question": "What is the weather in Bilbao?"
}
```

```http
GET /ai/chat/weather/
User-Id: demo-user
```

### Chat Feedback

```http
PUT /ai/chat/<chat_log_id>/like
Content-Type: application/json

{}
```

```http
PUT /ai/chat/<chat_log_id>/dislike
Content-Type: application/json

{}
```

### OCR

```http
POST /ai/ocr/
Content-Type: application/json

{
  "file_url": "https://example.com/document.pdf",
  "questions": ["invoice number", "total amount", "due date"]
}
```

### Language Experiments

```http
POST /ai/lang/simple
Content-Type: application/json

{
  "question": "Explain retrieval augmented generation in one paragraph."
}
```

```http
POST /ai/lang/complex
Content-Type: application/json

{}
```

## Local Development

### 1. Create an environment

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the provider keys.

```env
FLASK_DEBUG=false
AI_DB_CONNECTION_STRING=mongodb://localhost:27017/ai_db
MISTRAL_API_KEY=api-key-needed
GOOGLE_AI_API_KEY=api-key-needed
OPENAI_API_KEY=api-key-needed
```

Optional model overrides:

```env
DEFAULT_MISTRAL_CHAT_API_MODEL=mistral-small-2603
DEFAULT_GOOGLE_AI_CHAT_API_MODEL=gemini-3.1-flash-lite
DEFAULT_OPENAI_CHAT_API_MODEL=gpt-5.4-nano
DEFAULT_GOOGLE_AI_EMBEDDING_MODEL=gemini-embedding-2
```

### 3. Start MongoDB

Run MongoDB locally or point `AI_DB_CONNECTION_STRING` at a reachable MongoDB instance.

### 4. Start the Flask app

```bash
flask --app webapp.run run
```

The app exposes the health check at:

```text
http://127.0.0.1:5000/
```

### 5. Sync RAG documents

Run this after configuring the Google AI key and MongoDB connection:

```bash
flask --app webapp.run rag-sync
```

## Docker

Build the image:

```bash
docker build -t ai-project .
```

Run the container:

```bash
docker run --rm --env-file .env -p 8080:80 ai-project
```

Then call:

```text
http://localhost:8080/
```

The production container runs Gunicorn with gevent workers.

## Testing and Quality

Run the test suite:

```bash
pytest tests/ --color=yes --cov=webapp --cov-report=term-missing
```

Run linting:

```bash
ruff check webapp tests
```

The GitHub Actions pipeline runs:

- Dependency installation and `pip check`.
- Ruff linting.
- pytest with coverage and an 80% minimum threshold.
- Docker image build and import smoke test.
- Semgrep security scanning.
- Dependabot updates for pip, GitHub Actions, and Docker.

## Engineering Highlights

- Clear separation between API, services, repositories, models, prompts, and tools.
- Strict request validation with Pydantic models and forbidden extra fields.
- Multi-provider AI abstraction with retry handling and provider fallback for non-chat extraction tasks.
- Gemini tool calling with a backend weather function and bounded tool-hop loop.
- RAG pipeline with document fingerprinting, chunk storage, embedding model tracking, and cosine similarity retrieval.
- MongoDB indexes for chat history and RAG lookup paths.
- Structured response helpers for consistent API output.
- Focused tests across API routes, services, repositories, DTOs, models, prompts, tools, and CLI behavior.

## Repository Status

This project is intended as a portfolio centerpiece. The remaining portfolio polish is to add a live deployment URL, screenshots, and an API collection or short demo video.
