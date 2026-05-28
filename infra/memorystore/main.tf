// MARSYS-JIS Platform Modernization — Wave 4 unit 4.memorystore_caching
// Provisions a Memorystore Redis instance (Basic tier, 1GB) in asia-south1
// for the amjis-web + amjis-mcp shared cache layer.
//
// IaC only — apply runs via the zero-touch deploy pipeline (or manual
// `terraform apply` from the project root). DO NOT run apply from this
// worktree.
//
// Outputs REDIS_HOST + REDIS_PORT consumed by .github/workflows/deploy.yml.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

variable "gcp_project" {
  type        = string
  description = "GCP project ID (madhav-astrology)"
  default     = "madhav-astrology"
}

variable "gcp_region" {
  type        = string
  description = "Region — must match Cloud Run services"
  default     = "asia-south1"
}

variable "redis_instance_id" {
  type        = string
  description = "Memorystore instance identifier"
  default     = "amjis-cache"
}

variable "redis_tier" {
  type        = string
  description = "BASIC (no HA, dev/staging) or STANDARD_HA"
  default     = "BASIC"
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Initial size; can be resized in-place without downtime."
  default     = 1
}

variable "vpc_network" {
  type        = string
  description = "Authorised VPC network (the same one Cloud Run egresses through)"
  default     = "projects/madhav-astrology/global/networks/default"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

resource "google_redis_instance" "amjis_cache" {
  name           = var.redis_instance_id
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.gcp_region
  redis_version  = "REDIS_7_2"
  display_name   = "MARSYS-JIS shared cache (retrieval bundles, planner, embeddings)"

  authorized_network = var.vpc_network
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  // Eviction policy — LRU is fine for a cache (we never use Redis as source of truth).
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  labels = {
    component = "amjis-shared-cache"
    managed-by = "terraform"
    workstream = "platform-modernization-wave4"
  }
}

output "redis_host" {
  value       = google_redis_instance.amjis_cache.host
  description = "Internal IP — set as REDIS_HOST env var on Cloud Run services."
}

output "redis_port" {
  value       = google_redis_instance.amjis_cache.port
  description = "Redis port (typically 6379) — set as REDIS_PORT env var."
}

output "redis_current_location_id" {
  value = google_redis_instance.amjis_cache.current_location_id
}
