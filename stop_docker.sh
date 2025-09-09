#!/usr/bin/env bash

set -euo pipefail

echo "Stopping Crawler System (Docker)..."

# Choose docker compose command (plugin vs legacy)
choose_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

usage() {
  cat <<EOF
Usage: ./stop_docker.sh [options]

Options:
  -v, --volumes    Remove named and anonymous volumes
      --rmi TYPE   Remove images. TYPE is 'local' or 'all'
  -h, --help       Show this help

Examples:
  ./stop_docker.sh           # stop and remove containers, networks
  ./stop_docker.sh -v        # also remove volumes
  ./stop_docker.sh --rmi all # also remove images
EOF
}

COMPOSE_CMD=$(choose_compose_cmd)
if [[ -z "$COMPOSE_CMD" ]]; then
  echo "Docker Compose not found. Please install Docker and Docker Compose."
  exit 1
fi

REMOVE_VOLUMES=0
RMI_TYPE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--volumes)
      REMOVE_VOLUMES=1
      shift
      ;;
    --rmi)
      RMI_TYPE=${2:-}
      if [[ -z "$RMI_TYPE" ]]; then
        echo "--rmi requires an argument: local|all"
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

args=(down --remove-orphans)
if [[ "$REMOVE_VOLUMES" -eq 1 ]]; then
  args+=( -v )
fi
if [[ -n "$RMI_TYPE" ]]; then
  args+=( --rmi "$RMI_TYPE" )
fi

echo "Using command: $COMPOSE_CMD ${args[*]}"
$COMPOSE_CMD "${args[@]}"

echo "✅ All Docker services stopped"
echo "📋 Useful commands:"
echo "  $COMPOSE_CMD ps           # Show current state"
echo "  $COMPOSE_CMD logs         # View last logs"
echo "  $COMPOSE_CMD up -d        # Start again"

