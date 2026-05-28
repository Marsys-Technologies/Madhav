// MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene
//
// Cloud Scheduler jobs (IaC):
//   amjis-mv-refresh             — every 6h, refreshes materialized views.
//   amjis-pending-stream-reaper  — every 10m, fails orphaned pending streams.

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

variable "scheduler_invoker_sa" {
  type        = string
  description = "Service account that signs OIDC tokens for the scheduler → Cloud Run hop. Must hold roles/run.invoker on amjis-web."
  default     = "amjis-builder-runtime@madhav-astrology.iam.gserviceaccount.com"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

// ── Job: MV refresh (every 6 hours UTC) ──────────────────────────────────────

resource "google_cloud_scheduler_job" "mv_refresh" {
  name             = "amjis-mv-refresh"
  description      = "Refresh materialized views (school_convergence_index + others). Wave 4 4.edge_and_infra_hygiene."
  schedule         = "0 */6 * * *"
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "320s"

  retry_config {
    retry_count          = 2
    min_backoff_duration = "30s"
    max_backoff_duration = "300s"
    max_doublings        = 2
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/cron/refresh_materialized_views"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = var.scheduler_invoker_sa
      audience              = var.amjis_web_url
    }
  }
}

// ── Job: Pending-stream reaper (every 10 minutes UTC) ────────────────────────

resource "google_cloud_scheduler_job" "pending_stream_reaper" {
  name             = "amjis-pending-stream-reaper"
  description      = "Mark orphaned pending-state stream rows as failed after timeout. Wave 4 4.edge_and_infra_hygiene."
  schedule         = "*/10 * * * *"
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "120s"

  retry_config {
    retry_count          = 1
    min_backoff_duration = "10s"
    max_backoff_duration = "60s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/cron/reap_pending_streams"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = var.scheduler_invoker_sa
      audience              = var.amjis_web_url
    }
  }
}

output "scheduler_jobs" {
  value = [
    google_cloud_scheduler_job.mv_refresh.name,
    google_cloud_scheduler_job.pending_stream_reaper.name,
  ]
}
