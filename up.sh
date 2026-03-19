#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/terraform"

terraform apply -auto-approve

echo "VM external IP:"
gcloud compute instances describe nwn-pw-vm \
  --project nwn-pw \
  --zone southamerica-east1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
