#!/usr/bin/env bash

set -euo pipefail

echo "Starting Crawler System (Docker)..."

# Choose docker compose command (plugin vs legacy)
choose_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""  # not found
  fi
}

COMPOSE_CMD=$(choose_compose_cmd)
if [[ -z "$COMPOSE_CMD" ]]; then
  echo "Docker Compose not found. Please install Docker and Docker Compose."
  echo "- Docker Desktop (includes 'docker compose') or 'docker-compose' binary"
  exit 1
fi

REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --rebuild|--no-cache)
      REBUILD=1
      shift
      ;;
    *) ;;
  esac
done

# Prepare host log directory (mounted into containers)
mkdir -p logs
touch logs/{api,worker,beat,flower,scrapy,uvicorn}.log || true

echo "Using command: $COMPOSE_CMD"

if [[ "$REBUILD" -eq 1 ]]; then
  echo "Building images (no cache)..."
  $COMPOSE_CMD build --no-cache
else
  echo "Building images..."
  $COMPOSE_CMD build
fi

echo "Starting core services: redis, postgres..."
$COMPOSE_CMD up -d redis postgres

# Wait helpers
retry() {
  local tries=$1; shift
  local delay=$1; shift
  local name=$1; shift
  local i
  for ((i=1; i<=tries; i++)); do
    if "$@"; then
      echo "$name is ready"
      return 0
    fi
    if (( i < tries )); then
      sleep "$delay"
    fi
  done
  return 1
}

echo "Waiting for Redis to be ready..."
retry 60 1 "Redis" $COMPOSE_CMD exec -T redis redis-cli ping >/dev/null 2>&1 || {
  echo "Redis did not become ready in time."; exit 1; }

echo "Waiting for PostgreSQL to be ready..."
retry 60 1 "Postgres" $COMPOSE_CMD exec -T postgres pg_isready -U postgres -d crawler_db >/dev/null 2>&1 || {
  echo "PostgreSQL did not become ready in time."; exit 1; }

# Optionally initialize DB tables (API also does this on startup)
echo "Initializing database tables (one-off task)..."
$COMPOSE_CMD run --rm api uv run python -c "from src.models import init_db; init_db()" >/dev/null 2>&1 || true

echo "Starting application services: api, celery_worker, celery_beat, flower..."
$COMPOSE_CMD up -d api celery_worker celery_beat flower

# Health check API (retry)
echo "Checking API service health..."
API_HEALTH_OK=0
if command -v curl >/dev/null 2>&1; then
  if retry 60 1 "API (host port)" curl -sf --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then
    API_HEALTH_OK=1
  fi
fi

if [[ "$API_HEALTH_OK" -eq 0 ]]; then
  # Fallback: exec curl inside api container (Dockerfile includes curl)
  if retry 60 1 "API (in-container)" $COMPOSE_CMD exec -T api sh -lc 'curl -sf --max-time 2 http://localhost:8000/health' >/dev/null 2>&1; then
    API_HEALTH_OK=1
  fi
fi

if [[ "$API_HEALTH_OK" -eq 1 ]]; then
  echo "✅ API service is running normally"
else
  echo "❌ API service health check failed. Check logs via:"
  echo "   $COMPOSE_CMD logs api"
fi

echo ""
echo "All services started!"
echo "API:      http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Flower:   http://localhost:5555"
echo ""
echo "📄 Log files (mounted): logs/"
echo "  API:     logs/api.log"
echo "  Worker:  logs/worker.log"
echo "  Beat:    logs/beat.log"
echo "  Flower:  logs/flower.log"
echo "  Scrapy:  logs/scrapy.log"
echo "  Uvicorn: logs/uvicorn.log"
echo ""
echo "📋 Useful commands:"
echo "  $COMPOSE_CMD logs -f            # Tail all"
echo "  $COMPOSE_CMD logs -f api        # Tail API"
echo "  $COMPOSE_CMD ps                 # Show container status"
echo "  $COMPOSE_CMD down               # Stop all"
