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
