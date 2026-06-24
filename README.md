# AI Project

[![Tests](https://github.com/enekoperez/ai-project/actions/workflows/tests.yml/badge.svg)](https://github.com/enekoperez/ai-project/actions/workflows/tests.yml)

An AI backend service built with Flask, MongoDB, and multiple LLM providers. It combines retrieval-augmented chat, domain-specific assistants, tool calling, OCR-style document extraction, persistent conversation history, feedback logging, Docker deployment, and automated CI checks.

## Why This Project Matters

This project demonstrates how to build an AI application as a maintainable backend service rather than a one-off prompt wrapper. The code separates HTTP validation, service orchestration, provider integrations, prompts, persistence, and retrieval logic so each part can be tested and evolved independently.

Core capabilities:

- General RAG chat over markdown knowledge sources.
- Football assistant with Gemini cached context for reusable domain knowledge.
- Weather assistant using Gemini function calling and the Open-Meteo API.
- OCR/question extraction over remote PDF files with structured JSON output.
- Chat history persisted in MongoDB and replayed into future conversations.
- Like/dislike feedback endpoints for assistant responses.
- Built-in web chat UI, served by Flask, for trying the RAG assistant in a browser.
- Dockerized production runtime with Gunicorn and gevent.
- CI for linting, tests, coverage, Docker image validation, dependency updates, and security scanning.

## Tech Stack

- Python, Flask, Gunicorn, gevent
- MongoDB with MongoEngine
- Qdrant for local vector search
- Pydantic request validation
- Google Gemini, Mistral, and OpenAI provider integrations
- Loguru for structured logging
- pytest, pytest-cov, Ruff
- Docker, GitHub Actions, Semgrep, Dependabot

## Architecture

The application is organized around a small Flask API surface and a service layer that owns the AI behavior.

```text
rag_docs/          Markdown knowledge sources used for RAG
evals/             RAG retrieval eval harness (hit@k, MRR, recall@k)
webapp/
  api/             HTTP blueprints, validation, response formatting
  routes/          Route/blueprint registration and error handlers
  services/        AI orchestration, RAG, OCR, chat, domain assistants
  repositories/    MongoDB and Qdrant persistence access
  models/          MongoEngine document models
  dto/             DTO serializers for API responses
  prompts/         Prompt builders per assistant/task
  tools/           Model-callable tools, such as weather lookup
  static/          Web chat UI (index.html) served at /ui
  config.py        Environment-driven configuration
  run.py           Flask app factory and runtime entrypoint
  cli.py           Flask CLI commands
```

Request flow:

1. A Flask blueprint receives the request.
2. Pydantic validation rejects malformed JSON, unknown fields, and missing headers.
3. The service layer normalizes user input, builds prompts, retrieves history or RAG context, and calls the AI provider abstraction.
4. Provider responses are saved to MongoDB with timestamps and metadata.
5. API responses return consistent JSON payloads with IDs, timestamps, model output, cache metadata, or retrieved source names where relevant.

## Main Features

### General RAG Chat

`ChatGeneralService` retrieves relevant chunks from the RAG store using hybrid search (dense cosine + BM25, fused server-side by Qdrant Reciprocal Rank Fusion), injects them into the prompt, and asks Gemini for a grounded answer. The source names used for the answer are returned with the response so the caller can inspect what context was used.

RAG indexing is handled by the Flask CLI:

```bash
flask --app webapp.run rag-sync
```

The sync process reads local markdown docs, chunks and embeds them, and rebuilds the Qdrant vector collection. Qdrant stores only the source name and chunk text as payload, while MongoDB remains responsible for app data such as chat history and feedback.

### Web Chat UI

A single static page (`webapp/static/index.html`, vanilla JS with light/dark themes) is served by Flask at `GET /ui`. It provides a browser chat interface over the general RAG assistant: it keeps message history, sends questions to `POST /ai/v1/chat/general/` with a `User-Id` header, and offers thumbs-up/down feedback on each answer.

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

Request bodies are capped at 1 MB; larger payloads are rejected with HTTP 413.

### Rate Limits

Requests are rate limited per user (by the `User-Id` header, falling back to the
client IP) using [Flask-Limiter](https://flask-limiter.readthedocs.io/) backed by
Redis, so limits are shared across all Gunicorn workers. Exceeding a limit returns
HTTP 429 with the standard error envelope.

| Scope | Limit |
| --- | --- |
| Entire app (all endpoints combined) | 200 / hour |
| `POST /ai/v1/chat/orchestrator/` | 50 / hour |
| `POST /ai/v1/chat/{general,football,weather}/` (shared) | 100 / hour |

The shared chat limit is one combined bucket across the three plain chat
assistants. All limits roll up to the 20/hour app-wide cap. Configure the backend
with `RATELIMIT_STORAGE_URI` (e.g. `redis://localhost:6379`).

### Health Check

```http
GET /
```

Returns `{"success": true, "data": {"status": "OK"}}`.

### Web UI

```http
GET /ui
```

Serves the browser chat interface backed by the general RAG assistant.

### General RAG Chat

```http
POST /ai/v1/chat/general/
Content-Type: application/json
User-Id: demo-user

{
  "question": "What should I know about the available sports documents?"
}
```

```http
GET /ai/v1/chat/general/
User-Id: demo-user
```

### Football Chat

```http
POST /ai/v1/chat/football/
Content-Type: application/json
User-Id: demo-user

{
  "question": "Summarize the key football information."
}
```

```http
GET /ai/v1/chat/football/
User-Id: demo-user
```

```http
GET /ai/v1/chat/football/cache
User-Id: demo-user
```

```http
PUT /ai/v1/chat/football/cache
Content-Type: application/json
User-Id: demo-user

{}
```

### Weather Chat

```http
POST /ai/v1/chat/weather/
Content-Type: application/json
User-Id: demo-user

{
  "question": "What is the weather in Bilbao?"
}
```

```http
GET /ai/v1/chat/weather/
User-Id: demo-user
```

### Chat Feedback

```http
PUT /ai/v1/chat/<chat_log_id>/like
Content-Type: application/json

{}
```

```http
PUT /ai/v1/chat/<chat_log_id>/dislike
Content-Type: application/json

{}
```

### OCR

```http
POST /ai/v1/ocr/
Content-Type: application/json

{
  "file_url": "https://example.com/document.pdf",
  "questions": ["invoice number", "total amount", "due date"]
}
```

The `questions` list must contain between 1 and 10 entries.

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
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION_NAME=rag_chunks_hybrid
RATELIMIT_STORAGE_URI=redis://localhost:6379
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

### 4. Start Qdrant

Run Qdrant locally with Docker:

```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

On PowerShell:

```powershell
docker run -d --name qdrant `
  -p 6333:6333 -p 6334:6334 `
  -v qdrant_storage:/qdrant/storage `
  qdrant/qdrant:latest
```

Dashboard:

```text
http://127.0.0.1:6333/dashboard
```

### 5. Start Redis

Redis backs the rate limiter (see [Rate Limits](#rate-limits)) and must match
`RATELIMIT_STORAGE_URI`. Run it locally with Docker:

```bash
docker run -d --name ai-redis -p 6379:6379 redis:latest
```

### 6. Start the Flask app

```bash
flask --app webapp.run run
```

The app exposes the health check at:

```text
http://127.0.0.1:5000/
```

### 7. Sync RAG documents

Run this after configuring the Google AI key, MongoDB connection, and Qdrant. The command rebuilds the Qdrant collection and embeds all RAG documents each time.

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

### RAG retrieval evals

A small, zero-dependency harness measures retrieval quality against a hand-built golden set, reporting hit@k, MRR, and recall@k at the source-document level for positive cases, plus abstention accuracy on off-topic questions that should return nothing:

```bash
python -m evals.run_rag_eval
```

It runs against the live Qdrant collection and embedding API, so it is kept separate from the unit test suite (which is fast, deterministic, and free) rather than run on every commit. See [`evals/README.md`](evals/README.md) for the metric definitions and dataset format.

## Engineering Highlights

- Clear separation between API, services, repositories, models, prompts, and tools.
- Strict request validation with Pydantic models and forbidden extra fields, a 1 MB request-body cap (HTTP 413), and bounded inputs such as the 1-10 OCR question list.
- Multi-provider AI abstraction with retry handling and provider fallback for non-chat extraction tasks, with provider clients built lazily so app startup stays fast.
- Built-in web chat UI served from the same Flask app at `/ui`.
- Gemini tool calling with a backend weather function and bounded tool-hop loop.
- RAG pipeline with heading-aware markdown chunking, hybrid retrieval (dense cosine + BM25, fused by Qdrant Reciprocal Rank Fusion), an LLM reranker that reorders without shrinking recall, and a semantic-relevance gate that abstains when nothing clears the cosine floor (instead of answering off-topic questions from keyword overlap).
- Retrieval eval harness (hit@k, MRR, recall@k, plus abstention) over a golden set, kept separate from the unit tests.
- MongoDB indexes for chat history and feedback lookup paths.
- Structured response helpers for consistent API output.
- Focused tests across API routes, services, repositories, DTOs, models, prompts, tools, and CLI behavior.

## Repository Status

This project is a work in progress. The core backend structure, AI service integrations, tests, Docker setup, and CI workflows are in place, while deployment, documentation, and feature polish are still evolving.
