#!/usr/bin/env bash

set -euo pipefail

# Enable bash trace with DEBUG=1 ./start_docker.sh
if [[ "${DEBUG:-0}" == "1" ]]; then
  set -x
fi

echo "Starting Crawler System (Docker)..."

# Detect and wrap docker compose (plugin vs legacy)
COMPOSE_STYLE=""
detect_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_STYLE="plugin" # docker compose
    return 0
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_STYLE="legacy" # docker-compose
    return 0
  else
    return 1
  fi
}

compose() {
  if [[ "$COMPOSE_STYLE" == "plugin" ]]; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# Print quick diagnostics on any error
on_error() {
  local code=$?
  echo "❌ An error occurred (exit $code). Quick diagnostics:"
  compose ps || true
  echo "---- Recent API logs ----"; compose logs --tail=100 api 2>/dev/null || true
  echo "---- Recent worker logs ----"; compose logs --tail=100 celery_worker 2>/dev/null || true
  echo "---- Recent beat logs ----"; compose logs --tail=100 celery_beat 2>/dev/null || true
}
trap on_error ERR

if ! detect_compose; then
  echo "Docker Compose not found. Please install Docker and Docker Compose."
  echo "- Docker Desktop (includes 'docker compose') or 'docker-compose' binary"
  exit 1
fi

# Pretty name for printing examples
if [[ "$COMPOSE_STYLE" == "plugin" ]]; then
  COMPOSE_PRINT="docker compose"
else
  COMPOSE_PRINT="docker-compose"
fi

REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --rebuild|--no-cache)
      REBUILD=1
      ;;
    *) ;;
  esac
done

# Prepare host log directory (mounted into containers)
mkdir -p logs
touch logs/{api,worker,beat,flower,scrapy,uvicorn}.log || true

# Check common host port conflicts to avoid compose failures
check_port() {
  local port=$1
  if command -v nc >/dev/null 2>&1; then
    if nc -z localhost "$port" >/dev/null 2>&1; then
      return 0
    fi
  elif command -v lsof >/dev/null 2>&1; then
    if lsof -i ":$port" -sTCP:LISTEN -n | grep -q ":$port"; then
      return 0
    fi
  else
    return 2
  fi
  return 1
}

conflicts=()
for p in 6379 5432 8000 5555; do
  if check_port "$p"; then
    conflicts+=("$p")
  fi
done

if [[ ${#conflicts[@]} -gt 0 ]]; then
  echo "⚠️  Detected host ports in use: ${conflicts[*]}"
  echo "These conflict with docker compose port mappings."
  echo "Tip: If you previously ran local services, run ./stop.sh first."
  echo "Or stop the processes using those ports, then re-run this script."
  read -r -p "Continue anyway? [y/N] " ans
  if [[ ! "$ans" =~ ^[Yy]$ ]]; then
    echo "Aborting due to port conflicts."; exit 1
  fi
fi

echo "Using command: $COMPOSE_PRINT"

if [[ "$REBUILD" -eq 1 ]]; then
  echo "Building images (no cache)..."
  compose build --no-cache
else
  echo "Building images..."
  compose build
fi

echo "Starting core services: redis, postgres..."
compose up -d redis postgres

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
retry 60 1 "Redis" compose exec -T redis redis-cli ping >/dev/null 2>&1 || {
  echo "Redis did not become ready in time."; exit 1; }

echo "Waiting for PostgreSQL to be ready..."
retry 60 1 "Postgres" compose exec -T postgres pg_isready -U postgres -d crawler_db >/dev/null 2>&1 || {
  echo "PostgreSQL did not become ready in time."; exit 1; }

# Optionally initialize DB tables (API also does this on startup)
echo "Initializing database tables (one-off task)..."
compose run --rm api uv run python -c "from src.models import init_db; init_db()" >/dev/null 2>&1 || true

echo "Starting application services: api, celery_worker, celery_beat, flower..."
compose up -d api celery_worker celery_beat flower

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
  if retry 60 1 "API (in-container)" compose exec -T api sh -lc 'curl -sf --max-time 2 http://localhost:8000/health' >/dev/null 2>&1; then
    API_HEALTH_OK=1
  fi
fi

if [[ "$API_HEALTH_OK" -eq 1 ]]; then
  echo "✅ API service is running normally"
else
  echo "❌ API service health check failed. Check logs via:"
  echo "   $COMPOSE_PRINT logs api"
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
echo "  $COMPOSE_PRINT logs -f            # Tail all"
echo "  $COMPOSE_PRINT logs -f api        # Tail API"
echo "  $COMPOSE_PRINT ps                 # Show container status"
echo "  $COMPOSE_PRINT down               # Stop all"
