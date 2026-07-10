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
    # R6 0a-envauth (O-2): corrected from /api/cron/reap_pending_streams, which does
    # not exist in the repo (404) — the route has always lived at
    # /api/admin/cron/reap-pending-streams (platform/src/app/api/admin/cron/reap-pending-streams/route.ts,
    # introduced #33). This target URI was stale from this file's original authoring
    # and never matched the actual route path.
    uri = "${var.amjis_web_url}/api/admin/cron/reap-pending-streams"
    headers = {
      "Content-Type" = "application/json"
      # x-marsys-cron-secret (NOT set here in plaintext — provision via
      # `gcloud scheduler jobs update http amjis-pending-stream-reaper
      # --update-headers="x-marsys-cron-secret=<secret>"` post-apply, reusing the
      # same mcpt-scheduler-secret value already live in Secret Manager). R5.2 A4
      # finding (bbee27c3, applied here per O-2): this job's route-side
      # Authorization-header shared-secret check collided with the oidc_token
      # block below — Cloud Scheduler's OIDC identity token is ALSO delivered via
      # the Authorization header, so the app-level check (`Authorization ===
      # "Bearer <MARSYS_CRON_SECRET>"`) could never match a live OIDC JWT and
      # 401'd on every run (this is the pre-existing sibling-job silent failure
      # bbee27c3's commit message flagged but explicitly did not fix — fixed
      # here). Moved the app-level shared-secret check to this dedicated header,
      # mirroring the already-proven x-watchdog-auth / x-marsys-cron-secret
      # convention — it does not collide with Cloud Run's own OIDC-in-Authorization
      # mechanism, so the IAM-level oidc_token gate and the app-level secret
      # check now coexist correctly, same as panchanga_refresh.tf / canary_battery.tf.
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
