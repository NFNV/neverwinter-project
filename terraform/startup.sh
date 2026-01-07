#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[startup] $*"
}

need_install=0
if ! command -v docker >/dev/null 2>&1; then
  need_install=1
fi
if ! command -v git >/dev/null 2>&1; then
  need_install=1
fi
if ! command -v docker-compose >/dev/null 2>&1; then
  if command -v docker >/dev/null 2>&1; then
    if ! docker compose version >/dev/null 2>&1; then
      need_install=1
    fi
  else
    need_install=1
  fi
fi

if [ "$need_install" -eq 1 ]; then
  log "Installing dependencies"
  apt-get update -y
  apt-get install -y docker.io docker-compose docker-compose-plugin git
fi

systemctl enable --now docker || true

for _ in $(seq 1 30); do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker info >/dev/null 2>&1; then
  log "Docker did not become ready in time"
  exit 1
fi

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
    return
  fi
  log "Docker Compose not available"
  exit 1
}

repo_dir="/opt/neverwinter-project"
compose_file="$repo_dir/ops/docker-compose.prod.yml"

if [ ! -d "$repo_dir/.git" ]; then
  log "Cloning repository"
  git clone https://github.com/NFNV/neverwinter-project.git "$repo_dir"
fi

cd "$repo_dir"

git fetch --tags --force --prune

latest_tag=$(git tag --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | head -n 1)
if [ -z "$latest_tag" ]; then
  log "No release tag found"
  exit 1
fi

git checkout -f "$latest_tag"

if [ ! -f "$compose_file" ]; then
  log "Missing compose file at $compose_file"
  exit 1
fi

mkdir -p "$repo_dir/servervault" "$repo_dir/database" "$repo_dir/logs"

if ! compose -f "$compose_file" pull; then
  log "Image pull failed; continuing with cached images"
fi

compose -f "$compose_file" up -d
