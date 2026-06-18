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
- Dockerized production runtime with Gunicorn and gevent.
- CI for linting, tests, coverage, Docker image validation, dependency updates, and security scanning.

## Tech Stack

- Python, Flask, Gunicorn, gevent
- MongoDB with MongoEngine
- Qdrant for local vector search
- Pydantic request validation
- Google Gemini, Mistral, and OpenAI provider integrations
- LangChain-related dependencies for AI workflows
- pytest, pytest-cov, Ruff
- Docker, GitHub Actions, Semgrep, Dependabot

## Architecture

The application is organized around a small Flask API surface and a service layer that owns the AI behavior.

```text
rag_docs/          Markdown knowledge sources used for RAG
evals/             RAG retrieval eval harness (hit@k, MRR, recall@k)
webapp/
  api/             HTTP blueprints, validation, response formatting
  services/        AI orchestration, RAG, OCR, chat, domain assistants
  repositories/    MongoDB and Qdrant persistence access
  models/          MongoEngine document models
  prompts/         Prompt builders per assistant/task
  tools/           Model-callable tools, such as weather lookup
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

### LangChain Agent Experiments

These endpoints exercise LangChain and DeepAgents workflows separately from the main chat services. The simple endpoint runs a LangChain agent with a small weather tool, while the complex endpoint compares a LangChain agent with a DeepAgents setup on a tool-grounded document task.

```http
POST /ai/v1/lang/simple
Content-Type: application/json

{
  "question": "Explain retrieval augmented generation in one paragraph."
}
```

```http
POST /ai/v1/lang/complex
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
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION_NAME=rag_chunks_hybrid
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

### 5. Start the Flask app

```bash
flask --app webapp.run run
```

The app exposes the health check at:

```text
http://127.0.0.1:5000/
```

### 6. Sync RAG documents

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
- Strict request validation with Pydantic models and forbidden extra fields.
- Multi-provider AI abstraction with retry handling and provider fallback for non-chat extraction tasks.
- Gemini tool calling with a backend weather function and bounded tool-hop loop.
- RAG pipeline with heading-aware markdown chunking, hybrid retrieval (dense cosine + BM25, fused by Qdrant Reciprocal Rank Fusion), and an LLM reranker that reorders without shrinking recall.
- Retrieval eval harness (hit@k, MRR, recall@k, plus abstention) over a golden set, kept separate from the unit tests.
- MongoDB indexes for chat history and feedback lookup paths.
- Structured response helpers for consistent API output.
- Focused tests across API routes, services, repositories, DTOs, models, prompts, tools, and CLI behavior.

## Repository Status

This project is a work in progress. The core backend structure, AI service integrations, tests, Docker setup, and CI workflows are in place, while deployment, documentation, and feature polish are still evolving.
