# Repository Guidelines

## Project Structure & Module Organization
- Source in `src/`:
  - `api/` FastAPI app (`src/api/main.py`, routers).
  - `tasks/` Celery app and tasks (`celery_app.py`, `crawler_tasks.py`).
  - `spiders/` Scrapy spiders (e.g., `general.py`).
  - `models/` SQLAlchemy models (`article.py`, `database.py`).
  - `nlp/` NLP pipeline (`processor.py`, `classifier.py`, `extractor.py`).
  - `utils/` shared helpers; plus `settings.py`, `pipelines.py`, `middlewares.py`, `items.py`.
- Config in `config/` (e.g., `crawl_sources.json`). Tests in `tests/`. Runtime logs in `logs/`.
- Orchestration: `Makefile`, `docker-compose.yml`, `Dockerfile` at repo root.

## Build, Test, and Development Commands
- `make install`: install dependencies via `uv` (Python 3.11).
- `make run-api`: start FastAPI at `http://localhost:8000` with reload.
- `make run-worker` | `make run-beat` | `make run-flower`: start Celery services.
- `make crawl URL=https://example.com`: run Scrapy `general` spider for a URL.
- `make test`: run pytest; `uv run pytest -k api -v` to target tests.
- `make format` | `make lint`: format (black/isort) and lint (flake8/mypy).
- `make docker-up` / `make docker-down`: start/stop all services; `make docker-logs` to tail.
- `make init-db`: initialize tables with SQLAlchemy metadata.

## Coding Style & Naming Conventions
- Python 3.11, 4‑space indent. Black line length 88; isort profile "black".
- Type hints required; `mypy` runs on `src/` (configured in `pyproject.toml`).
- flake8 must pass before merge. Run `make format && make lint` prior to PRs.
- Naming: files/modules and functions `snake_case`; classes `PascalCase`; constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: pytest. Conventions (pyproject): files `test_*.py`, classes `Test*`, functions `test_*`.
- Run with `make test`. Example: `uv run pytest -k nlp -v`.
- Prefer unit tests for utils/NLP/spiders; use FastAPI `TestClient` for API routes. Avoid external network calls—use fixtures or sample HTML.

## Commit & Pull Request Guidelines
- History is minimal; adopt Conventional Commits (e.g., `feat(api): add search endpoint`, `fix(spider): handle 403`).
- PRs: small and focused. Include description, linked issues, test plan (commands + expected output), and any config changes (e.g., `config/crawl_sources.json`).

## Security & Configuration Tips
- Do not commit secrets. Use `.env` (see `.env.example`). Docker uses dev credentials—never reuse in prod.
- Update `config/crawl_sources.json` atomically and validate fields referenced by `spiders/general.py`.

## Architecture Overview
```
[Clients/CLI/Frontend] → FastAPI (Uvicorn)
         │                   │
         │ HTTP/API calls    │ Enqueue tasks
         ▼                   ▼
     Routers/Services → Celery (worker, beat) ← Flower (monitor)
            │                 │
            │ calls           │ broker/results
            ▼                 ▼
      Scrapy Spiders     Redis (broker)
            │
            ▼
         NLP Pipeline → PostgreSQL (storage)
```
- API in `src/api` enqueues work to Celery (`src/tasks`). Workers run spiders (`src/spiders`) and NLP (`src/nlp`), persist via `src/models`.
- Local dev via `make run-*`; full stack via `docker-compose` (Redis, Postgres, API, workers, Flower).
