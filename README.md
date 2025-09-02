# Web Crawler with NLP Processing

A complete web crawler system with scheduled crawling, text classification, keyword extraction and intelligent tagging.

## Features

- **Scrapy Framework** - High-performance distributed crawling
- **NLP Processing** - Auto classification, tagging, sentiment analysis  
- **Celery Scheduler** - Scheduled tasks, async processing
- **FastAPI Service** - RESTful API service
- **PostgreSQL Storage** - Structured data persistence
- **Docker Deployment** - One-click containerized deployment

## Tech Stack

```
[Scrapy] ----> [Redis] <---- [Celery]
    |                            |
    v                            v
[NLP] -------> [PostgreSQL] <---- [FastAPI]
```

## Quick Start

### 1. Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### 2. Local Installation

```bash
# Clone project
git clone <repository-url>
cd crawler

# Install dependency manager
pip install uv

# Install project dependencies
uv sync

# Copy environment config
cp .env.example .env
# Edit .env file to set database connection
```

### 3. Database Setup

```bash
# Create database (adjust host/port as needed)
PGPASSWORD=123456 /Library/PostgreSQL/17/bin/createdb -h 127.0.0.1 -p 5432 -U postgres crawler_db

# Or using psql
PGPASSWORD=123456 /Library/PostgreSQL/17/bin/psql -h 127.0.0.1 -p 5432 -U postgres -c "CREATE DATABASE crawler_db;"

# Initialize database tables
uv run python init_db.py
```

### 4. Start Services

#### Method 1: Using startup script (recommended)
```bash
./start.sh
```

#### Method 2: Using Makefile
```bash
# Run in different terminal windows
make run-api      # Start API service
make run-worker   # Start Celery Worker
make run-beat     # Start Celery Beat
make run-flower   # Start Flower monitoring
```

#### Method 3: Manual startup
```bash
# Start Redis
redis-server

# Start API service
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery Worker
uv run celery -A src.tasks.celery_app worker --loglevel=info

# Start Celery Beat
uv run celery -A src.tasks.celery_app beat --loglevel=info

# Start Flower monitoring
uv run celery -A src.tasks.celery_app flower
```

### 5. Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Usage

### Basic Info
- **API URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower**: http://localhost:5555

### Main Endpoints

#### 1. Crawl Single URL
```bash
curl -X POST "http://localhost:8000/api/tasks/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.36kr.com"}'
```

#### 2. Batch Crawl
```bash
curl -X POST "http://localhost:8000/api/tasks/crawl/batch" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.36kr.com", "https://www.ifanr.com"]}'
```

#### 3. Get Articles
```bash
# Get all articles
curl "http://localhost:8000/api/articles"

# Filter by category
curl "http://localhost:8000/api/articles?category=tech&limit=10"

# Filter by level
curl "http://localhost:8000/api/articles?level=3&limit=10"

# Get recent articles
curl "http://localhost:8000/api/articles?days=7"
```

#### 4. Search Articles
```bash
curl "http://localhost:8000/api/articles/search?q=AI"
```

#### 5. Get Statistics
```bash
# Category stats
curl "http://localhost:8000/api/articles/stats/categories"

# Daily stats
curl "http://localhost:8000/api/articles/stats/daily?days=7"
```

#### 6. Task Status
```bash
# Get task status
curl "http://localhost:8000/api/tasks/status/{task_id}"

# View active tasks
curl "http://localhost:8000/api/tasks/active"

# View scheduled tasks
curl "http://localhost:8000/api/tasks/scheduled"
```

#### 7. System Admin
```bash
# System info
curl "http://localhost:8000/api/admin/system/info"

# Worker status
curl "http://localhost:8000/api/admin/workers/status"

# Cleanup old data
curl -X POST "http://localhost:8000/api/admin/database/cleanup?days=90"
```

## Crawler Configuration

Edit `config/crawl_sources.json` to configure crawl sources:

```json
{
  "sources": [
    {
      "name": "Tech Blog",
      "enabled": true,
      "urls": [
        "https://www.infoq.cn/",
        "https://segmentfault.com/"
      ],
      "spider": "general",
      "category": "tech"
    }
  ]
}
```

## NLP Features

The system automatically processes crawled articles:

### 1. Text Classification
- Auto-classify into 10 predefined categories
- Categories: Tech, Finance, Education, Health, Entertainment, Sports, Policy, Society, Culture, International

### 2. Quality Grading
- 1-5 quality scoring system
- Based on content length, keyword density, originality indicators

### 3. Keyword Extraction
- TF-IDF algorithm
- TextRank algorithm
- Frequency statistics
- Combined algorithm results

### 4. Tag Generation
- Auto-extract 10 key tags
- Chinese word segmentation support

### 5. Sentiment Analysis
- Positive/negative sentiment analysis
- Sentiment score from -1 to 1

### 6. Summary Generation
- Auto-generate 200-character summary
- Based on key sentence extraction

## Project Structure

```
crawler/
├── src/                    # Source code
│   ├── api/               # FastAPI endpoints
│   ├── models/            # Database models
│   ├── nlp/              # NLP processing
│   ├── spiders/          # Scrapy spiders
│   ├── tasks/            # Celery tasks
│   └── utils/            # Utilities
├── config/               # Configuration files
├── tests/                # Test code
├── logs/                 # Log files
├── docker-compose.yml    # Docker compose
├── Dockerfile           # Docker image
├── Makefile             # Build scripts
├── pyproject.toml       # Project config
├── init_db.py           # DB initialization
├── start.sh             # Startup script
└── README.md            # Documentation
```

## Development Guide

### Run Tests
```bash
# Install dev dependencies
uv sync --dev

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_nlp.py -v
```

### Code Formatting
```bash
# Format code
make format

# Check code quality
make lint
```

### Add New Spider
1. Create new spider file in `src/spiders/`
2. Inherit from `scrapy.Spider` class
3. Implement `parse` method
4. Add crawl source in config file

### Add New API Endpoint
1. Create new router file in `src/api/routers/`
2. Implement endpoint logic
3. Register router in `src/api/main.py`

## Operations

### Log Viewing
```bash
# API logs
tail -f logs/api.log

# Scrapy logs
tail -f logs/scrapy.log

# Celery logs
docker-compose logs -f celery_worker
```

### Database Management
```bash
# Backup database
pg_dump -h 192.168.0.167 -U postgres crawler_db > backup.sql

# Restore database
psql -h 192.168.0.167 -U postgres crawler_db < backup.sql

# Cleanup old data
curl -X POST "http://localhost:8000/api/admin/database/cleanup?days=30"
```

### Performance Monitoring
- Flower monitoring: http://localhost:5555
- View task queue status
- Monitor worker performance
- View task execution history

## Troubleshooting

### 1. Database Connection Failed
- Check if PostgreSQL service is running
- Verify database config in .env
- Check firewall settings

### 2. Celery Tasks Not Executing
- Check if Redis service is running
- Verify Worker process is running
- Check Celery logs for errors

### 3. Crawl Failed
- Check if target website is accessible
- View logs/scrapy.log file
- Check USER_AGENT settings

### 4. NLP Processing Error
- Verify jieba tokenizer loaded properly
- Check text encoding issues
- View processing logs

### 5. Docker Startup Failed
- Ensure Docker and Docker Compose installed
- Check if ports are occupied
- View docker-compose logs

## Contributing

Welcome to submit Issues and Pull Requests!

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

MIT License

## Contact

For questions or suggestions, please submit an Issue or contact the maintainer.

---

**Note**: Please follow website robots.txt rules and terms of service, use crawler responsibly.