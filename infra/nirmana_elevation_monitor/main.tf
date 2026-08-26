// Nirmana elevation monitor — isolated Terraform root.
//
// This root deliberately owns only the monitor's four resources. It must not
// share state with infra/scheduler, whose state manages unrelated Scheduler jobs.

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
  type        = string
  description = "Fully-qualified amjis-web Cloud Run URL (no trailing slash)."
  default     = "https://amjis-web-938361928218.asia-south1.run.app"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

data "google_project" "nirmana_elevation_monitor" {
  project_id = var.gcp_project
}

// This identity is dedicated to the monitor and can invoke only amjis-web.
resource "google_service_account" "nirmana_elevation_monitor" {
  account_id   = "amjis-nirmana-monitor"
  display_name = "Nirmana elevation monitor Scheduler invoker"
  description  = "Dedicated Cloud Scheduler OIDC identity for the read-only Nirmana elevation monitor."
  project      = var.gcp_project
}

resource "google_cloud_run_v2_service_iam_member" "nirmana_elevation_monitor_invokes_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.nirmana_elevation_monitor.email}"
}

// Cloud Scheduler's Google-managed service agent mints only this job's OIDC token.
resource "google_service_account_iam_member" "cloud_scheduler_mints_nirmana_monitor_oidc" {
  service_account_id = google_service_account.nirmana_elevation_monitor.name
  role               = "roles/iam.serviceAccountOpenIdTokenCreator"
  member             = "serviceAccount:service-${data.google_project.nirmana_elevation_monitor.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}

resource "google_cloud_scheduler_job" "nirmana_elevation_monitor" {
  name             = "amjis-nirmana-elevation-monitor"
  description      = "Record a read-only Nirmana elevation program-monitor observation every five minutes."
  schedule         = "*/5 * * * *"
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "120s"

  retry_config {
    retry_count          = 2
    min_backoff_duration = "30s"
    max_backoff_duration = "120s"
    max_doublings        = 2
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/admin/internal/nirmana-elevation-monitor"
    headers = {
      "Content-Type" = "application/json"
      # The MARSYS_CRON_SECRET custom header is configured outside Terraform.
      # Do not use Authorization: Cloud Scheduler uses that header for OIDC.
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.nirmana_elevation_monitor.email
      audience              = var.amjis_web_url
    }
  }

  // Preserve the custom secret header installed by an approved operator.
  lifecycle {
    ignore_changes = [http_target[0].headers]
  }
}

output "nirmana_elevation_monitor_job" {
  value = google_cloud_scheduler_job.nirmana_elevation_monitor.name
}
