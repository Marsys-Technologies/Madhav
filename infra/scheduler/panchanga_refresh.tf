// R5.1 C3 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md) — Forward Panchanga.
//
// Cloud Scheduler job (IaC):
//   panchanga-daily-refresh   — monthly, refreshes the panchanga_daily rolling
//                               +12-month window via panchanga_daily_writer.py.
//
// NOT YET APPLIED. Authored in an isolated worktree per this repo's IaC discipline
// (see infra/scheduler/README.md "Apply discipline: IaC only. Apply runs on main;
// never from a worktree."). Flagged for the conductor to `terraform apply` from
// main post-merge. Until applied, panchanga_daily stays fresh only via the manual
// `python scripts/panchanga_daily_writer.py` run already performed to seed real
// data for R5.1 C3 acceptance (see R5_1_RUN_LEDGER_v1_0.md) — the rolling window
// will silently go stale after ~12 months without this job (or a manual re-run).
//
// Mirrors the exact pattern established in infra/scheduler/main.tf (mv_refresh /
// pending_stream_reaper): same variables, same provider, same OIDC auth model.
// Declared in a separate file (not appended to main.tf) to keep this addition
// surgical and independently reviewable/applicable.

resource "google_cloud_scheduler_job" "panchanga_daily_refresh" {
  name             = "panchanga-daily-refresh"
  description      = "R5.1 C3 — refresh panchanga_daily rolling +12-month window (panchanga_daily_writer.py via /api/admin/cron/refresh-panchanga-daily)."
  schedule         = "0 3 1 * *" // 03:00 UTC on the 1st of every month
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "300s" // writer computes ~366 days of panchang_engine.compute_panchang() calls

  retry_config {
    retry_count          = 2
    min_backoff_duration = "60s"
    max_backoff_duration = "600s"
    max_doublings        = 2
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/admin/cron/refresh-panchanga-daily"
    headers = {
      "Content-Type" = "application/json"
      // Authorization (Bearer MARSYS_CRON_SECRET) is NOT set here in plaintext —
      // provision via `gcloud scheduler jobs update http panchanga-daily-refresh
      // --update-headers="Authorization=Bearer <secret>"` post-apply, or wire a
      // Secret Manager-backed header once this repo's scheduler jobs adopt one
      // (the sibling reap-pending-streams job has the same open gap today).
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = var.scheduler_invoker_sa
      audience              = var.amjis_web_url
    }
  }
}

output "panchanga_refresh_scheduler_job" {
  value = google_cloud_scheduler_job.panchanga_daily_refresh.name
}
