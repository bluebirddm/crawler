#!/bin/bash

echo "Starting Crawler System..."

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    pip install uv
fi

# 检查Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Redis is not installed. Please install Redis first."
    exit 1
fi

# 检查PostgreSQL
if ! command -v /Library/PostgreSQL/17/bin/psql &> /dev/null; then
    echo "PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi

# 安装项目依赖
echo "Installing dependencies..."
uv sync

# 启动Redis
echo "Starting Redis..."
redis-server --daemonize yes

# 等待Redis启动
sleep 2

# 初始化数据库
echo "Initializing database..."
uv run python -c "from src.models import init_db; init_db()"

# 初始化日志文件
echo "Initializing log files..."
mkdir -p logs
touch logs/{api,worker,beat,flower,scrapy,uvicorn}.log
echo "Log files created: api.log, worker.log, beat.log, flower.log, scrapy.log, uvicorn.log"

# 启动Celery Worker
echo "Starting Celery Worker..."
nohup uv run celery -A src.tasks.celery_app worker --loglevel=info --logfile=logs/worker.log > /dev/null 2>&1 &

# 启动Celery Beat
echo "Starting Celery Beat..."
nohup uv run celery -A src.tasks.celery_app beat --loglevel=info --logfile=logs/beat.log > /dev/null 2>&1 &

# 启动Flower
echo "Starting Flower..."
nohup uv run celery -A src.tasks.celery_app flower --port=5555 > logs/flower.log 2>&1 &

# 等待服务启动
sleep 3

# 启动API服务  
echo "Starting API Server..."
nohup uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/uvicorn.log 2>&1 &

# 等待API服务启动
sleep 3

echo "All services started!"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Flower: http://localhost:5555"
echo ""
echo "📄 Log files:"
echo "  API:     logs/api.log"
echo "  Worker:  logs/worker.log"
echo "  Beat:    logs/beat.log"
echo "  Flower:  logs/flower.log"
echo "  Scrapy:  logs/scrapy.log"
echo "  Uvicorn: logs/uvicorn.log"
echo ""
echo "📋 View logs: make logs-api | make logs-worker | make logs-all"

# 检查API服务是否启动成功
echo "Checking API service..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API service is running normally"
else
    echo "❌ API service failed to start, check logs/api.log and logs/uvicorn.log for details"
fi