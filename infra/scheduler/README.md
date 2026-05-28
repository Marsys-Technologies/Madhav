# infra/scheduler — Cloud Scheduler jobs as IaC

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Two Cloud Scheduler jobs that were previously comment-only / manually-created:

| Job name                           | Cadence              | Target                                                                                                  | Purpose                                                              |
|------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `amjis-mv-refresh`                 | `0 */6 * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/cron/refresh_materialized_views`                                  | Refreshes materialized views (school_convergence_index + others).    |
| `amjis-pending-stream-reaper`      | `*/10 * * * *` (UTC) | HTTP POST → `https://amjis-web.../api/cron/reap_pending_streams`                                        | Marks orphaned `pending`-state stream rows as `failed` after timeout. |

Both jobs:
- Authenticate via OIDC token, audience = target URL.
- Run as `amjis-builder-runtime` (cron caller — least-priv: only `roles/run.invoker` on amjis-web).

## Files

- `main.tf` — provider + 2 `google_cloud_scheduler_job` resources + IAM grant for the cron caller.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Apply discipline

IaC only. Apply runs on main; never from a worktree.

## Acceptance pointer

Acceptance item 5 (BRIEF_4_edge_and_infra_hygiene.md): "`infra/scheduler/` has 2 jobs
(MV-refresh, pending-stream-reaper) with cadence specs." Both `google_cloud_scheduler_job`
resources have explicit `schedule = "..."` attributes.
