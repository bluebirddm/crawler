#!/bin/bash

echo "Stopping Crawler System..."

# 停止Celery服务
echo "Stopping Celery services..."
pkill -f "celery -A src.tasks.celery_app worker"
pkill -f "celery -A src.tasks.celery_app beat"
pkill -f "celery -A src.tasks.celery_app flower"

# 停止API服务
echo "Stopping API service..."
pkill -f "uvicorn src.api.main:app"

# 停止Redis（可选，如果你想保留Redis运行，可以注释掉）
echo "Stopping Redis..."
redis-cli shutdown

echo "All services stopped!"

# 清理临时文件
echo "Cleaning up temporary files..."
rm -f celerybeat-schedule
rm -f celerybeat.pid

echo "Cleanup completed!"