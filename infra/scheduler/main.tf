// MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene
//
// Cloud Scheduler jobs (IaC):
//   amjis-mv-refresh             — every 6h, refreshes materialized views.
//   amjis-pending-stream-reaper  — every 10m, fails orphaned pending streams.
//   amjis-nirmana-elevation-monitor — every 5m, records NTAP program observations.

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

data "google_project" "scheduler" {
  project_id = var.gcp_project
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

// ── Job: Nirmana elevation monitor (every 5 minutes UTC) ────────────────────

// This identity is intentionally dedicated to the monitor. It may invoke only
// amjis-web; the legacy scheduler_invoker_sa remains unchanged for existing jobs.
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

// Cloud Scheduler's Google-managed service agent mints only the job's OIDC token.
// Scope that OIDC-only role to this one dedicated service account.
resource "google_service_account_iam_member" "cloud_scheduler_mints_nirmana_monitor_oidc" {
  service_account_id = google_service_account.nirmana_elevation_monitor.name
  role               = "roles/iam.serviceAccountOpenIdTokenCreator"
  member             = "serviceAccount:service-${data.google_project.scheduler.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
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
      # x-marsys-cron-secret is deliberately not stored in Terraform or state.
      # After protected-main apply, configure the existing MARSYS_CRON_SECRET as
      # the X-Marsys-Cron-Secret header using the established Scheduler secret-
      # header procedure. It must not use Authorization: OIDC occupies that
      # header on Cloud Scheduler's Cloud Run dispatch.
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.nirmana_elevation_monitor.email
      audience              = var.amjis_web_url
    }
  }

  // The secret header is configured outside Terraform after protected-main
  // apply. Ignore only the target header map so future plans do not remove it.
  lifecycle {
    ignore_changes = [http_target[0].headers]
  }
}

output "scheduler_jobs" {
  value = [
    google_cloud_scheduler_job.mv_refresh.name,
    google_cloud_scheduler_job.pending_stream_reaper.name,
    google_cloud_scheduler_job.nirmana_elevation_monitor.name,
  ]
}
