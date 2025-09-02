# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a distributed web crawler system with NLP processing capabilities, built using Scrapy for crawling, Celery for task scheduling, FastAPI for API services, and PostgreSQL for data storage.

## Key Commands

### Development Setup
```bash
# Install dependencies (uses uv package manager)
make install

# Initialize database (first time only)
PGPASSWORD=123456 /Library/PostgreSQL/17/bin/createdb -h 127.0.0.1 -p 5432 -U postgres crawler_db
uv run python init_db.py

# Quick start all services
./start.sh
```

### Running Individual Services
```bash
# API service (port 8000)
make run-api

# Celery worker (processes crawl tasks)
make run-worker

# Celery beat (scheduled tasks)
make run-beat

# Flower monitoring (port 5555)
make run-flower

# Run a single crawl
make crawl URL=https://example.com
```

### Testing
```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_nlp.py -v

# Run single test
uv run pytest tests/test_nlp.py::TestNLPProcessor::test_process_article -v
```

### Code Quality
```bash
# Format code
make format

# Lint check
make lint

# Clean cache/temp files
make clean
```

### Docker Operations
```bash
make docker-up    # Start all services
make docker-down  # Stop all services
make docker-logs  # View logs
```

## Architecture Overview

### Service Architecture
The system consists of four main services that communicate through Redis and PostgreSQL:

1. **Scrapy Crawler** (`src/spiders/`) - Fetches web content
   - Entry point: `src/spiders/general.py`
   - Data flows through pipelines defined in `src/pipelines.py`
   - Middleware in `src/middlewares.py` handles retries and proxies

2. **Celery Task Queue** (`src/tasks/`) - Manages async crawl jobs
   - Celery app configuration: `src/tasks/celery_app.py`
   - Task definitions: `src/tasks/crawler_tasks.py`
   - Tasks are triggered via API or scheduled via beat

3. **NLP Processor** (`src/nlp/`) - Analyzes crawled content
   - Main processor: `src/nlp/processor.py` orchestrates all NLP operations
   - Text classification: `src/nlp/classifier.py` (10 predefined categories)
   - Keyword extraction: `src/nlp/extractor.py` (TF-IDF, TextRank)
   - Processing happens in Scrapy pipeline before database storage

4. **FastAPI Service** (`src/api/`) - REST API interface
   - Main app: `src/api/main.py`
   - Routers: `articles.py` (CRUD), `tasks.py` (crawl management), `admin.py` (system ops)

### Data Flow
```
API Request → Celery Task → Scrapy Spider → NLP Pipeline → PostgreSQL
                ↑                                              ↓
              Redis                                     API Response
```

### Database Schema
Single main table `articles` defined in `src/models/article.py`:
- Content fields: url, title, content, author, publish_date
- NLP fields: category, tags, level, sentiment, keywords, summary
- Metadata: crawl_time, update_time, source_domain

### Configuration
- Environment variables: `.env` file (database, Redis, API settings)
- Crawl sources: `config/crawl_sources.json` (URLs and schedules)
- Scrapy settings: `src/settings.py`

## Database Connection

The project uses PostgreSQL with specific connection settings:
- Host: 127.0.0.1 (localhost)
- Port: 5432
- Database: crawler_db
- User: postgres
- Password: 123456 (in .env)

PostgreSQL path is hardcoded in scripts: `/Library/PostgreSQL/17/bin/`

Note: All Python commands should be run with `uv run` prefix to ensure they execute in the virtual environment.

## Special Considerations

1. **Chinese NLP Focus**: The system uses jieba for Chinese text processing and bert-base-chinese model references.

2. **Dependency Management**: Uses `uv` package manager instead of pip directly.

3. **Service Dependencies**: 
   - Redis must be running before Celery services
   - PostgreSQL must be accessible before API/crawler start
   - Database tables must be initialized with `init_db.py`

4. **Crawl Politeness**: 
   - Default download delay: 1 second
   - Concurrent requests: 16
   - Retry times: 3

5. **Task Scheduling**: Celery beat schedule defined in `src/tasks/celery_app.py`:
   - Hourly crawls at minute 0
   - Daily cleanup at 2:00 AM