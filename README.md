# Neverwinter Nights: EE Persistent World – Docker + GCP

This repository contains a small **Neverwinter Nights: Enhanced Edition (NWN:EE) persistent world** server.  
The server is packaged as a Docker image (published to GHCR) and can run both locally and on a Google Cloud VM.

The focus is on:

- Custom NWN:EE content (module, NPCs, persistence).
- Containerized dedicated server.
- Simple CI → image registry → VM deployment flow.

---

## Overview

**Components**

- **Module**: `module/NV_PW_Seed.mod` – custom area, banker NPC, persistent chest, vendor, server vault enabled.
- **Docker image**: built from `nwnxee/unified:latest` with the module baked into `/nwn/run/modules/`.
- **Registry**: GitHub Container Registry (GHCR) – `ghcr.io/nfnv/neverwinter-project:<tag>`.
- **Infra**: Terraform-managed GCE VM (Debian, `e2-small`) in `southamerica-east1-a`, with a startup script that runs the server via Docker Compose.

**Repository layout**

```text
module/                     # NWN:EE module (.mod)
ops/
  Dockerfile                # Builds NWN server image from nwnxee/unified
  docker-compose.yml        # Local compose
  docker-compose.prod.yml   # Prod compose (GHCR image, GCP VM)
terraform/
  main.tf                   # Firewall, VM, startup script
.github/workflows/
  docker-image.yml          # GHCR build & push

---

  # Running Locally (Docker)
