---
artifact: MADHAV_PURNA_ANVESANA_TRANSFER_HANDOFF_2026_09_19
status: HANDOFF_READY
scope: execution-ownership transfer only; product completion is not accepted
prepared_at: 2026-09-19
---

# Pūrṇa Anveṣaṇa execution handoff

## Stand-down state

- The campaign goal is **PAUSED**, not complete. The recurring automation
  `planner-and-inquiry-autonomous-monitor` was deleted during handoff. No campaign worker,
  database mutation, protected CI run, or deployment operation remains in flight.
- The active integration reference is protected `origin/main@4adcf04978757d2f8e8157492f1922f8b5fb92e3`
  (`feat(purna): expand source availability contracts`, PR #2681, merged 2026-09-19 03:42:42Z).
  The prior PR head `24839cc8562de619f0d5c8fc032766b5b38ae197` is contained by that merge.
- This task's preserved worktree is
  `/Users/Dev/.codex/worktrees/23e4/Madhav`, branch
  `codex/purna-product-completion-v2`, clean at
  `95242400fe2dbcf4b5f545f4d74af411a0493051`. Its PR #2633 is merged, but its historical
  commit is not an ancestor of the current protected main because protected delivery used a
  different integration history. Do not treat that branch head as current deployment evidence.

## What is established

- The immutable product denominator remains five original cases / 34 route obligations plus 30
  product scenarios, executed through Portal, managed MCP, and governed raw MCP.
- Current protected-main capability census: 182 addressable SCUs, 186 executable bindings, 257
  typed concepts, 53 edges, 152 executable availability contracts, and zero undispositioned
  producer/isolated-SCU gaps. The compiler preserves the review denominator of 174 descriptor
  reviews plus 8 authored declarations; this is source-accounting, not observed availability.
- PR #2681 passed the full local suite before merge: 12,270 passed, 704 skipped, 2 todo; TypeScript,
  code generation, and ESLint (0 errors) passed. Its protected integration is proven; deployment
  and live corpus acceptance are not.
- The source-only Beyond-Acarya record remains 34/34 routes, 0 omissions, and
  `SOURCE_ONLY_NOT_LIVE`. The product 5+30 suite has no candidate/live acceptance run.
- Historical three-door evidence proved only a shared active snapshot and fail-closed dark state.
  It did not prove delivered 34-route replay, pagination/exhaustion, strict semantic parity,
  cross-instance recovery, or product answer acceptance.

## Live state observed during handoff

- Cloud Run `amjis-web` and `amjis-mcp` are each at 100% traffic on
  `*-probe-93a3a5eb8d85-35069281039-1`, whose `NIRMANA_DEPLOYED_SHA` is
  `93a3a5eb8d8552656efc6582d92dfbdf7555b0e1`. This is older than, and cannot validate,
  protected `origin/main@4adcf049...`.
- Latest ready revisions are those same `93a3...` probe revisions. No release for PR #2681 was
  observed. The only recent branch deploy record relevant to this task is GitHub run 35256663582
  for `95242400...`: its PR-only image-build job succeeded while all deploy/migration jobs were
  skipped. It is not deployment evidence.
- A read-only revision inspection exposed a literal legacy watchdog secret in the zero-percent,
  tagged `amjis-web-02826-huf` revision. The value is intentionally not recorded here. Treat this
  as a security incident: an authorized security/runtime owner must revoke/rotate it and audit
  revision/env exposure before using that revision or its configuration as evidence. No secret,
  IAM, traffic, or runtime setting was changed in this handoff.

## Preserved work and continuation actions

| Item | State | Exact continuation action |
| --- | --- | --- |
| PR #2681 / `codex/purna-l1-next-contracts` | merged; clean at `24839cc...` | Rebase a new successor on `origin/main@4adcf...`; do not re-merge its commits. Continue only by auditing the remaining executable bindings against real probes/receipts. |
| PR #2676 / `codex/purna-l0-remedy-contract` | open, clean, base `codex/purna-autonomy-recovery` | Preserve; review/rebase its stacked base before any integration. It is not current-main delivery. |
| PRs #2597–#2605 | open clean stacked historical source-review chain | Preserve as evidence/history; do not drain them mechanically into main. Reconcile scope and protected-base ancestry first. |
| `/Users/Dev/.codex/worktrees/a4d5/Madhav` | one untracked file `docs/superpowers/plans/2026-09-17-purna-anvesana-focused-completion.md` | Preserve verbatim; identify its author and intent before staging or deleting. |
| `/Users/Dev/.codex/worktrees/purna-focused-completion` | same untracked plan file | Preserve verbatim; it appears duplicated across worktrees, so reconcile ownership before mutation. |

All other Pūrṇa/planner/source-query worktrees inspected for this handoff were clean. No in-flight
mutation owner or active protected CI was found.

## Blockers and safe next sequence

1. Start a successor from exact `origin/main@4adcf...`; regenerate the capability snapshot/census
   and identify the remaining binding-level evidence gaps. Do not infer probe success from a source
   contract.
2. Obtain authorized data-plane/admin access sufficient to read the deployed revision identity,
   provision/replay an approved corpus, and write only approved evidence records. Fail closed if
   the credential lacks those rights; never reconstruct credentials.
3. Release a revision containing the chosen protected-main successor, then prove the running
   revision through `latestReadyRevisionName` and its `NIRMANA_DEPLOYED_SHA` for each served door.
4. Execute and retain the immutable 5/34 plus 30-case three-door corpus. Require real evidence
   receipts for delivery, pagination/exhaustion, interruption/cross-instance recovery, and the
   independent automated answer scorer. Fixtures, source tests, CI, or dark-state agreement do
   not satisfy these gates.
5. Address the legacy secret incident under separate authorized security ownership; do not couple
   it to a source-contract patch or make a completion claim until the audit/rotation evidence exists.

## Native Surrogate and operating controls

- On two identical deterministic failures, invoke a GPT-5.6 Sol high Native Surrogate with the
  exact failure fingerprint, governing charter, permitted actions, and stop conditions. It may
  decide charter-scoped implementation/evidence choices only, must record its decision, must not
  invent credentials/IAM/release approval, and then returns control to the original model/effort.
- For external credentials, IAM, secrets, production roles, or release approval: fail closed,
  prepare the exact authority request, and continue independent source/test/evidence work.
- There is no remaining heartbeat/control loop for this campaign. The successor owner must create
  a new one only after taking ownership and must make it quiet on unchanged state.

## Evidence anchors

- `CAMPAIGN_STATE.md`, `LIVE_COMPLETION_MATRIX_v1.json`,
  `PRODUCT_ACCEPTANCE_PROTOCOL_v2.json`, and `BEYOND_ACARYA_ACCEPTANCE_v4.json` in this directory.
- Source plan: `docs/superpowers/plans/2026-09-17-purna-product-completion-v2.md`, SHA-256
  `6cc17144f3877bdac7048f9a7cba5caf15e1f7ca59306289c0f13ec94eb1b666`.
- Source verification commands: `npm test`, `npm run typecheck`, capability code generation/checks,
  and the Pūrṇa-focused suites recorded in `SOURCE_VERIFICATION_EVIDENCE_v1.json`. Re-run against
  the successor exact head rather than inheriting their pass.
