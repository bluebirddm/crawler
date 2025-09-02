.PHONY: install test run clean docker-build docker-up docker-down

# 安装依赖
install:
	pip install uv
	uv sync

# 运行测试
test:
	uv run pytest tests/ -v

# 启动API服务
run-api:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker
run-worker:
	uv run celery -A src.tasks.celery_app worker --loglevel=info

# 启动Celery Beat
run-beat:
	uv run celery -A src.tasks.celery_app beat --loglevel=info

# 启动Flower
run-flower:
	uv run celery -A src.tasks.celery_app flower

# 运行爬虫
crawl:
	uv run scrapy crawl general -a start_url=$(URL)

# Docker相关
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf logs/*.log

# 代码格式化
format:
	uv run black src/ tests/
	uv run isort src/ tests/

# 代码检查
lint:
	uv run flake8 src/ tests/
	uv run mypy src/

# 数据库初始化
init-db:
	uv run python -c "from src.models import init_db; init_db()"

# 创建数据库（仅用于首次设置）
create-db:
	PGPASSWORD=123456 /Library/PostgreSQL/17/bin/createdb -h 127.0.0.1 -p 5432 -U postgres crawler_db

# 帮助
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make run-api     - Start API server"
	@echo "  make run-worker  - Start Celery worker"
	@echo "  make run-beat    - Start Celery beat"
	@echo "  make run-flower  - Start Flower monitoring"
	@echo "  make crawl URL=  - Run crawler for specific URL"
	@echo "  make docker-up   - Start Docker services"
	@echo "  make docker-down - Stop Docker services"
	@echo "  make clean       - Clean cache files"
	@echo "  make format      - Format code"
	@echo "  make lint        - Check code quality"
	@echo "  make init-db     - Initialize database tables"