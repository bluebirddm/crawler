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

# 启动Celery Worker
echo "Starting Celery Worker..."
uv run celery -A src.tasks.celery_app worker --loglevel=info --detach

# 启动Celery Beat
echo "Starting Celery Beat..."
uv run celery -A src.tasks.celery_app beat --loglevel=info --detach

# 启动Flower
echo "Starting Flower..."
uv run celery -A src.tasks.celery_app flower --detach

# 等待服务启动
sleep 3

# 启动API服务
echo "Starting API Server..."
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000

echo "All services started!"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Flower: http://localhost:5555"