# infra/scheduler — Cloud Scheduler jobs as IaC

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

This table covers the Scheduler job defined in `main.tf`. The separate
`panchanga_refresh.tf` and `canary_battery.tf` resources remain in this Terraform
module and are intentionally not represented here. The Nirmana elevation monitor
is isolated in `../nirmana_elevation_monitor` with its own Terraform state.

| Job name                           | Cadence              | Target                                                                                                  | Purpose                                                              |
|------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `amjis-pending-stream-reaper`      | `*/10 * * * *` (UTC) | HTTP POST → `https://amjis-web.../api/admin/cron/reap-pending-streams`                                 | Marks orphaned `pending`-state stream rows as `failed` after timeout. |

The tabled job authenticates via OIDC token with the target URL as audience and
retains its existing `scheduler_invoker_sa` configuration.

The obsolete generic `amjis-mv-refresh` schedule interface is intentionally withdrawn: its `/api/cron/refresh_materialized_views` target is absent from the current source. Historical materialized views and migrations, the named manual dispatcher and recovery paths remain. This does not declare `school_convergence_index` unused or remove the other jobs. Provider retirement is separate and requires exact live job and Terraform state custody verification; no Terraform operation is performed here.

## Files

- `main.tf` — provider and the tabled job resource.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Apply discipline

IaC only. `terraform apply` runs only from protected `main`, never from a worktree
or an unprotected branch. This change does not apply Terraform, create or update a
Cloud Scheduler job, deploy an application revision, or invoke the monitor.
