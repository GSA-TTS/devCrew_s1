# Example GCP Terraform Configuration
# Issue #38: Infrastructure as Code Platform

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # GCS backend for remote state
  backend "gcs" {
    bucket = "terraform-state-bucket"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
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

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "machine_type" {
  description = "Machine type"
  type        = string
  default     = "f1-micro"
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.environment}-vpc"
  auto_create_subnetworks = false
  mtu                     = 1460

  lifecycle {
    prevent_destroy = false
  }
}

# Public Subnet
resource "google_compute_subnetwork" "public" {
  name          = "${var.environment}-public-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.main.id

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Private Subnet
resource "google_compute_subnetwork" "private" {
  name          = "${var.environment}-private-subnet"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.main.id

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Firewall Rule - Allow HTTP
resource "google_compute_firewall" "allow_http" {
  name    = "${var.environment}-allow-http"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]
}

# Firewall Rule - Allow HTTPS
resource "google_compute_firewall" "allow_https" {
  name    = "${var.environment}-allow-https"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]
}

# Firewall Rule - Allow SSH
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.environment}-allow-ssh"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]  # Should be restricted in production
  target_tags   = ["web"]
}

# External IP Address
resource "google_compute_address" "web" {
  name   = "${var.environment}-web-ip"
  region = var.region
}

# Compute Instance
resource "google_compute_instance" "web" {
  name         = "${var.environment}-web-instance"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["web"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20
      type  = "pd-standard"
    }
  }

  # Additional data disk
  attached_disk {
    source = google_compute_disk.data.id
  }

  network_interface {
    network    = google_compute_network.main.name
    subnetwork = google_compute_subnetwork.public.name

    access_config {
      nat_ip = google_compute_address.web.address
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
    echo "<h1>Hello from Terraform on GCP</h1>" > /var/www/html/index.html
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    project     = "iac-platform"
  }
}

# Persistent Disk
resource "google_compute_disk" "data" {
  name = "${var.environment}-data-disk"
  type = "pd-standard"
  zone = var.zone
  size = 10

  labels = {
    environment = var.environment
  }
}

# Cloud Storage Bucket
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-${var.environment}-data-${random_id.bucket_suffix.hex}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = null
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Cloud Storage Bucket IAM - Block public access
resource "google_storage_bucket_iam_binding" "prevent_public_access" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.admin"

  members = [
    "projectEditor:${var.project_id}",
    "projectOwner:${var.project_id}",
  ]
}

# Random ID for unique bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Cloud NAT for private instances
resource "google_compute_router" "main" {
  name    = "${var.environment}-router"
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "main" {
  name                               = "${var.environment}-nat"
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Outputs
output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.main.name
}

output "public_subnet_name" {
  description = "Public subnet name"
  value       = google_compute_subnetwork.public.name
}

output "instance_name" {
  description = "Compute instance name"
  value       = google_compute_instance.web.name
}

output "instance_external_ip" {
  description = "Instance external IP"
  value       = google_compute_address.web.address
}

output "storage_bucket_name" {
  description = "Storage bucket name"
  value       = google_storage_bucket.data.name
}

output "storage_bucket_url" {
  description = "Storage bucket URL"
  value       = google_storage_bucket.data.url
}
