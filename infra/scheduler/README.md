# infra/scheduler — Cloud Scheduler jobs as IaC

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

This table covers the three Scheduler jobs defined in `main.tf`. The separate
`panchanga_refresh.tf` and `canary_battery.tf` resources remain in this Terraform
module and are intentionally not represented here.

| Job name                           | Cadence              | Target                                                                                                  | Purpose                                                              |
|------------------------------------|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `amjis-mv-refresh`                 | `0 */6 * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/cron/refresh_materialized_views`                                  | Refreshes materialized views (school_convergence_index + others).    |
| `amjis-pending-stream-reaper`      | `*/10 * * * *` (UTC) | HTTP POST → `https://amjis-web.../api/admin/cron/reap-pending-streams`                                 | Marks orphaned `pending`-state stream rows as `failed` after timeout. |
| `amjis-nirmana-elevation-monitor`  | `*/5 * * * *` (UTC)  | HTTP POST → `https://amjis-web.../api/admin/internal/nirmana-elevation-monitor`                         | Records a read-only NTAP program-synchronization observation.         |

All tabled jobs authenticate via OIDC token with the target URL as audience.

The legacy MV-refresh and pending-stream-reaper jobs retain their existing
`scheduler_invoker_sa` configuration. Only the Nirmana monitor uses the dedicated
`amjis-nirmana-monitor` service account. Terraform grants that account only
`roles/run.invoker` on the single `amjis-web` Cloud Run service; it grants the
Cloud Scheduler service agent `roles/iam.serviceAccountTokenCreator` only on that
dedicated service account so Scheduler can mint its OIDC token.

The Nirmana monitor has a 120-second deadline and at most two retries. Its route
also validates `MARSYS_CRON_SECRET` through `X-Marsys-Cron-Secret`; configure that
existing secret header outside Terraform after apply. Do not put the secret in
Terraform, its variables, or state, and do not use `Authorization` for the app
secret because Scheduler uses it for the OIDC token. The monitor job ignores only
its HTTP-header map after initial creation so a later Terraform run does not remove
the separately configured secret header.

## Files

- `main.tf` — provider, the three tabled job resources, and monitor-only IAM resources.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Apply discipline

IaC only. `terraform apply` runs only from protected `main`, never from a worktree
or an unprotected branch. This change does not apply Terraform, create or update a
Cloud Scheduler job, deploy an application revision, or invoke the monitor.

## Protected-main pre-apply IAM and secret-header procedure

Before a protected-main apply, confirm that the Cloud Scheduler API has created
its Google-managed service agent and that the Terraform executor may, within this
project only: create the dedicated service account, set IAM policy on that account,
set IAM policy on the `amjis-web` service, and create/update Scheduler jobs. These
are required for the monitor's dedicated identity, its service-level invoker grant,
and the Scheduler service agent's token-mint binding; no project-wide `run.invoker`
or broad runtime identity is required for this monitor.

After the protected-main resource exists, an approved secret-aware operator—not
Terraform—must configure the existing `MARSYS_CRON_SECRET` under the custom header.
Use the organization-approved secret-injection mechanism, never a clipboard,
shell-history literal, Terraform variable, or source-controlled file. The operation
targets `amjis-nirmana-elevation-monitor` in `madhav-astrology` / `asia-south1`:

```sh
gcloud scheduler jobs update http amjis-nirmana-elevation-monitor \
  --project=madhav-astrology \
  --location=asia-south1 \
  --update-headers='X-Marsys-Cron-Secret=<value injected only by the approved secret-aware operator>'
```

Verify without printing the header value:

```sh
gcloud scheduler jobs describe amjis-nirmana-elevation-monitor \
  --project=madhav-astrology \
  --location=asia-south1 \
  --format=json | jq -e '.httpTarget.headers | has("X-Marsys-Cron-Secret")'
```

Then verify the job's OIDC principal and target URI in the same protected operator
session, and verify a new authenticated dashboard observation becomes fresh within
the five-minute cadence plus the ten-minute grace. Do not invoke the monitor merely
to test this configuration.

## Acceptance pointer

The Nirmana monitor's static contract test is
`platform/src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts`.
It verifies the scheduler resource, five-minute cadence, protected route, OIDC
caller/audience, secret-header convention, retries, and deadline without invoking
Terraform or cloud resources.
