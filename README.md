# Neverwinter Nights: EE Persistent World (Docker + GCP)

A small Neverwinter Nights: Enhanced Edition persistent world server, packaged as a Docker image and deployed to Google Cloud. The goal is a compact but real-world infra project: custom NWN content, containerized server, CI to GHCR, and a VM running the image.

## What this project demonstrates

- CI/CD with tagged releases and GHCR images
- Infrastructure as code (Terraform) for GCE
- Secure deploys using WIF + IAP (no SSH to the world)
- Boot-time convergence via VM startup script (pull/up on every boot)
- Container-truth health via a lightweight status backend

## Docs

- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Operations: [OPS.md](OPS.md)
- Postmortem: [UDP status false offline](postmortems/2026-01-udp-status-false-offline.md)

## What this includes

- Custom module: `module/NV_PW_Seed.mod`
  - Small outdoor camp starting area.
  - Banker NPC with persistent gold storage.
  - Vendor NPC with shop inventory.
  - Persistent camp chest.
  - Server vault enabled for character persistence.
- Docker image built from `nwnxee/unified:latest`.
- GitHub Actions workflow to build/push to GHCR.
- Terraform to provision a GCE VM and firewall rules.

## Repository layout

```
module/                     # NWN:EE module (.mod)
ops/
  Dockerfile                # Builds NWN server image from nwnxee/unified
  docker-compose.yml        # Local compose
  docker-compose.prod.yml   # Prod compose (GHCR image, GCP VM)
terraform/
  main.tf                   # Firewall, VM, startup script
.github/workflows/
  docker-image.yml          # GHCR build & push
```

## Requirements

- Docker and Docker Compose (local)
- NWN:EE client for testing
- Terraform + GCP account (production)

## Local development

### 1) Build the local image

```
docker build -t nwn-ee-pw:local -f ops/Dockerfile .
```

### 2) Start the server

```
docker compose -f ops/docker-compose.yml up -d
```

### 3) Connect from your client

- Direct Connect to `<your-mac-ip>:5121`
- TCP and UDP 5121 are exposed for local testing.

### 4) Logs

```
docker logs --tail=80 nwn-ee-pw
```

## Updating the module

1. Edit the module in the Aurora Toolset.
2. Export to `module/NV_PW_Seed.mod`.
3. Rebuild the image and restart the container.

```
docker build -t nwn-ee-pw:local -f ops/Dockerfile .
docker compose -f ops/docker-compose.yml up -d
```

## CI/CD (GHCR)

Workflow: `.github/workflows/docker-image.yml`

### Release model

- `master` pushes build `ghcr.io/nfnv/neverwinter-project:staging-latest`
- Tags `vX.Y.Z` push both:
  - `ghcr.io/nfnv/neverwinter-project:vX.Y.Z`
  - `ghcr.io/nfnv/neverwinter-project:prod-latest`

### GCP credentials (WIF)

Deploy uses Workload Identity Federation (OIDC) from GitHub Actions; no JSON key files.

Required secrets/vars:
- `GCP_PROJECT_ID`
- `GCP_ZONE`
- `GCP_INSTANCE`
- `WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL`

Ensure `iamcredentials.googleapis.com` is enabled for impersonation.

## Production (GCP)

Terraform: `terraform/main.tf`

Creates:
- A Debian VM (`e2-small`) in `southamerica-east1-a`.
- Firewall rule opening TCP/UDP 5121.
- Startup script that installs Docker, clones the repo, and runs the prod compose.

### Apply Terraform

```
cd terraform
terraform init
terraform apply
```

### Start the server on the VM

The startup script already runs the server, but you can manually refresh it:

```
cd /opt/neverwinter-project
sudo docker compose -f ops/docker-compose.prod.yml pull
sudo docker compose -f ops/docker-compose.prod.yml up -d
```

### Get the external IP

```
gcloud compute instances describe nwn-pw-vm \
  --project <project-id> \
  --zone southamerica-east1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### Connect

Direct Connect to `<external-ip>:5121` from NWN:EE.

### How to verify it's running

On the VM:

```
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/status
```

## Security & SSH access

SSH uses IAP tunneling:

```
gcloud compute ssh nwn-pw-vm \
  --project=nwn-pw \
  --zone=southamerica-east1-a \
  --tunnel-through-iap
```

Terraform configures two firewall rules:
- `nwn-pw-ssh-iap`: allows tcp:22 only from the IAP proxy range `35.235.240.0/20` (no direct public SSH).
- `nwn-pw-game`: allows tcp/udp:5121 from `0.0.0.0/0` so players can connect.

This keeps the game port open for players while limiting SSH to authenticated IAP users.

## Notes on monitoring

NWN uses UDP for gameplay. A generic TCP probe on port 5121 can show "offline" even when the server is healthy. Use:
- Actual client connection.
- Server logs.

## Troubleshooting

- If the server is running but you cannot connect, check:
  - VM firewall rules (TCP/UDP 5121).
  - VM external IP.
  - Container logs: `docker logs --tail=80 nwn-ee-pw`.
- If you see an image pull error, ensure GHCR auth and correct tag.
