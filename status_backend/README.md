# NWN Status Backend

Lightweight FastAPI service that reports NWN server status based on Docker container state and exposes health and status endpoints. The `online` field reflects whether the NWN container is running, not UDP query results.

## Environment variables

- NWN_CONTAINER_NAME: Docker container name to check (default: nwn-ee-pw)
- DOCKER_SOCK: path to docker.sock (default: /var/run/docker.sock)
- NWN_HOST / NWN_PORT: reserved for future diagnostics (not used for online status)

## Endpoints

- GET /health
  - Returns: {"status": "ok"}
- GET /status
  - Returns: {"online": bool, "server_running": bool, "players": int, "max_players": int | null, "name": str | null}
  - Optional debug fields: docker_error, container_state, checked_at

## Local run (Docker)

```
docker build -t nwn-status-backend ./status_backend
docker run -p 8080:8080 \
  -e NWN_CONTAINER_NAME=nwn-ee-pw \
  -e DOCKER_SOCK=/var/run/docker.sock \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  nwn-status-backend
```
