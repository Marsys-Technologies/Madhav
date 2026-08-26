# Task 6 — NTAP tracker monitor scheduler IaC report

## Status

Complete: scheduler IaC, its static contract test, scheduler documentation, and
the NTAP monitor operator runbook are present. No Terraform apply, Cloud Scheduler
create/update, deployment, production trigger, or production-code change was run.

## Delivered

- `infra/scheduler/main.tf` declares
  `amjis-nirmana-elevation-monitor` as a five-minute UTC POST to the internal
  monitor route. It uses the existing production URL variable, `scheduler_invoker_sa`,
  OIDC audience, two retries, and a 120-second deadline.
- The resource documents the established `X-Marsys-Cron-Secret` configuration
  model without placing a secret in Terraform or state; OIDC retains the
  `Authorization` header.
- `infra/scheduler/README.md` requires apply only from protected `main` and
  explicitly records this task's non-application boundary.
- `scheduler-contract.test.ts` statically verifies the resource, cadence, route,
  OIDC service account/audience, secret-header convention, retry count, and deadline.
- `docs/runbooks/ntap-tracker-monitor.md` defines the audited super-admin baseline
  acceptance and plan-supersession flows, fresh/stale verification, and the
  prohibitions on direct SQL, historical-ledger import, and manual progress edits.

## Verification

- Before implementation: the new focused scheduler contract test failed because
  the `nirmana_elevation_monitor` Scheduler resource did not exist.
- After implementation: `cd platform && npx vitest run src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts` — PASS (1 test).
- `cd platform && npx tsc --noEmit` — PASS.
- `terraform fmt -check infra/scheduler/main.tf` — PASS.
- `git diff --check` — PASS.

## Commit

`feat(nirmana): schedule NTAP tracker monitoring`

## Concern / follow-up

The authenticated snapshot and dashboard Audit Drawer expose only
`candidate_definition_sha256`; they do not currently expose the required
`candidate_catalogue_sha256`. The governed acceptance endpoint correctly requires
both. The runbook therefore blocks baseline acceptance until an authenticated
candidate-detail surface exposes both exact current digests; it forbids deriving a
replacement through the scheduler-only internal endpoint, direct SQL, or a manual
value. This is an existing acceptance-surface gap, not bypassed by Task 6.

## Fix Round 1 — dedicated monitor scheduler principal

The initial Scheduler resource reused `scheduler_invoker_sa`, whose default is the
broad `amjis-builder-runtime` identity. Per the controller's least-privilege ruling,
the monitor now uses a dedicated `amjis-nirmana-monitor` service account instead.

- Terraform grants that principal `roles/run.invoker` only on the `amjis-web` Cloud
  Run service in the configured region; legacy jobs and their existing principal are
  unchanged.
- Terraform grants the Cloud Scheduler Google-managed service agent the standard
  OIDC token-mint role only on this dedicated service account.
- The monitor job ignores only its HTTP-header map after initial creation so the
  approved out-of-band `X-Marsys-Cron-Secret` configuration is not later removed by
  Terraform. The README now includes protected-main pre-apply IAM requirements and
  a non-secret-bearing job/project/region/header-presence verification procedure.
- The static test was strengthened to inspect the exact service-account, service
  IAM, token-mint IAM, and Scheduler job resources plus the operator instructions.

Verification after Fix Round 1:

- Focused scheduler contract test — PASS (1 test).
- `cd platform && npx tsc --noEmit` — PASS.
- `terraform fmt -check infra/scheduler/main.tf` — PASS.
- `git diff --check` — PASS.

No Terraform apply, Scheduler mutation, deployment, or monitor invocation was run.
