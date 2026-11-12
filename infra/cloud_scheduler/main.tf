// Retired build-reaper definitions for the verified default deployment.
// Backend/provider declarations are retained for history; apply.sh refuses all operations.
// Alternate projects, regions and backends require a separate state disposition.

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
  type    = string
  default = "madhav-astrology"
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"
}

variable "amjis_web_url" {
  type    = string
  default = "https://amjis-web-938361928218.asia-south1.run.app"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}
