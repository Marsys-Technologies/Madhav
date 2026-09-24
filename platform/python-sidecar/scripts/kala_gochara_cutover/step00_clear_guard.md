# Step 0 — Phase 1.1: Clear `is_active` filter + (table, generation) guard

Runbook: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 step 0.
Sheet: GOCHARA_RULING_SHEET_v2_0.md A-2 (tranche 1).
Tranche: 1 (requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`; this step is a git
operation plus a TS-side gate test, not a SQL step).

## What this step consumes — do not re-implement

The Clear-route `is_active` filter and the (table, generation) guard already
exist on branch `origin/l3/kala-p1-1-b1-clear-guard`, head commit
`eb00da67d` ("close the live Clear path into the protected Gochara v1 snapshot
(B1)"). The remainder brief §7.A is explicit: **reference or cherry-pick with
attribution; do not duplicate them.**

Landing instruction at tranche-1 start:

```
git fetch origin l3/kala-p1-1-b1-clear-guard
git cherry-pick -x eb00da67d   # attribution preserved via -x trailer
```

If the branch has merged to `main` by the time the tranche runs, this step is
a no-op: verify with `git merge-base --is-ancestor eb00da67d origin/main` and
record the result in the evidence file instead of cherry-picking.

Also in scope per runbook step 0: the stale migration-540 comment at
`platform/src/app/api/cockpit/clear/route.ts:95-96` is removed by that same
change set — confirm it is gone after the cherry-pick, and remove it in a
follow-up commit on the tranche branch if the cherry-pick did not carry it.

## Gate test (TS-side; not runnable from this directory)

The route test lives with the change on the guard branch:
`platform/src/app/api/cockpit/clear/__tests__/route.protected-assets.test.ts`
(sweep row unreachable by any principal). Gate: that test green after the
cherry-pick, plus a static check that `clear/route.ts` filters
`is_active=false` assets out of Clear dispatch.

Rehearsal status: **NOT_RUN** on the disposable database — this step's gate is
a route test against the TS layer, which the rehearsal DB cannot host. Recorded
as NOT_RUN with this reason in WP10_REHEARSAL_v1_0.md.

## Reversal

Revert the cherry-picked commit (`git revert <cherry-pick-sha>`).

## Evidence

`evidence/step00_evidence.md` — record: whether the branch was already merged,
the cherry-pick sha, the route-test result, and the stale-comment check.
