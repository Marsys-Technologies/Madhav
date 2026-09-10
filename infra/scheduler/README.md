# infra/scheduler — Cloud Scheduler jobs as IaC

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

This table covers the two Scheduler jobs defined in `main.tf`. The separate
`panchanga_refresh.tf` and `canary_battery.tf` resources remain in this Terraform
module and are intentionally not represented here. The Nirmana elevation monitor
is isolated in `../nirmana_elevation_monitor` with its own Terraform state.

| Job name                           | Cadence              | Target                                                                                                  | Purpose                                                              |
|------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `amjis-mv-refresh`                 | `0 */6 * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/cron/refresh_materialized_views`                                  | Refreshes materialized views (school_convergence_index + others).    |
| `amjis-pending-stream-reaper`      | `*/10 * * * *` (UTC) | HTTP POST → `https://amjis-web.../api/admin/cron/reap-pending-streams`                                 | Marks orphaned `pending`-state stream rows as `failed` after timeout. |

All tabled jobs authenticate via OIDC token with the target URL as audience and
retain their existing `scheduler_invoker_sa` configuration.

## Files

- `main.tf` — provider and the two tabled job resources.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Apply discipline

IaC only. `terraform apply` runs only from protected `main`, never from a worktree
or an unprotected branch. This change does not apply Terraform, create or update a
Cloud Scheduler job, deploy an application revision, or invoke the monitor.
