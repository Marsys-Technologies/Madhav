---
artifact: BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE
type: PARKED FOLLOW-UP BRIEF (spec only — not executed)
campaign: PB — Paripraśna Build
wave: PB-3.1 (follow-up to PB-3 SAMĪKṢĀ)
version: 1.0
status: READY-FOR-EXECUTION — parked, awaiting native go-ahead
date: 2026-07-29
authored_by: Claude Code (PB-3 §G gate-close session)
governing: REPORT_PB-3.md (SHIP-DEGRADED disposition, §G items 3/4/5/7/8/11), BRIEF_PB-3.md,
           MEMO_PB-3_0.md, LEDGER_MAP_PB-3.md, FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md
           (the false-confidence-gate doctrine this brief's acceptance criteria enforce)
sequencing: Re-enters `platform/src` — runs AFTER SATYA-DĪPA PR #870 merges, under the same
            merge lock PB-3 operated under. Do not open lanes against `main` before #870 lands.
---

# BRIEF_PB-3.1 — Make the loop live

## Mission

Turn the PB-3 prediction loop from **built-but-inert** into **live**: a real deployed reading
flows all the way to a resolved, scored outcome, with nothing in the chain unmounted, starved,
or silently no-op-ing.

## Why this brief exists

`REPORT_PB-3.md` closed PB-3 SHIP-DEGRADED, not PASS. Every lane's own tests passed; the wave's
own gate proved that in production the loop has **no live entry** (the confirm affordance is
dead code, unmounted on every route — `brahma_mimamsa_prediction_ledger` holds zero rows despite
six real detections) and **no live exit** (the daily job silently no-ops on a secret-name
mismatch and reports green forever; the resolve action bypasses the wave's own Brier recorder).
This brief is the parked, costed fix for exactly those gaps — nothing more, nothing
speculative. It does not re-litigate anything REPORT_PB-3.md already disposed as
VERIFIED-FIXED (items 1, 2, 9, 10, 12) or as a legitimate park (item 8's calibration-write
half, per `PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md`, which stands unchanged).

## Scope — five gaps, each with its origin in REPORT_PB-3.md

| Gap | Priority | Origin | Fix |
|---|---|---|---|
| **G1** | **P0** | §G item 3/4/Final Proof — FAIL | Mount `LogToSamiksha` → `POST /api/pariprashna/samiksha/confirm` on the live Paripraśna reading route, so a real detection writes a `detected` ledger row. This is the loop's only missing entry point; every downstream FAIL/PARTIAL in the gate traces back to this one gap. |
| **G2** | **P1** | §G item 7 — FAIL | `samiksha-daily.yml:63` reads `secrets.DATABASE_URL`, which does not exist. Every other workflow in the repo uses `secrets.PROD_DATABASE_URL`. The one real cron run so far logged "skipping live run (exit 0)" and reported green. Fix: rename the secret reference; change the no-secret branch from `exit 0` to a visible failure so a misconfigured run can never report green again. |
| **G3** | **P1** | §G item 7 — the net that should have caught G2 | `SAMIKSHA_TEST_DATABASE_URL`/`SAMIKSHA_E2E_DATABASE_URL` are set nowhere in CI, so all six of the wave's own honesty-standard DB-integration tests (`samiksha_daily_job.integration.test.ts` and five siblings) are permanently skipped — the exact PB-2 false-confidence pattern, recurring. Fix: wire the env var(s) into the CI workflow so these tests actually execute on every PR, not just locally on demand. |
| **G4** | **P2** | §G item 8 — PARTIAL | The live resolve action (`resolvePredictionAction`/`batchResolveAction` in `clients/[id]/samiksha/actions.ts`) calls the L-1 `recordOutcome` DAL function directly with a locally re-implemented outcome→value map, bypassing L-5's `recordConversationalOutcome` (Brier computation + `CalibrationWriteIntent`) entirely — which as a result has zero non-test callers. Fix: wire the live route to the real recorder, OR — if there is a real reason the local map should stay separate — document that reason explicitly in code and in this brief's close report. Do not leave two outcome maps with no stated relationship between them. |
| **G5** | **P2** | §G item 11 — PARTIAL | `compute_spine_bundle.ts` assembles a `calibration` object that cannot currently reach a user-facing surface, but only by structural accident: no field marks it internal-only, `serving_path_manifest.ts` omits the two files that assemble it, and `assertNoCalibrationLeak` has zero production call sites (and, as written, would not even match the payload's key shape if it were wired). Fix: add `compute_spine_bundle.ts`, `materialize.ts`, `register_spine_bundle.ts`, and `query_calibration.ts` to `serving_path_manifest.ts`'s tracked set; add the spine-bundle URI to `CALIBRATION_CONTEXT_ONLY_URIS`; widen `CALIBRATION_LEAK_KEYS` to match a bare `calibration` object key; give `assertNoCalibrationLeak` a real call site in the response-assembly path. Close the containment deliberately instead of leaving it accidental. |

## Acceptance criteria — LIVE proofs, not fixtures

Every criterion below must be verified against the **real deployed route, on a real chart**,
never a hand-written fixture, a mock agreeing with itself, or a throwaway database standing in
for production. This is not a stylistic preference — it is the direct lesson of PB-3's own gate,
where six lanes' fixture-scoped tests all passed while the live product did nothing. A criterion
that can only be checked against a fixture has not been checked.

- **A1** — A real reading conducted on the deployed app produces a `detected` row in
  `brahma_mimamsa_prediction_ledger`. Verified by a direct `psql` query against production
  after the reading, not by a test double asserting the DAL function was called.
- **A2** — That row renders on the live review tab. Verified by a real screenshot or a DOM read
  of the deployed, authenticated `/clients/[id]/samiksha` route — not the unmounted
  `samiksha/KalaRekha.tsx`/`PredictionCard.tsx` pair the current gate found dead.
- **A3** — The row resolves to an outcome through the mounted UI, and choosing "can't tell"
  writes `outcome_value = NULL`. The PB-3 gate's demonstrated-can-fail proof — insert the
  violating row in a transaction, watch the DB CHECK constraint reject it for real, roll back,
  insert the valid row, confirm nothing is left behind — is the template to preserve, not
  merely a comment citing that it once passed.
- **A4** — The daily job, run against the real production database with the corrected secret,
  transitions a real `open` row to `window_closed`; and the CI integration tests that exercise
  this (currently permanently skipped) **run and pass** in the actual CI pipeline, not just
  locally with a manually-exported env var.
- **A5** — Exactly one outcome-scoring map exists, and the map that ships has a live production
  caller. If `recordConversationalOutcome` is the one that ships, its Brier computation and
  `CalibrationWriteIntent` must be observably produced by a real resolve action, not just by a
  unit test calling it directly.
- **A6** — The calibration leak guard runs in production (has a real call site in the response
  path, not just in a test harness), covers both the `query_calibration.ts` and
  `compute_spine_bundle.ts` paths, and a mutation test proves it can fail: temporarily reintroduce
  a leak locally, confirm the guard trips, then revert.

**Every criterion demands a demonstrated-can-fail check.** A green result that cannot be made to
go red by breaking the thing it claims to verify is not acceptance — per this campaign's own
§N.7 Earned-Signal doctrine, it is an unimplemented check wearing a clean result's clothes.

**Honest parking clause**: if any single criterion genuinely cannot be met live within this
brief's scope (for example, if mounting G1 surfaces a further downstream gap not visible from
outside a mounted route), that criterion parks with its own costed spec and an explicit
Pratinidhi MEMO ask — exactly as PB-3's own L-5 lane parked its calibration-write half. A
criterion may park honestly. It may not be quietly declared met by a fixture standing in for the
live proof.

## Sequencing

PB-3.1 re-enters `platform/src` — the same territory PB-3 itself worked in — and therefore runs
**after SATYA-DĪPA's PR #870 merges**, under the same merge-lock discipline PB-3 operated under
(rebase onto latest `main` immediately before integrating; no lane opens against a `main` that
still has #870 pending). This brief does not open lanes, does not create worktrees, and does not
touch `platform/src` in any way — it is a specification only, parked pending the native's
go-ahead to execute.

## Status

**READY-FOR-EXECUTION — parked.** This brief is complete and actionable as written. No lane has
been dispatched. Execution begins only on explicit native/Pratinidhi go-ahead, and only after
confirming PR #870 has merged.
