// Cloud Scheduler module — build reaper cron + supporting IAM.
// Applied via deploy.yml on every main-branch push.

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

// Allow build-reaper SA to invoke the amjis-web Cloud Run service.
resource "google_cloud_run_v2_service_iam_member" "reaper_invokes_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.build_reaper.email}"
}
