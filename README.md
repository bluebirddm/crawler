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

启动后系统会显示：
- 各服务的访问地址
- 日志文件位置信息  
- 日志查看命令提示

#### Method 2: Using Makefile
```bash
# Run in different terminal windows
make run-api      # Start API service
make run-worker   # Start Celery Worker
make run-beat     # Start Celery Beat  
make run-flower   # Start Flower monitoring

# 查看服务日志（启动后使用）
make logs-api     # 实时查看API日志
make logs-worker  # 实时查看Worker日志
 
# 运行 Scrapy（支持单/多 URL）
# 单个 URL：
uv run scrapy crawl general -a start_url="http://httpbin.org/html"
# 多个 URL（逗号分隔或 JSON 数组）：
uv run scrapy crawl general -a start_urls="http://httpbin.org/html, https://example.com"
uv run scrapy crawl general -a start_urls='["http://httpbin.org/html", "https://example.com"]'
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
# Option A: One-click startup script (recommended)
./start_docker.sh           # builds, starts, waits, and health-checks
# Rebuild without cache
./start_docker.sh --rebuild

# Stop all services
./stop_docker.sh            # compose down (remove orphans)
# Stop and remove volumes/images as needed
./stop_docker.sh -v         # also remove volumes
./stop_docker.sh --rmi all  # also remove images

# Option B: Raw docker compose
docker compose up -d        # or: docker-compose up -d
docker compose logs -f      # tail logs
docker compose down         # stop all
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

## 日志系统架构

### 技术实现

本项目采用分布式日志架构，每个服务维护独立的日志文件：

#### 1. API服务日志 (loguru)
```python
# 配置位置: src/api/main.py
logger.add(
    "logs/api.log",
    rotation="10 MB",      # 文件轮转
    retention="7 days",    # 保留时间
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    level="INFO",
    enqueue=True          # 异步写入
)
```

#### 2. Celery服务日志
```python  
# 配置位置: src/tasks/celery_app.py
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)
```

#### 3. Scrapy爬虫日志
```python
# 配置位置: src/settings.py  
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scrapy.log'
```

#### 4. 日志轮转策略
- **API日志**: 按文件大小轮转（10MB），保留7天
- **Worker日志**: 按天轮转，保留30天
- **Scrapy日志**: 手动管理，建议定期清理大文件

#### 5. 性能优化
- 异步日志写入，避免阻塞主线程
- 日志级别可配置，生产环境建议使用INFO级别
- 支持日志文件压缩和自动清理

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
├── logs/                 # 统一日志目录（api.log, worker.log, beat.log等）
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

### 日志管理系统

本系统提供了统一的日志管理和查看工具，所有服务日志都集中存储在 `logs/` 目录下。

#### 日志文件结构
```
logs/
├── api.log          # FastAPI服务日志（loguru格式，自动轮转）
├── worker.log       # Celery Worker任务处理日志
├── beat.log         # Celery Beat调度器日志
├── flower.log       # Flower监控服务日志
├── uvicorn.log      # Uvicorn ASGI服务器日志
└── scrapy.log       # Scrapy爬虫引擎日志
```

#### 日志查看命令
```bash
# 查看特定服务日志（实时跟踪）
make logs-api        # 查看API服务日志
make logs-worker     # 查看Celery Worker日志
make logs-beat       # 查看Celery Beat日志
make logs-flower     # 查看Flower监控日志
make logs-scrapy     # 查看Scrapy爬虫日志
make logs-uvicorn    # 查看Uvicorn服务器日志

# 查看所有日志
make logs-all        # 同时跟踪所有服务日志

# 日志管理
make logs-size       # 查看所有日志文件大小
make logs-clean      # 清空所有日志文件（谨慎操作）
```

#### 日志配置特性

1. **智能轮转**: API日志自动按10MB大小轮转，保留7天
2. **统一格式**: 所有日志使用一致的时间戳和级别格式
3. **双重输出**: 关键日志同时输出到文件和控制台
4. **性能优化**: 异步日志写入，不影响服务性能

#### 日志级别说明
- **INFO**: 服务启动、数据库操作、任务执行等正常信息
- **WARNING**: 重试操作、配置问题等需要关注的警告
- **ERROR**: 服务异常、数据库连接失败、任务执行失败等错误
- **DEBUG**: 详细的调试信息（需要修改配置启用）

#### 常见日志查看场景
```bash
# 调试API接口问题
make logs-api

# 检查爬虫任务执行状态
make logs-worker

# 查看定时任务调度情况
make logs-beat

# 监控整体系统运行状态
make logs-all

# 检查磁盘空间使用
make logs-size
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
- Check Celery logs: `make logs-worker` or `make logs-beat`
- View Flower监控: http://localhost:5555

### 3. Crawl Failed
- Check if target website is accessible
- View Scrapy logs: `make logs-scrapy`
- Check USER_AGENT settings in src/settings.py
- Verify proxy middleware configuration

### 4. NLP Processing Error
- Verify jieba tokenizer loaded properly
- Check text encoding issues
- View API processing logs: `make logs-api`
- Check database connection status

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
