#!/bin/bash

set -euo pipefail

# Trace mode: DEBUG=1 ./start.sh
if [[ "${DEBUG:-0}" == "1" ]]; then
  set -x
fi

echo "Starting Crawler System (host)…"

# Always run from repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Lightweight .env reader for specific keys (avoid sourcing values with spaces)
load_env_var() {
  local key="$1"; local default_val="$2"; local val=""
  # Prefer already-exported env
  if [[ -n "${!key:-}" ]]; then
    echo "${!key}"
    return 0
  fi
  if [[ -f .env ]]; then
    val=$(grep -E "^${key}=" .env 2>/dev/null | tail -n1 | cut -d'=' -f2- || true)
  fi
  if [[ -n "$val" ]]; then
    echo "$val"
  else
    echo "$default_val"
  fi
}

command_exists() { command -v "$1" >/dev/null 2>&1; }

PYTHON="$(command -v python3 || command -v python || true)"
if [[ -z "${PYTHON}" ]]; then
  echo "Python is not installed. Please install Python 3.11+ or use Docker (./start_docker.sh)."
  exit 1
fi

HAVE_UV=0
if command_exists uv; then
  HAVE_UV=1
fi

# # 检查Redis
# if ! command -v redis-cli &> /dev/null; then
#     echo "Redis is not installed. Please install Redis first."
#     exit 1
# fi

# # 检查PostgreSQL
# if ! command -v /Library/PostgreSQL/17/bin/psql &> /dev/null; then
#     echo "PostgreSQL is not installed. Please install PostgreSQL first."
#     exit 1
# fi

echo "Installing dependencies…"
if [[ "$HAVE_UV" -eq 1 ]]; then
  echo "Using uv to sync environment"
  uv sync
else
  # Fallback to pip if uv is not available
  PY_MAJOR="$($PYTHON -c 'import sys; print(sys.version_info[0])')"
  PY_MINOR="$($PYTHON -c 'import sys; print(sys.version_info[1])')"
  if (( PY_MAJOR > 3 || (PY_MAJOR == 3 && PY_MINOR >= 11) )); then
    echo "uv not found; falling back to pip install . (Python ${PY_MAJOR}.${PY_MINOR})"
    if $PYTHON -m pip --version >/dev/null 2>&1; then
      $PYTHON -m pip install --upgrade pip >/dev/null 2>&1 || true
      # Install runtime dependencies from pyproject via PEP 621
      $PYTHON -m pip install .
    else
      echo "pip is not available for $PYTHON. Please install pip or install uv."
      exit 1
    fi
  else
    echo "❌ Python ${PY_MAJOR}.${PY_MINOR} detected. This project requires Python 3.11+."
    echo "   Please either install Python 3.11+ or install 'uv' (https://astral.sh/uv) to manage it,"
    echo "   or run the Docker workflow: ./start_docker.sh"
    exit 1
  fi
fi

# Command wrappers (uv run if available, otherwise python -m …)
if [[ "$HAVE_UV" -eq 1 ]]; then
  RUN_PY=(uv run python)
  RUN_CELERY=(uv run celery)
  RUN_UVICORN=(uv run uvicorn)
else
  RUN_PY=("$PYTHON")
  RUN_CELERY=("$PYTHON" -m celery)
  RUN_UVICORN=("$PYTHON" -m uvicorn)
fi

# Quick host-port readiness checks (helpful when Redis/Postgres run in Docker)
wait_for_tcp() {
  local host="$1"; shift
  local port="$1"; shift
  local name="$1"; shift
  local timeout="${1:-30}"; shift || true
  local start_ts now
  start_ts=$(date +%s)
  while true; do
    if command -v nc >/dev/null 2>&1; then
      if nc -z "$host" "$port" >/dev/null 2>&1; then
        echo "${name} reachable at ${host}:${port}"
        return 0
      fi
    else
      if (echo > "/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
        echo "${name} reachable at ${host}:${port}"
        return 0
      fi
    fi
    now=$(date +%s)
    if (( now - start_ts >= timeout )); then
      echo "Timeout waiting for ${name} at ${host}:${port}."
      return 1
    fi
    sleep 1
  done
}

REDIS_HOST="$(load_env_var REDIS_HOST localhost)"
REDIS_PORT="$(load_env_var REDIS_PORT 6379)"
DB_HOST="$(load_env_var DB_HOST 127.0.0.1)"
DB_PORT="$(load_env_var DB_PORT 5432)"
DB_USER="$(load_env_var DB_USER postgres)"
DB_NAME="$(load_env_var DB_NAME crawler_db)"
DB_PASSWORD="$(load_env_var DB_PASSWORD '')"

echo "Checking external services…"
wait_for_tcp "$REDIS_HOST" "$REDIS_PORT" "Redis" 30 || {
  echo "❌ Cannot reach Redis at ${REDIS_HOST}:${REDIS_PORT}. If using Docker, run: docker compose up -d redis"
  exit 1
}
wait_for_tcp "$DB_HOST" "$DB_PORT" "PostgreSQL" 30 || {
  echo "❌ Cannot reach PostgreSQL at ${DB_HOST}:${DB_PORT}. If using Docker, run: docker compose up -d postgres"
  exit 1
}

# Sanity check: common docker-compose default password is 123456 in this repo
if [[ "$DB_HOST" == "127.0.0.1" || "$DB_HOST" == "localhost" ]]; then
  if grep -Eq "POSTGRES_PASSWORD:\s*123456" docker-compose.yml 2>/dev/null; then
    if [[ "${DB_PASSWORD:-}" != "123456" ]]; then
      echo "⚠️  DB_PASSWORD in .env is '${DB_PASSWORD:-<empty>}' but docker-compose uses '123456'."
      echo "    Update .env to DB_PASSWORD=123456 if you’re using the provided postgres container."
    fi
  fi
fi

# # 启动Redis
# echo "Starting Redis..."
# redis-server --daemonize yes

# # 等待Redis启动
# sleep 2

echo "Initializing database tables…"
if ! "${RUN_PY[@]}" -c "from src.models import init_db; init_db()"; then
  echo "❌ Database init failed. Verify connection settings:"
  echo "   postgresql://${DB_USER}:<password>@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  exit 1
fi

# 初始化日志文件
echo "Initializing log files..."
mkdir -p logs
touch logs/{api,worker,beat,flower,scrapy,uvicorn}.log
echo "Log files created: api.log, worker.log, beat.log, flower.log, scrapy.log, uvicorn.log"

echo "Starting Celery Worker…"
nohup "${RUN_CELERY[@]}" -A src.tasks.celery_app worker --loglevel=info --logfile=logs/worker.log >> logs/worker.log 2>&1 &

echo "Starting Celery Beat…"
nohup "${RUN_CELERY[@]}" -A src.tasks.celery_app beat --loglevel=info --logfile=logs/beat.log >> logs/beat.log 2>&1 &

echo "Starting Flower…"
nohup "${RUN_CELERY[@]}" -A src.tasks.celery_app flower --port=5555 >> logs/flower.log 2>&1 &

# 等待服务启动
sleep 3

echo "Starting API Server…"
nohup "${RUN_UVICORN[@]}" src.api.main:app --host 0.0.0.0 --port 8000 >> logs/uvicorn.log 2>&1 &

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
echo "Checking API service…"
if command -v curl >/dev/null 2>&1; then
  if curl -sSf --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then
      echo "✅ API service is running normally"
  else
      echo "❌ API health check failed. See logs/api.log and logs/uvicorn.log"
  fi
else
  echo "curl not found; skip health check. Use: curl http://localhost:8000/health"
fi
