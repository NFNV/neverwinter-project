terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_firewall" "nwn_pw_5121" {
  name    = "nwn-pw-ports"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5121"]
  }

  allow {
    protocol = "udp"
    ports    = ["5121"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["nwn-pw"]
}

resource "google_compute_instance" "nwn_pw_vm" {
  name         = "nwn-pw-vm"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["nwn-pw"]

  boot_disk {
    initialize_params {
      image = "projects/debian-cloud/global/images/family/debian-12"
      size  = var.boot_disk_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"

    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/usr/bin/env bash
    set -euxo pipefail

    apt-get update -y
    apt-get install -y docker.io docker-compose-plugin git

    if [ ! -d "/opt/neverwinter-project" ]; then
      git clone https://github.com/NFNV/neverwinter-project.git /opt/neverwinter-project
    fi

    cd /opt/neverwinter-project

    mkdir -p servervault database logs

    docker compose -f ops/docker-compose.yml pull || true
    docker compose -f ops/docker-compose.yml up -d
  EOT

  labels = {
    game  = "nwn"
    env   = "demo"
    owner = "nv"
  }
}

output "nwn_pw_vm_name" {
  description = "Name of the NWN PW VM"
  value       = google_compute_instance.nwn_pw_vm.name
}

output "nwn_pw_external_ip" {
  description = "External IP for NWN:EE client connections"
  value       = google_compute_instance.nwn_pw_vm.network_interface[0].access_config[0].nat_ip
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "GCE machine type"
  type        = string
  default     = "e2-small"
}

variable "boot_disk_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}