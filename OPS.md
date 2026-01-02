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
- One firewall rule allowing SSH (tcp:22) and the NWN port (tcp/udp:5121)

Basic workflow:

```
cd terraform
terraform init
terraform plan
terraform apply
```

## Production operations (GCP VM)

Start/stop the VM from your local machine:

```
gcloud compute instances start nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
gcloud compute instances stop nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
```

The container runs as `nwn-ee-pw` with `restart: unless-stopped` in `ops/docker-compose.prod.yml`.

To update the server image or restart the container, SSH in and run:

```
gcloud compute ssh nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
cd /opt/neverwinter-project
sudo docker compose -f ops/docker-compose.prod.yml pull
sudo docker compose -f ops/docker-compose.prod.yml up -d
```

To stop the server container:

```
sudo docker compose -f ops/docker-compose.prod.yml down
```

## Ephemeral external IP (important)

The VM uses an ephemeral external IP, which changes on each stop/start. This avoids the cost of a reserved static IP, but you must re-check the IP before connecting.

Get the current external IP:

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
gcloud compute ssh nwn-pw-vm --project=nwn-pw --zone=southamerica-east1-a
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
