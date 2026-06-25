---
artifact: GA_POSITIONS_FIX_EXECUTION_v1_0.md
canonical_id: GA_POSITIONS_FIX_EXECUTION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: GA_POSITIONS_CONTAMINATION_BRIEF_v1_0.md
purpose: >
  Execution prompt for the ga_positions contamination fix. The CODE FIX is already written by Cowork
  (see §1 — adapter passes birth_params, writer refuses native-fallback for non-native charts, footgun
  default removed, tests updated/added). This brief drives: verify+commit the code, rebuild job image,
  delete+recreate orphans, and the sequenced prod rebuild with whole-chart verification.
audience: Claude Code (Antigravity)
---

# ga_positions contamination — execution

## §1 — The code fix is ALREADY APPLIED in the working tree (Cowork-authored)
Confirm these exact changes via `git diff` before committing — do not re-derive them:

1. `pipeline/orchestrator/writers/ga_positions.py` — the adapter now passes
   `birth_params=ctx.config.get('birth_params')` to `build_ga_positions` (it previously dropped it —
   THE bug; every peer ga_ adapter already passes it).
2. `ga_writers/ga_positions_writer.py`:
   - `build_ga_positions` signature: `chart_id` is now REQUIRED (removed the
     `= CANONICAL_CHART_ID` native-default footgun).
   - Birth-param resolution replaced `bp = birth_params or NATIVE_BIRTH` with: explicit birth_params
     win; `NATIVE_BIRTH` permitted ONLY when `chart_id == CANONICAL_CHART_ID`; a non-native chart with
     no birth_params RAISES ValueError (refuses to contaminate).
3. `tests/test_ga_orchestrator_conformance.py` — the two ownership tests now pass `_DUMMY_BIRTH`
   (non-native chart needs explicit params); added `test_non_native_without_birth_params_refuses_native_fallback`
   and `test_native_without_birth_params_uses_native_default`.

NOTE: the FORENSIC gate is ALREADY native-scoped in the current code (`if chart_id == CANONICAL_CHART_ID:
forensic_gate(...)`, ga_positions_writer ~L483) — no change needed there; the earlier brief's
"scope the gate" step is already satisfied.

## §2 — PASTE TO CLAUDE CODE — verify, test, commit, job image
```
The ga_positions contamination code fix is already in the working tree (Cowork-authored). Verify and
ship it; do not rewrite the logic.

1. git diff — confirm exactly the 3 files in §1 changed and nothing else. If other files differ, list
   them and STOP.
2. Run the sidecar tests: pytest for ga_positions + the orchestrator conformance suite +
   test_ga_writer_generalization. All green. In particular the two NEW regression tests must pass
   (non-native-without-birth_params raises; native-without-birth_params is allowed).
3. Grep for any OTHER caller of build_ga_positions that relies on the removed chart_id default
   (a bare build_ga_positions() with no chart_id). The known callers (ga_prashna_cast, build_runner,
   the adapter, tests) all pass chart_id explicitly — confirm none break.
4. COMMIT: fix(ga_positions): pass per-chart birth_params; refuse NATIVE_BIRTH fallback for non-native charts
   Report the SHA.
5. JOB IMAGE: rebuild + push the brahma-build-pipeline-job image from this SHA (web deploy does NOT
   rebuild the job image). If the AK reckoning fix (GA_SENSITIVE_AK_RECKONING_FIX_BRIEF) is also ready,
   include BOTH commits in this single job-image build to avoid a double rebuild. Report the image
   tag/digest, and confirm a runs-response job_image_tag matches it.
```

## §3 — PASTE TO CLAUDE CODE — orphans (delete + recreate) — NATIVE APPROVED
```
Native approved deleting + recreating the two orphan charts (1789595b, b35046d8) — they have
graha_position rows but no public.charts row. Prod via :5433.

A — pre-delete safety (read-only): confirm BOTH chart_ids have ZERO row in public.charts AND are not
   referenced by asset_throughput or build_runs for any REAL chart. If either is referenced or appears
   in charts, STOP and report (do not delete).
B — DELETE all chart_facts rows (and any chart-scoped rows in chart_dashas, chart_divisionals,
   ga_condition_composite, asset_throughput) for these two orphan chart_ids ONLY. Record per-table
   row counts deleted. Never touch 482012f1 or 1c826d5a here.
C — RECREATE: these orphans had no birth data, so recreation needs real birth params. ASK THE NATIVE
   for each orphan's intended birth details (name, date, time, place, lat/lng, timezone) — do NOT
   invent them. Once provided, INSERT proper public.charts rows (new uuids or the same, native's call),
   then build them through the normal orchestrator (execute_run) like any chart. If the native does not
   want them recreated (they were pure test artifacts), STOP after the delete and report — recreation
   is optional.
DELIVER: pre-delete safety result, per-table deletion counts, and the recreate status (awaiting birth
data / recreated + built). STOP and report.
```

## §4 — PASTE TO CLAUDE CODE — rebuild 1c826d5a (sequenced) + whole-chart proof
```
Rebuild the contaminated chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a cleanly. SAFE chart; never native
482012f1. Prod via execute_run (NOT the local one-off script, NOT a hand-built run). The job image must
carry the ga_positions fix commit (§2.5) — and ideally the AK reckoning fix too, so ga_sensitive is
rebuilt ONCE on correct positions + correct Rāhu reckoning.

SEQUENCE:
  1. Confirm job_image_tag carries the ga_positions fix (and AK fix if ready). If stale, rebuild job
     image first.
  2. Rebuild ga_positions for 1c826d5a via execute_run.
  3. Then rebuild ALL downstream ga_ assets (the 14 suspect assets) in DAG order via execute_run.
  4. Re-verify the Gaṇita layer counts.

WHOLE-CHART verification (not Sun alone — a partial fix must not pass): after rebuild, confirm 1c826d5a
moved OFF the native's values on ALL THREE anchors:
  - SUN  → ~318° Aquarius (was 291.96° Capricorn = native)
  - MOON → OFF Purva Bhadrapada (was the native's 327° PB)
  - LAGNA→ OFF 12.4° Aries (was the native's lagna)
Query chart_facts graha_position for SUN/MOON/LAGNA before claiming success. If any of the three still
shows the native's value, the rebuild did not take — STOP and report.

ALSO: re-run the degenerate-distribution sanity check on a couple of downstream assets (e.g. confirm
ga_dashas/ga_strength didn't collapse to a single value) per the degenerate-distribution-guard memory.

DELIVER: job_image_tag confirmation, per-asset rebuild result, the Gaṇita layer counts, and the
SUN+MOON+LAGNA BEFORE/AFTER proving the whole-chart fix. STOP and report.
```

## §5 — Sequencing summary
1. §2 commit code + job image (bundle AK fix commit if ready).
2. §3 orphans delete (+ recreate when native supplies birth data).
3. §4 rebuild 1c826d5a (ga_positions → 14 downstream) with whole-chart proof.
The AK reckoning rebuild (separate brief) folds into §4's downstream pass — do not rebuild ga_sensitive
twice.

## §6 — Guardrails
- Destructive ops on 1c826d5a + the two named orphans ONLY; never native 482012f1.
- Data plane = prod via :5433; rebuilds via execute_run on the cloud job carrying the fix commit.
- Whole-chart verification (Sun+Moon+Lagna) is the acceptance bar, not Sun alone.
- Orphan recreation needs native-supplied birth data — never fabricate birth params.
