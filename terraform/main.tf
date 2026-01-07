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

resource "google_compute_firewall" "nwn_pw_ssh_iap" {
  name    = "nwn-pw-ssh-iap"
  network = "default"

  direction = "INGRESS"
  priority  = 1000

  source_ranges = ["35.235.240.0/20"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags = ["nwn-pw"]
}

resource "google_compute_firewall" "nwn_pw_game" {
  name    = "nwn-pw-game"
  network = "default"

  direction = "INGRESS"
  priority  = 1000

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["5121", "8080"]
  }

  allow {
    protocol = "udp"
    ports    = ["5121"]
  }

  target_tags = ["nwn-pw"]
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

  metadata = {
    "startup-script" = file("${path.module}/startup.sh")
  }

  lifecycle {
    ignore_changes = [
      metadata_startup_script,
    ]
  }

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

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "southamerica-east1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "southamerica-east1-a"
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
