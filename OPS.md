# Operations Runbook

## Overview

This repo hosts a Neverwinter Nights: Enhanced Edition persistent world. The module is `NV_PW_Seed`, packaged into a custom Docker image built from `nwnxee/unified:latest`. The image is published to GHCR and deployed on a GCP VM named `nwn-pw-vm` in the `nwn-pw` project.

## Local development (Docker)

Build the image:

```
docker build -t nwn-ee-pw:local -f ops/Dockerfile .
```

Start the server:

```
docker compose -f ops/docker-compose.yml up -d
```

Stop the server:

```
docker compose -f ops/docker-compose.yml down
```

## Cloud infrastructure (GCP + Terraform)

Terraform in `terraform/` creates:
- `nwn-pw-vm` (GCE VM)
- Firewall rules for game/status traffic and IAP-only SSH

Basic workflow:

```
cd terraform
terraform init
terraform plan
terraform apply
```

## Production operations (GCP VM)

### Get current external IP

```
gcloud compute instances describe nwn-pw-vm \
  --project=nwn-pw \
  --zone=southamerica-east1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Start/stop the VM from your local machine:

```
gcloud compute instances start nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
gcloud compute instances stop nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
```

The container runs as `nwn-ee-pw` with `restart: unless-stopped` in `ops/docker-compose.prod.yml`.

To update the server image or restart the container, SSH in and run:

```
gcloud compute ssh nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a --tunnel-through-iap
cd /opt/neverwinter-project
sudo docker compose -f ops/docker-compose.prod.yml pull
sudo docker compose -f ops/docker-compose.prod.yml up -d
```

To stop the server container:

```
sudo docker compose -f ops/docker-compose.prod.yml down
```

## Automation

Boot-time automation: each VM boot checks out the latest prod tag (`vX.Y.Z`) and runs `docker compose pull` and `docker compose up -d` using `/opt/neverwinter-project/ops/docker-compose.prod.yml`. If GHCR is temporarily unavailable, it continues with cached images.

Release automation: tagging `vX.Y.Z` triggers CI build+push and a CD deploy that updates the VM (when it is online). If the VM is offline during a release, it will update on the next boot via the startup script.

### CI/CD credentials (WIF)

Deploy uses Workload Identity Federation (OIDC) from GitHub Actions; no JSON key files.

Required secrets/vars:
- `GCP_PROJECT_ID`
- `GCP_ZONE`
- `GCP_INSTANCE`
- `WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL`

Ensure `iamcredentials.googleapis.com` is enabled for impersonation.

## Deploy a release

```
git tag vX.Y.Z
git push origin vX.Y.Z
```

Then verify the deploy job succeeded in GitHub Actions and confirm on the VM:

```
gcloud compute ssh nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a --tunnel-through-iap
sudo docker ps
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/status
```

## Rollback

Rollback by redeploying the previous tag (vX.Y.Z-1). If the tag already exists, re-run the workflow in GitHub Actions or re-push the tag.

Verify the running image digest on the VM:

```
sudo docker inspect --format='{{.Image}}' nwn-ee-pw
sudo docker image inspect --format='{{index .RepoDigests 0}}' ghcr.io/nfnv/neverwinter-project:prod-latest
```

## Debug quick commands

```
sudo docker compose -f ops/docker-compose.prod.yml ps
sudo docker logs --tail=120 nwn-ee-pw
ss -tuln
ss -uapn
```

### Status backend

The `nwn-status` service runs on the same VM and exposes `GET /status` on port 8080.

Example:

```
curl http://<VM_EXTERNAL_IP>:8080/status
```

## Ephemeral external IP (important)

The VM uses an ephemeral external IP, which changes on each stop/start. This avoids the cost of a reserved static IP, but you must retrieve the current IP before connecting.

Get the current external IP with:

```
gcloud compute instances describe nwn-pw-vm \
  --project=nwn-pw \
  --zone=southamerica-east1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Static IP tradeoff: stable address for players, but a small cost even when the VM is stopped.

## Useful commands (cheat sheet)

Start VM:

```
gcloud compute instances start nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
```

Stop VM:

```
gcloud compute instances stop nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
```

Get external IP:

```
gcloud compute instances describe nwn-pw-vm \
  --project=nwn-pw \
  --zone=southamerica-east1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

SSH to VM:

```
gcloud compute ssh nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a --tunnel-through-iap
```

Pull and start server:

```
sudo docker compose -f ops/docker-compose.prod.yml pull
sudo docker compose -f ops/docker-compose.prod.yml up -d
```

Stop server:

```
sudo docker compose -f ops/docker-compose.prod.yml down
```

Tail server logs:

```
sudo docker logs --tail=80 nwn-ee-pw
```
SSH access is now IAP-only (port 22 allowed from `35.235.240.0/20`). You must have the IAP-Secured Tunnel User role to connect.

## Known limitations

- External IP is ephemeral (no static IP for this practice project).
- Status endpoint reports container-truth, not UDP query results.
