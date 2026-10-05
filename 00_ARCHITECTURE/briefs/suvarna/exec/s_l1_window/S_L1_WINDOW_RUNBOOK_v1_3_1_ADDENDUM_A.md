# S-L1 window runbook v1.3.1 — ADDENDUM A (deploy-environment pre-checks)

Status: addendum only. The runbook v1.3.1 (sha256 783536b4ab7289bf06cec65f1766003e0ec4ec2f42d83471d0db55dc0b808131) is locked and NOT reopened. This file adds three read-only pre-checks. Approved by Strategic Suvarṇa (madhav-06).

Basis (read from `.github/workflows/deploy.yml` on origin/main, names only):
- The routine `migrate` job ("Apply Routine DB Migrations") declares NO `environment:`. It uses the repo-level secret `PROD_DATABASE_URL` and shares the concurrency group `data-plane-production-cutover` (cancel-in-progress false = serialization only).
- The environment `data-plane-production-cutover` is declared only by `privileged-bootstrap` and `jataka-protected-migrations`. Our window does not use either in the normal path.

When executed: at W0, and again immediately before arming the W1 PR.

## A.1 Migration-state and protected jobs on the latest deploy
On the latest completed deploy run on main, confirm:
- "Inspect DB Migration State" outputs: data_plane = marked, data_plane_isolation = strict, nirmana = marked, purna = marked.
- Jobs `privileged-bootstrap` and `jataka-protected-migrations` = skipped.
- "Apply Routine DB Migrations" = success.
FAIL (any output different, or a protected job not skipped) → see A.3.

## A.2 No run holding the concurrency group
`gh run list --workflow deploy.yml` shows NO in-progress, queued or waiting deploy run (any branch or dispatch) that holds group `data-plane-production-cutover` at the time of arming W1. If one exists: do not arm; wait for it to finish (or report to SS if it is waiting on an approval).

## A.3 Fallback case needs the owner
If migration-state is not marked/strict (A.1 FAIL), the environment-gated `privileged-bootstrap` would be required on the next deploy and would wait for an approval by the owner; the routine `migrate` job (which needs it) would wait too. In that case: do NOT arm W1, tell SS and Pravāha (madhav-78) at once, and stay in the runbook's safe state. Nothing is approved by me or by a peer in place of the owner.

Read-only throughout: no secret value is read or printed; only job names, output names/values and run states.
