# NWN:EE PW Seed

Small persistent-world seed for Neverwinter Nights: Enhanced Edition:
- Outdoor camp with persistent chest (Campaign DB), banker (per-player balance), vendor.
- Server-vault character persistence (inventory & gold).
- Containerized server with mounted volumes for `/servervault` and `/database`.

## Run locally (Docker)
Requirements: Docker Desktop.

```bash
docker compose -f ops/docker-compose.yml up -d
# connect from client: Multiplayer → Direct Connect → 127.0.0.1:5121
```
