# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A Telegram bot that lets users upload documents (PDF, Excel, Word) and ask questions about them in Russian. Built on a RAG pipeline: Ollama (local LLM + embeddings) + Qdrant (vector store) + aiogram (Telegram bot framework).

## Setup

```bash
poetry install
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN
docker compose up -d  # starts Qdrant on port 6334→6333
ollama serve          # must have gemma3 and nomic-embed-text pulled
```

## Running

```bash
# Development (foreground)
poetry run python -m src.main

# Managed (background, with logs)
make start
make stop
make logs  # tails logs/bot.log
```

## Linting

```bash
poetry run ruff check .          # lint
poetry run ruff check --fix .    # auto-fix imports/style
poetry run ruff format .         # format (tabs, double quotes)
poetry run pre-commit run --all-files
```

## Tests

```bash
poetry run pytest                          # all tests
poetry run pytest tests/path/to/test.py   # single file
```

Evaluation script (requires a running stack):
```bash
python -m scripts.eval
```

## Architecture

**Request flow:**
1. User sends `/ingest` + file → `tg_bot/handlers/ingest.py` downloads it, SHA-256 deduplicates via `SQLiteIngestRegistry` (`docs/ingest_registry.db`), then calls `DocumentIngestion.ingest()`
2. `DocumentIngestion` (`rag/ingest.py`) picks a loader by extension, splits into chunks (text: 700/120 overlap, tables: 400/60), embeds via `EmbeddingHelper`, and upserts into Qdrant via `VectorStoreClient`
3. User sends `/query` + question → `tg_bot/handlers/query.py` calls `query_rag()` which retrieves top-7 chunks via `CustomRetriever`, builds prompt, invokes `ChatOllama`, returns answer

**Key singletons** (`tg_bot/runtime.py`):
- `RAGContainer` — holds shared `ChatOllama`, `VectorStoreClient`, `EmbeddingHelper` instances (heavy to construct, created once at startup)

**Document loaders** (`rag/loaders/loaders.py`):
- `PdfLoader` — PyPDFLoader for text + pdfplumber for tables (separate extraction paths, different chunk sizes)
- `ExcelLoader` — pandas, each row becomes a Document
- `WordLoader` — UnstructuredWordDocumentLoader (marked as not working yet)

**Config** (`environ/`): pydantic-settings, loaded from `.env`. Nested structure: `settings.LLM`, `settings.EMBEDDING`, `settings.VECTOR_STORE`, `settings.TELEGRAM`.

**Fixed collection name**: all documents go into a single Qdrant collection `"questions"` (hardcoded in `handlers/ingest.py`).

**Qdrant** runs in Docker on port `6334` (host) → `6333` (container). Vector size is 1024 (matches `nomic-embed-text`).

**Embedding** is synchronous under the hood (`OllamaEmbeddings`) — wrapped in `run_in_executor` to avoid blocking the async event loop.

## Code style

- Tabs for indentation, double quotes for strings (enforced by ruff)
- Line length: 120
- Python 3.13+, use modern syntax (ruff UP rules active)