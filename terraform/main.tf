provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

variable "project_id" {
  type        = string
  default     = "wildfire-detection-495521"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "machine_type" {
  type    = string
  default = "e2-highcpu-8" # 4 cores, 8GB RAM
}

resource "google_service_account" "vm_sa" {
  account_id   = "wildfire-deploy-sa"
  display_name = "Service Account for Wildfire VM"
}

resource "google_project_iam_member" "sa_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

resource "google_compute_instance" "k8s_master" {
  name         = "k8s-master"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["k8s-node", "k8s-master"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 30
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

  metadata_startup_script = file("${path.module}/scripts/k8s-setup.sh")
}

resource "google_compute_instance" "k8s_worker" {
  count        = 2
  name         = "k8s-worker-${count.index}"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["k8s-node", "k8s-worker"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 30
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

  metadata_startup_script = file("${path.module}/scripts/k8s-setup.sh")
}

resource "google_compute_firewall" "allow_k8s_internal" {
  name    = "allow-k8s-internal"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }

  source_tags = ["k8s-node"]
  target_tags = ["k8s-node"]
}

resource "google_compute_firewall" "allow_k8s_control_plane" {
  name    = "allow-k8s-control-plane"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["6443", "2379-2380", "10250", "10257", "10259"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-master"]
}

resource "google_compute_firewall" "allow_app_traffic" {
  name    = "allow-app-traffic"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "30080"] # Specific NodePort
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}

output "master_ip" {
  value = google_compute_instance.k8s_master.network_interface[0].access_config[0].nat_ip
}

output "worker_ips" {
  value = google_compute_instance.k8s_worker[*].network_interface[0].access_config[0].nat_ip
}
