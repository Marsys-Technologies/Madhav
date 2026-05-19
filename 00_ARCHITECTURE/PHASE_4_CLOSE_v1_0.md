---
canonical_id: PHASE_4_CLOSE
version: 1.0
status: CURRENT (campaign sealing artifact)
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
closed_on: 2026-05-19
final_commit: d7ec853
---

# Phase 4 — Ephemeris Accessibility Campaign · CLOSE

## What shipped (4 sub-phases, 1 day)

| Sub | Commit | Headline |
|---|---|---|
| 4A | bd41f13 | query_ephemeris tool (27th) + R-TC transit-context rule in PLANNER_PROMPT v2.0.3 |
| 4B | c63ef9f | Migration 059 + 7 derived columns + MEAN_NODE Rahu + BPHS dignity/combust/vargottama + ephemeris_derivations.py |
| 4C | abab885 | Migration 060 + panchanga_daily + panchanga_derivations.py + query_panchanga (28th) + R-PA rule |
| 4D | d7ec853 | transit_search.py + sidecar /transit_search + query_transit_event (29th) + R-TE rule |

**Tool count: 26 → 29.**

Planner rules added: R-TC (transit-context lookup), R-PA (panchanga anchor), R-TE (transit event search).

Pre-commit gate results at §4.D close:
- `tsc --noEmit`: clean
- TS vitest full retrieve suite: 268/268 (29 test files)
- Python pytest transit_search: 12/12
- planner_regression_gate: 2/2

## Production deploys deferred to native

Three operator-supervised data operations remain (none execute autonomously):

1. **ephemeris_daily full rebuild (Path A)** — MEAN_NODE + 7 derived columns for all 657K rows. ~4–6h. Runbook: `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §2–3`.
2. **panchanga_daily bootstrap** — ~73K rows via bootstrap_panchanga.py. ~30 min. Runbook: `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4`.
3. **sidecar /transit_search verification** — curl spot-check after sidecar deploy. ~5 min. Runbook: `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §5`.

All steps documented in `00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`.

## Consolidated answer:eval

Per campaign discipline (declared 2026-05-17), production answer:eval against
the new 29-tool registry runs AFTER all 3 operator data operations complete.
This is the consolidated batch the native referenced in the original
retrieval-tools campaign agreement.

**Recommendation on sequencing (§8 item 7):** Run the Path A rebuild (data
operation 1) BEFORE the consolidated answer:eval batch. Path A changes Rahu
longitudes in ephemeris_daily, which affects sign/nakshatra values returned by
query_ephemeris. Running answer:eval pre-rebuild would score against stale Rahu
data and produce misleading results. The panchanga bootstrap (operation 2)
should also complete before eval — query_panchanga will return diagnostic
empty-table rows otherwise. The /transit_search sidecar verification (operation
3) is fast and can run immediately after sidecar deploy without waiting for the
Postgres rebuilds.

Recommended sequence: **sidecar deploy + verify → Path A rebuild → panchanga
bootstrap → consolidated answer:eval**. Estimated total pre-eval elapsed time:
~5h (dominated by Path A rebuild).

## Lessons captured

- **ephemeris_derivations.py as the canonical constant module.** The
  pure-Python derivation-module pattern established in §4.B was reused without
  modification in §4.C and §4.D. `SIGNS`, `SIGN_TO_IDX` from
  ephemeris_derivations.py and `NAKSHATRAS` from panchanga_derivations.py are
  the single source of truth for naming across the pipeline. No sub-phase
  re-declared constants.

- **Pre-commit verification + native-supervised data operation = the right
  split.** Code merges fast; data rebuilds get the human review they need. The
  brief-executor discipline (author → gate → commit → defer data ops) was
  respected for all four sub-phases.

- **Executor scope-notes as the loop-back channel.** Two semantics carry-forwards
  from §4.C to §4.D (tithi integer-floor convention, vara IST-datetime
  convention) were captured as `executor_scope_notes_for_4D` in the master plan
  §B block. §4.D honored both. This is the pattern for future multi-sub-phase
  campaigns.

- **Synthetic mock data sizing for bisection tests.** The bisection loop in
  `transit_search.py` runs up to 30 iterations with 2 `calc_ut` calls per
  iteration (60 calls for bisection) plus 2 for bracketing = 62 minimum. Tests
  that use a finite `side_effect` list must provide ≥66 items to avoid
  `StopIteration`. The fix: `*([lo, hi] * 32)` pairs.

- **revjul mock discipline.** When `_make_swe()` sets `revjul.side_effect` as a
  lambda, test-level `return_value` assignments are silently ignored. The fix:
  use `return_value` (not `side_effect`) in `_make_swe()` for revjul so
  individual tests can override cleanly.
