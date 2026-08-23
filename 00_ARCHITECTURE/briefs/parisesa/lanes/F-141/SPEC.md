---
lane: F-141
stream: S6_ADHARA
stage: S (SPEC) — rescoped remediation per PAR-R-9
author: ADHARA-LEAD (sonnet)
---

# F-141 — SPEC

## 0. Scope note

This is a **disclosure-only remediation** (SP-8), not a defect fix. PRATINIDHI (PAR-R-9,
`LEDGER_PRATINIDHI.md`, `par/pratinidhi-ledger`) refused both DB-write options this lane
escalated (restate `state`, rebuild) and rescoped F-141 to: a detector, honest disclosure
of the 5 real rows, a continued (best-effort, not required-complete) mechanism trace, and a
pre-write evidence snapshot. This SPEC covers the parts of that rescoped remediation that
are genuine code/doc changes with an exit test; the mechanism trace itself is inconclusive
and reported as such, not as a closed sub-claim.

## 1. Root cause

Two independent, compounding gaps, not one:

1. **The detector was scoped too narrowly.** `platform/scripts/governance/ekv_controls.py`'s
   pre-existing `F-102` control checked `state = 'lit'` only, missing the `'mature'` state
   also present in this column's live vocabulary — a narrower invariant than the real one
   (`state IN ('lit','mature') AND last_error IS NOT NULL AND last_error <> ''`).
2. **The detector was never actually run.** Even at its narrower scope, `F-102` was (a) not
   in `ekv_controls.py`'s `CHEAP_IDS` per-batch subset (so INTEGRATOR's routine `--cheap`
   invocations always skipped it) and (b) not referenced by any file under
   `.github/workflows/` (so no CI job ever calls it at all, cheap or full). A detector
   function existing in source is not the same as an invariant being monitored — this is
   the concrete, traced mechanism behind "nothing detects this today," not merely an
   assertion about it.

The underlying 5 anomalous `asset_throughput` rows are a **separate, still-untraced**
question (see DIAGNOSIS.md §5) — PAR-R-9 confirmed no known orchestrator or watchdog-route
code path can currently produce any of them. This SPEC does not claim to close that
question; it closes the detection gap that let it go unnoticed.

## 2. Files changed

- `platform/scripts/governance/ekv_controls.py`:
  - `_check_f102`: SQL widened from `state = 'lit'` to `state IN ('lit', 'mature')`;
    docstring rewritten to record the PAR-R-9 census, the CI-wiring-gap finding, and the
    5-row live count at time of writing (commit `39a8e7206`).
  - `ALL_CONTROLS` / `CHEAP_IDS`: `F-102`'s `is_cheap` flag flipped `False → True` and added
    to `CHEAP_IDS`, so INTEGRATOR's routine per-batch `--cheap` runs stop silently skipping
    it (commit `6ea6dd4d3`, responding to a second independent gap INTEGRATOR found after
    the first commit). Module docstring's CHEAP-subset listing updated to match.
- `00_ARCHITECTURE/briefs/parisesa/evidence/F-141_pre_write.json` (new) — the PAR-R-9-
  mandated pre-write snapshot: full row content for all 5 violating `asset_throughput` rows,
  captured read-only via direct SQL, independently re-derived (not copied from the ruling)
  and cross-checked to match it exactly.
- `00_ARCHITECTURE/briefs/parisesa/lanes/F-141/DIAGNOSIS.md` — Stage D findings plus the
  PAR-R-9 addendum recording the corrected census and the refused-fix reasoning.

**Explicitly not changed:** no `asset_throughput` row. No `platform/src/app/api/cockpit/
watchdog/route.ts` (traced, found already correct — see DIAGNOSIS.md §3). No
`pipeline/orchestrator/asset_runner.py` (the D-1.6 no-op-completion branch was read as part
of the continued trace; no change made because the trace did not reach a confirmed
conclusion — see §4).

## 3. Exit test

Not a red→green unit test — this is a live-data detector, and per VERIFIER's own standing
rule from PAR-R-10 (recorded in `REBUILD_SCOPE.md`), an in-worktree assertion is not live
evidence for a writer/data-layer claim. The exit criterion is instead:

**Command:** `python3 platform/scripts/governance/ekv_controls.py --control F-102 --db-url
<production DATABASE_URL>` (or `--json` for machine-readable output).

**Expected result today (and the correct, honest result — this is a disclosure detector,
not a bug the code should silently make disappear):** `FAIL`, reporting `5` — matching
`evidence/F-141_pre_write.json`'s row count exactly. A `PASS` (`0`) would mean either the
5 rows were genuinely repaired through the FROZEN orchestrator (not authorized by PAR-R-9
tonight) or the detector regressed and stopped seeing them — both are real signal either
direction, which is the point of a real detector per §N.8.

**Verified this session** (read-only, via `mcp__postgres__query`, not by running the actual
script — no `DATABASE_URL` is exposed to this environment): the widened SQL predicate
(`state IN ('lit','mature') AND last_error IS NOT NULL AND last_error <> ''`) independently
re-run against live production returns count `5`, matching `evidence/F-141_pre_write.json`.
The script's SQL is copied verbatim from what was tested; VERIFIER or a session with real
DB-URL access should still run the actual script end-to-end before marking this LIVE, per
PAR-R-10's own standing rule.

## 4. Sibling sites covered

Not applicable in the usual sense (this is not a code-defect-with-repeated-instances lane).
The two candidate mechanisms named in DIAGNOSIS.md §5 (`asset_runner.py`'s D-1.6 no-op-
completion / `zero_rows_is_complete` branch for the 4 global singletons; genuinely unknown
for the `ka_kshetra` row) were both read this session. The `asset_runner.py` branch does not
contain an explicit, unconditional `last_error = NULL` clear on the specific
`zero_rows_is_complete`/global-singleton path this session could find — consistent with,
but not proof of, it being implicated. **Not confirmed; recorded as still open**, not
claimed as a covered sibling site. A future session with more budget should trace this
branch to its actual `UPDATE asset_throughput` statement (this session read the state-
determination logic but did not locate the exact persisting write for this specific path).

## 5. Recurrence guard

The widened + wired-into-CHEAP_IDS `F-102` control is itself the recurrence guard for the
detection gap (§1 item 1/2). It does not (and cannot, without DB-write authorization) guard
against the underlying 5-row anomaly recurring — that requires the mechanism trace to
actually complete, which is explicitly deferred, not claimed done.

**Still open, flagged for conductor/SENTINEL, not fixed in this lane (out of
`platform/scripts/governance/**`'s reach):** `ekv_controls.py` remains uninvoked by any
`.github/workflows/*` file. Wiring an actual scheduled or per-batch CI job to run the
now-cheap `F-102` (and the rest of the battery) is a SENTINEL/conductor-level decision
(`INTEGRATOR` has already been separately notified per this session's earlier report) —
this SPEC does not claim that wiring as done.

## 6. Dependencies / rollback

- Depends on nothing else landing first. No migration, no schema change.
- No DB write in this PR — nothing to roll back on the data side. Code rollback: `git revert`
  the two `ekv_controls.py` commits; no functional regression risk (the only behavior change
  is which rows a detector script flags and whether it runs in the cheap subset).
- PAR-R-9's explicit condition — no future write to any of the 5 rows without a fresh,
  separate PRATINIDHI ruling — is unaffected by this PR; nothing here authorizes or performs
  one.

## 7. Sub-claim coverage table

| Sub-claim (PAR-R-9's rescoped remediation items) | Status | Spec element |
|---|---|---|
| (1) Detector for the invariant | **Closed** | §2 `ekv_controls.py` widen + cheap-subset fix |
| (2) Honest disclosure of all 5 rows, preserve-don't-repair | **Closed** | §2 `evidence/F-141_pre_write.json` |
| (3) Continue mechanism trace as budget allows | **Attempted, inconclusive — honestly open** | §4 |
| (4) Pre-write snapshot before any future write | **Closed** | §2 (same evidence file doubles as this) |

## 8. Status

PR #1312 (`par/s6-f141-lit-beside-error` → `origin/main`), head `6ea6dd4d3`. `mergeable:
MERGEABLE`. Failing checks (`D-01a`/`D-01c`/`D-01d`/`D-08`) confirmed pre-existing on
`origin/main`'s own tip, unrelated to this diff (Python-only governance-script change).
**Not merged.** Expected close state per the conductor's framing: `PARKED-WITH-DETECTOR` —
the detector and disclosure are real, verified deliverables; the underlying anomaly is
correctly left open rather than guessed at.
