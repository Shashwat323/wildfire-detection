provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Variable for Project ID
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default = "wildfire-detection-495518"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

# Define the existing bucket name as a variable for easy management
variable "bucket" {
  type    = string
  default = "wildfire-detection-bucket"
}

# 1. Service Account for the VM
resource "google_service_account" "vm_sa" {
  account_id   = "wildfire-deploy-sa"
  display_name = "Service Account for Wildfire VM"
}

# 2. IAM Policy: Allow the VM to read from the EXISTING bucket
resource "google_project_iam_member" "bucket_reader" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

# 3. Firewall Rule (Port 8000)
resource "google_compute_firewall" "allow_http_8000" {
  name    = "allow-http-8000"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["wildfire-app"]
}

# 4. Compute Instance
resource "google_compute_instance" "app_server" {
  name         = "wildfire-app-server"
  machine_type = "e2-highcpu-8"
  zone         = var.zone
  tags         = ["wildfire-app"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {} 
  }

  service_account {
    email  = google_service_account.vm_sa.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e

    # Install Docker
    apt-get update
    apt-get install -y docker.io

    mkdir -p /app
    cd /app

    # Wait for metadata service
    sleep 10

    # Download project files from the EXISTING bucket
    gcloud storage cp gs://${var.bucket}/main.py .
    gcloud storage cp gs://${var.bucket}/Dockerfile .
    gcloud storage cp gs://${var.bucket}/requirements.txt .
    
    mkdir -p fire-models
    gcloud storage cp gs://${var.bucket}/fire-models/fire_m.pt fire-models/

    # Build and Run
    docker build -t wildfire-app .
    docker run -d --name wildfire-api -p 8000:8000 wildfire-app
  EOT
}

output "external_ip" {
  value = google_compute_instance.app_server.network_interface[0].access_config[0].nat_ip
}
