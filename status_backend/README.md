# NWN Status Backend

Lightweight FastAPI service that queries a Neverwinter Nights: Enhanced Edition server over UDP and exposes health and status endpoints.

## Environment variables

- NWN_HOST: hostname or container name for the NWN server (default: nwn-ee-pw)
- NWN_PORT: UDP port for the NWN server (default: 5121)

## Endpoints

- GET /health
  - Returns: {"status": "ok"}
- GET /status
  - Returns: {"online": bool, "players": int, "max_players": int | null, "name": str | null}

## Local run (Docker)

```
docker build -t nwn-status-backend ./status_backend
docker run -p 8080:8080 -e NWN_HOST=localhost -e NWN_PORT=5121 nwn-status-backend
```
