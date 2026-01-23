# Architecture

```
Developer
  |  push/tag
  v
GitHub repo
  |  CI build
  v
GitHub Actions (build)
  |  push images
  v
GHCR

Tag release
  |  deploy (WIF + IAP SSH)
  v
GitHub Actions (deploy)
  |  scp compose + remote docker compose
  v
GCE VM
  |  docker compose
  v
+------------------+    +--------------------+
| nwn-ee-pw        |    | nwn-status         |
| NWN:EE server    |    | FastAPI status API |
+------------------+    +--------------------+

Boot-time convergence:
- VM startup script checks out latest vX.Y.Z tag and runs
  docker compose pull (non-fatal) + up -d
```

## Components

- `nwn-ee-pw`: NWN:EE dedicated server container
- `nwn-status`: FastAPI status API (container-truth online/offline)
- `servervault/`, `database/`, `logs/`: persistence and logs
- Ports: 5121 TCP/UDP (game), 8080 TCP (status API)
- Security: SSH via IAP only; firewall open only for game/status
