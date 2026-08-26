# infra/scheduler — Cloud Scheduler jobs as IaC

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Three Cloud Scheduler jobs that were previously comment-only / manually-created:

| Job name                           | Cadence              | Target                                                                                                  | Purpose                                                              |
|------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `amjis-mv-refresh`                 | `0 */6 * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/cron/refresh_materialized_views`                                  | Refreshes materialized views (school_convergence_index + others).    |
| `amjis-pending-stream-reaper`      | `*/10 * * * *` (UTC) | HTTP POST → `https://amjis-web.../api/cron/reap_pending_streams`                                        | Marks orphaned `pending`-state stream rows as `failed` after timeout. |
| `amjis-nirmana-elevation-monitor`  | `*/5 * * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/admin/internal/nirmana-elevation-monitor`                         | Records a read-only NTAP program-synchronization observation.         |

All jobs:
- Authenticate via OIDC token, audience = target URL.
- Run as `amjis-builder-runtime` (cron caller — least-priv: only `roles/run.invoker` on amjis-web).

The Nirmana monitor has a 120-second deadline and at most two retries. Its route
also validates `MARSYS_CRON_SECRET` through `X-Marsys-Cron-Secret`; configure that
existing secret header after apply by the established Scheduler procedure. Do not
put the secret in Terraform, its variables, or state, and do not use `Authorization`
for the app secret because Scheduler uses it for the OIDC token.

## Files

- `main.tf` — provider + 3 `google_cloud_scheduler_job` resources + IAM grant for the cron caller.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Apply discipline

IaC only. `terraform apply` runs only from protected `main`, never from a worktree
or an unprotected branch. This change does not apply Terraform, create or update a
Cloud Scheduler job, deploy an application revision, or invoke the monitor.

## Acceptance pointer

The Nirmana monitor's static contract test is
`platform/src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts`.
It verifies the scheduler resource, five-minute cadence, protected route, OIDC
caller/audience, secret-header convention, retries, and deadline without invoking
Terraform or cloud resources.
