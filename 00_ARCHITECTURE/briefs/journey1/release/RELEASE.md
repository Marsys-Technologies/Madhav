---
artifact: JOURNEY1_RELEASE
version: 1.0
status: DEPLOYED_WITH_RECORDED_RESIDUALS
---

# Journey 1 release

Direct owner authorization: “Go ahead and deploy it.” Scope is the reviewed Journey1 payload and required release corrections, existing protected PR/merge queue/CI, zero-traffic web candidate, guarded promotion and live verification. Journey2 stays deferred. No new migration, chart rebuild, paid provider execution, credential/account approval/reset or foreign-worktree change.

Release authority narrowly supersedes GIP §P.4 for this delivery only; CCD-021 records it. Existing quality and exact-revision/traffic controls remain.

Baseline: main `944ccf22c250b6ebd0507c18d0f23438efceade4`; 100% live `amjis-web-probe-944ccf22c250-37310776256-1`. This is the rollback reference, not a deployment claim for the new UI.

Steps: typed test lint fixes, current-main reconciliation, full lint/types/unit, production build via protected PR, merge queue, established no-traffic smoke/promotion, authenticated read-only UI verification and traffic/revision proof. Real account creation/reset remains a separate manual acceptance task; no production records will be created to demonstrate it.

## Local qualification

Reconciled current protected main `944ccf22c250` into the owned branch with no conflicts. Full ESLint: zero errors,628 inherited warnings; TypeScript including tests: zero errors; full unit suite:1,409 files and15,655 tests passed, zero unexpected failures. Three lint-error test fixtures are now explicitly typed, with all security/provisioning assertions retained. In-session adversarial review: `RED_TEAM.md`, limitations disclosed. Repository merge protections and zero-traffic release checks remain required.

## Release-gate correction

First PR governance run rejected the candidate because the implementation close appended SESSION_LOG but its current-state dedicated last-session pointer retained the prior AI Console session (44 schema findings versus baseline43). Corrected only the close provenance fields to match the validated implementation record; other campaign fields remain unchanged. No gate ceiling or validation rule was changed.

## Deployed outcome

PR #3178 merged through the protected queue to `052ac7e89856757bbb2564688ff111a9a2c2cc05`. PR build, queue CI and main CI passed. Deploy run37325087280 succeeded; web candidate smoke and Pūrṇa signing/RLS canary passed before promotion. Both desired and observed traffic give100% to `amjis-web-probe-052ac7e89856-37325087280-1`; image and commit label match. Existing tags preserved. Only web deployed; no new migration was applied.

Live Chrome verified the reviewed entry and chart screens, actual distinct D1/D9/D10, title/pin controls, Places suggestion/coordinate fill, username availability, and responsive391px/1512px screens without saving/resetting/approving/building any records.49 recorded Journey1 HTTP requests returned200, zero5xx. Exact scope: `LIVE_REVIEW.json`, `HTTP_CHECKS.json` and screenshot evidence.

Residuals remain explicit: native activation-window lookup is unavailable (no invented timeline); separate automatic Paripraśna behaviour smoke failsHTTP400 /6 of11 blocking assertions on both this revision and the previous baseline (`PARIPRASHNA_RESIDUAL.json`). Root causes and engine/build repair are not qualified by this release. Real login/recovery/reset/approval/username-save/chart-CRUD/recompute acceptance is not exercised. Journey2 remains deferred, and the separate cleanup worktree is untouched.
