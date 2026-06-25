---
artifact: GA_POSITIONS_CONTAMINATION_BRIEF_v1_0.md
canonical_id: GA_POSITIONS_CONTAMINATION_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
severity: HIGH — chart-identity contamination of L1 facts
purpose: >
  Root-cause + blast-radius + fix for ga_positions writing the NATIVE's planetary positions under
  every non-native chart_id. Found while investigating the ga_sensitive AK divergence on Abhinandan
  1c826d5a (build 26bbbd7c stored Sun=292° Capricorn — the native's Feb-5 Sun — under Abhinandan).
audience: Claude Code (Antigravity)
---

# ga_positions chart-identity contamination — HIGH severity

## §0 — Root cause (Cowork code audit — CONFIRMED, not hypothesis)
`platform/python-sidecar/ga_writers/ga_positions_writer.py`:
```
NATIVE_BIRTH = { "datetime_iso": "1984-02-05T10:43:00", ... }   # ~line 67-68
def build_ga_positions(chart_id: str = CANONICAL_CHART_ID, ..., birth_params=None):  # ~line 431
    ...
    bp = birth_params or NATIVE_BIRTH                            # ~line 458  ← THE BUG
```
The orchestrator adapter `pipeline/orchestrator/writers/ga_positions.py` calls
`build_ga_positions(chart_id=ctx.config['chart_id'], build_id=..., conn=...)` and **never passes
birth_params**. So `bp` always falls back to `NATIVE_BIRTH`. Result: **ga_positions computes the
NATIVE's chart for every chart, then stores those facts under whatever chart_id it was given.** The
`chart_id` default (`= CANONICAL_CHART_ID`) is the same anti-pattern — a native-defaulting signature.

SECOND failure (why nothing caught it): `forensic_gate` (~line 167) asserts Sun=Capricorn,
Moon=Purva Bhadrapada, Lagna=Aries — the NATIVE's anchors, hardcoded. For a non-native chart the gate
passes ONLY because it is checking native anchors against native-computed positions. The gate is
structurally blind to this contamination — it validates it as correct.

## §1 — Why this matters (blast radius)
- ga_positions is foundational: many downstream ga_ assets read graha_position facts. Any non-native
  chart whose downstream assets were built from these facts inherited the native's positions.
- For Abhinandan 1c826d5a, build 26bbbd7c stored Sun=292.06° (sidereal Capricorn = native Feb-5).
  Abhinandan's real Sun (Mar-2 1985) is ~317.9° (Aquarius), proven by the sensitive build 58df4af1,
  which went through execute_run (reads birth params from the charts table) and is authoritative.
- The "fully lit Gaṇita layer" for 1c826d5a is therefore SUSPECT for every asset sourced from
  ga_positions — the sensitive/nakshatra builds that read birth params via execute_run/charts are OK,
  but anything reading the contaminated graha_position facts is not.

## §2 — PASTE TO CLAUDE CODE — PART 1: CONTAINMENT + BLAST RADIUS (read-only first)
```
HIGH-severity chart-identity contamination in ga_positions. Read-only investigation FIRST; do not
write or rebuild until Part 2. Data plane = prod via :5433.

A — NATIVE SAFETY (do this first): confirm the native 482012f1 ga_positions are CORRECT (native params
   are what it should have — the bug only mis-stores for NON-native charts). Verify:
   SELECT fact_subject, fact_key, fact_value FROM chart_facts
     WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_position'
       AND fact_subject='SUN' AND fact_key IN ('longitude_sidereal','sign');
   Expect Sun sidereal Capricorn (~292°). If native is correct, native is SAFE (it coincidentally gets
   the right answer because the writer defaults to its params). Confirm and record.

B — CONFIRM the contamination on 1c826d5a:
   SELECT fact_subject, fact_key, fact_value, build_id FROM chart_facts
     WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a' AND fact_category='graha_position'
       AND fact_subject IN ('SUN','MOON','LAGNA') ORDER BY fact_subject, fact_key;
   If SUN shows ~292° Capricorn (native) instead of ~317.9° Aquarius (Abhinandan) → contaminated.
   Record the build_id (expected 26bbbd7c).

C — ENUMERATE all affected charts: every non-native chart that has graha_position facts is suspect.
   SELECT DISTINCT chart_id FROM chart_facts WHERE fact_category='graha_position'
     AND chart_id <> '482012f1-710e-4a25-994a-93821f5871aa';
   For each, spot-check SUN longitude vs that chart's true birth date. List contaminated chart_ids.
   (Current roster also has Kiran Shenoy cb73cd3d — check it too.)

D — DOWNSTREAM blast radius: list the ga_ assets whose writers read graha_position facts (grep
   ga_writers for 'graha_position' reads + check asset_registry.depends_on edges into ga_positions).
   For each contaminated chart, those downstream assets' rows are also suspect and must be rebuilt
   AFTER ga_positions is fixed + rebuilt.

DELIVER (Part 1): native-safe confirmation, the 1c826d5a contamination proof + build_id, the full list
of contaminated non-native charts, and the downstream-asset rebuild list. STOP and report before Part 2.
```

### Part 1 RESULT (received 2026-06-25) — confirmed
- **Native 482012f1 SAFE** ✓ (Sun ~292° Capricorn, FORENSIC 7/7).
- **Abhinandan 1c826d5a CONTAMINATED** ✗ — Sun 291.96° Capricorn (native's), Moon 327° Purva
  Bhadrapada (native's), Lagna 12.4° Aries (native's); build_id 26bbbd7c. Real Abhinandan Sun ~318°
  Aquarius. All 14 non-root ga_ assets for this chart are suspect.
- **Two ORPHAN charts** 1789595b + b35046d8 — have graha_position rows but NO row in `charts`
  (identical 63.23° Gemini under two build_ids). Cannot be rebuilt (no birth params to fetch) → these
  are a DELETE decision, not a rebuild (see Part 2 step 0).
- Two charts in `charts` never built (cb73cd3d, acdf0d66) — zero rows, unaffected.
- Root bugs confirmed: writer L458 `bp = birth_params or NATIVE_BIRTH`; adapter never passes
  birth_params; forensic_gate only guards the native.

## §3 — PASTE TO CLAUDE CODE — PART 2: FIX (after Part 1 reported + native approves)
```
Fix ga_positions so it builds from the TARGET chart's birth params, never the native default.

0. ORPHAN charts (1789595b, b35046d8) — these have graha_position rows but NO `charts` row, so they
   CANNOT be rebuilt (no birth params to fetch). They are phantom/test artifacts (identical 63.23°
   Gemini under two build_ids). PROPOSED ACTION: DELETE their graha_position rows (and any other
   chart_facts rows under those two chart_ids) since they reference no real chart. This is destructive
   and is GATED ON EXPLICIT NATIVE APPROVAL (brief §5 — not yet ruled). Until the native says "delete
   the orphans", do NOT delete: leave their rows in place and just report them. When approved, before
   deleting, confirm read-only that BOTH chart_ids have zero row in `charts` AND are not referenced by
   asset_throughput/build_runs for any real chart; if either is referenced or appears in `charts`, do
   NOT delete — report and stop. Record row counts deleted.

1. ga_positions_writer.py build_ga_positions:
   - REMOVE the native-defaulting fallbacks. `bp = birth_params or NATIVE_BIRTH` must become: birth
     params are REQUIRED and fetched from the charts table for the given chart_id (birth_date,
     birth_time, birth_place/lat/lon) when not explicitly passed. No silent native fallback.
   - The `chart_id: str = CANONICAL_CHART_ID` default signature should also drop the native default
     (make chart_id required) so a missing chart_id fails loudly, never silently builds the native.
   - Keep NATIVE_BIRTH only if some native-specific test needs it; it must NOT be a runtime fallback.
2. forensic_gate: it currently hardcodes the NATIVE's anchors (Sun=Capricorn etc). It must only run
   those native-anchor assertions when chart_id == the native 482012f1. For non-native charts either
   skip it or assert against that chart's own expected anchors. A gate that validates every chart
   against native anchors is worse than no gate — fix or scope it to the native.
3. Tests: add a regression test that build_ga_positions for a NON-native chart with a different birth
   date produces a DIFFERENT Sun longitude than the native (i.e. it cannot pass when contaminated).
   Run the sidecar position tests green.
4. COMMIT: fix(ga_positions): build from target chart birth params, not native default; scope forensic gate to native
5. REBUILD via execute_run (NOT the local one-off, and NOT a hand-built run) for the contaminated real
   chart 1c826d5a — ga_positions first, then its downstream assets from Part 1.D, in DAG order, on prod
   through the normal orchestrator path. Re-verify the Gaṇita layer counts after.
   SEQUENCING (important — avoids rebuilding ga_sensitive twice): land the AK reckoning code fix
   (GA_SENSITIVE_AK_RECKONING_FIX_BRIEF) BEFORE this downstream rebuild, so ga_sensitive is rebuilt
   once on correct positions AND correct Rāhu reckoning. Order: (a) commit positions fix; (b) commit AK
   reckoning fix; (c) ensure the Cloud Run job image carries BOTH commits (check job_image_tag, rebuild
   job image if stale per BUILD_TRACKER_WRITER_FIXES_PERSIST_BRIEF); (d) ONE downstream rebuild pass.
   WHOLE-CHART verification (not just Sun): after rebuild, confirm 1c826d5a moved OFF the native's
   values on ALL three anchors — Sun → ~318° Aquarius (was 291.96° Capricorn), Moon → OFF Purva
   Bhadrapada (was the native's 327° PB), Lagna → OFF 12.4° Aries. A fix that only moves Sun is a
   partial fix masquerading as success — assert all three.
   Never touch native 482012f1 destructively — it is already correct; do not rebuild it.

DELIVER: the diff, the regression-test result, commit SHA, the orphan-row report (and deletion counts
IF the native approved §5), and the 1c826d5a BEFORE/AFTER for Sun + Moon + Lagna proving the whole-chart
fix. STOP and report.
```

## §5 — Open native decision (gates the orphan step)
The two ORPHAN charts (1789595b, b35046d8) have graha_position rows but no `charts` row. They cannot be
rebuilt. Options: (a) DELETE their rows (recommended — they reference no real chart); (b) leave them and
add a registry-integrity check that flags chart_facts rows whose chart_id has no `charts` row. The
executor must NOT delete until the native picks (a). Until then, orphans are reported, not touched.

## §4 — Guardrails
- Native 482012f1 is already CORRECT (it gets the native params by coincidence of the default). Do NOT
  rebuild or touch it destructively. The fix is for non-native charts.
- This is a B.10 / chart-identity integrity failure — the kind the whole instrument exists to prevent.
  Treat the contaminated downstream rebuild as mandatory, not optional, before any L2+ work trusts
  1c826d5a.
- Hygiene note (not blocking): `run_abhinandan_sensitive_nakshatra.py` hardcodes the DB password in
  plaintext. Move it to an env var / the proxy convention before that script is committed or reused.
