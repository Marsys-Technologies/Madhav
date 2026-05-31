// Cloud Scheduler + Service Account for the build reaper cron job.
// Invokes POST /api/build/reap every 15 min with OIDC auth.
// Brief: CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md §L3.4
//
// Variables amjis_web_url / gcp_project / gcp_region declared in main.tf.

resource "google_service_account" "build_reaper" {
  account_id   = "build-reaper"
  display_name = "Build Reaper (Cloud Scheduler invoker)"
  project      = var.gcp_project
}

resource "google_cloud_scheduler_job" "build_reaper" {
  name             = "build-reaper"
  description      = "Reaps stale builds every 15 min. See BRIEF BUILD_TIMEOUT_HARDENING_v1_0."
  schedule         = "*/15 * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "120s"
  region           = var.gcp_region

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/build/reap"

    oidc_token {
      service_account_email = google_service_account.build_reaper.email
      audience              = var.amjis_web_url
    }
  }
}
