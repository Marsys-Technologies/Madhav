// R5.1 C5.2 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md) — Canary battery scheduled job.
//
// Cloud Scheduler job (IaC):
//   canary-battery-daily   — daily, runs the P1-P8 canary probe set against prod
//                            amjis-mcp for both canonical charts and feeds results
//                            into system_health (migration 366), alerting on
//                            regression via the existing mcp_alerts_config path.
//
// NOT YET APPLIED. Authored in an isolated worktree per this repo's IaC discipline
// (see infra/scheduler/README.md "Apply discipline: IaC only. Apply runs on main;
// never from a worktree."). Flagged for the conductor to `terraform apply` from
// main post-merge — same pattern as C3's panchanga_refresh.tf.
//
// PREREQUISITE (must happen before this job will succeed, and before applying):
// The target route (platform/src/app/api/admin/cron/run-canary-battery/route.ts)
// requires an MCP_CANARY_KEY env var — the read-only probe-service-account test
// credential provisioned in R5 W0a (00_ARCHITECTURE/R5_RUN_LEDGER_v1_0.md P0-iii,
// key_id=mcp_prod_tDO7obNw). It is NOT currently wired into the amjis-web Cloud Run
// service. Conductor steps, in order:
//   1. Create the Secret Manager secret (value = the full_key recorded in
//      R5_RUN_LEDGER_v1_0.md P0-iii — do not re-paste it into any new file):
//        gcloud secrets create mcp-canary-key --replication-policy=automatic
//        printf '%s' "<full_key from the ledger>" | gcloud secrets versions add mcp-canary-key --data-file=-
//   2. Grant the amjis-web runtime SA access:
//        gcloud secrets add-iam-policy-binding mcp-canary-key \
//          --member="serviceAccount:amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com" \
//          --role="roles/secretmanager.secretAccessor"
//   3. .github/workflows/deploy.yml already updated (this commit) to map
//      MCP_CANARY_KEY=mcp-canary-key:latest into the amjis-web deploy step's
//      `secrets:` block — merge to main and let the normal deploy pipeline run so
//      the env var is live on the next revision.
//   4. THEN apply this Terraform resource (it will otherwise create a scheduler job
//      that calls a route returning 503 MCP_CANARY_KEY not configured):
//        cd infra/scheduler && ./apply.sh apply
//
// Mirrors the exact pattern established in infra/scheduler/main.tf (mv_refresh /
// pending_stream_reaper) and panchanga_refresh.tf: same variables, same provider,
// same OIDC auth model. Declared in a separate file to keep this addition surgical
// and independently reviewable/applicable.

resource "google_cloud_scheduler_job" "canary_battery_daily" {
  name             = "canary-battery-daily"
  description      = "R5.1 C5.2 — daily P1-P8 canary probe battery against prod MCP (both canonical charts), feeds system_health, alerts on regression."
  schedule         = "0 6 * * *" // 06:00 UTC daily
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "300s" // 8 probes x 2 charts = 16 live MCP tool calls

  retry_config {
    retry_count          = 1
    min_backoff_duration = "60s"
    max_backoff_duration = "300s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/admin/cron/run-canary-battery"
    headers = {
      "Content-Type" = "application/json"
      // x-marsys-cron-secret (NOT set here in plaintext — provision via
      // `gcloud scheduler jobs update http canary-battery-daily
      // --update-headers="x-marsys-cron-secret=<secret>"` post-apply). Reuses the
      // SAME mcpt-scheduler-secret value already live in Secret Manager. R5.2 A4
      // live-verification finding: see panchanga_refresh.tf's identical note —
      // a plain Authorization header does not survive Cloud Scheduler's HTTP
      // dispatch to a *.run.app target; x-marsys-cron-secret mirrors the
      // already-proven x-watchdog-auth convention instead.
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = var.scheduler_invoker_sa
      audience              = var.amjis_web_url
    }
  }
}

output "canary_battery_scheduler_job" {
  value = google_cloud_scheduler_job.canary_battery_daily.name
}
