---
lane: F-69
stream: S3_SATYA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-69/SPEC.md, F-69/DIAGNOSIS.md. No REVIEW_LEADS.md exists in lane dir.
Read source (main-ro):
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` (full, 153 lines)
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts` (full, 150 lines)
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` lines 200-320, 355-435, 495-519
- `platform-mcp/src/tools/register_p1_synthesis.ts` lines 520-590
- `platform/python-sidecar/services/ka_kshetra/stage8_spec.py` lines 128-140 (P3-b precedent)

No code run (TypeScript unit; traced line-by-line against current source).

## Q1 — Mechanism vs. symptom

The spec addresses the mechanism: `query_insights.ts:138` returns `insight_units: insightResult.rows` with zero transform — confirmed in source. The fix is applied at the serving boundary (the exact point where raw DB rows become MCP response payload), mirroring ka_kshetra/stage8_spec.py:136's precedent of suppressing at the shape-assembly boundary. Not a disclosure-only flag. Mechanism addressed.

## Q2 — Every D-2 sub-claim mapped to a spec element

| Sub-claim | Spec element | Verified |
|---|---|---|
| C1: envelope declares non-calibrated | Correctly noted as already correct (register_p1_synthesis.ts:578-580 confirmed) | Yes |
| C2: verdict_object evidence_grade permanently 'structural' | Correctly framed as current reality the serve layer must respond to; addressed by §2a predicate | Yes |
| C3: retrodiction evidence_grade honestly conditional (n>=5) | Preserved by per-row predicate; third exit test case guards this differential | Yes |
| C4: full numerics served despite C1-C3, no suppression | §2a (query_insights.ts suppression map) + §2b (sibling fix) + §3 exit test | Yes |
| load_bearing sibling (DIAGNOSIS §4, line 247) | Covered by generic predicate at serve boundary, §4 table row 1 | Yes |

All D-2 sub-claims map. No unmapped claim found.

## Q3 — Exit test would genuinely fail on today's code

Line-by-line trace:
1. Test mocks `query` → returns `[row({ evidence_grade: 'structural', rank_consequence: 0.88, ... })]`
2. `queryInsightsCapability.handler` calls `query(sql, params)` → mock returns that row
3. Returns `{ content: { insight_units: insightResult.rows, ... } }` — source line 138, no transform
4. `unit.rank_consequence` = 0.88 (not null)
5. `expect(unit.rank_consequence).toBeNull()` → **RED** (0.88 ≠ null)
6. Similarly `confidence_band` and `provenance_chain.grade` stay non-null → second assertion also **RED**

First two test cases fail on current code as spec claims. Third case (evidence_grade=empirical) passes today by accident (no transform touches it) — correct.

## Q4 — Sibling sites covered or excluded with stated reason

- `load_bearing` (mi_darshana.py:247, 'structural' hardcode): covered by generic serving predicate (§4) — verified line 247 is 'structural' ✓
- `verdict_object` lines 366, 509 (both 'structural' hardcode): primary targets — verified ✓
- `emergent_law`/retrodiction line 215 (honestly conditional): preserved, not broken — verified ✓
- `calibrated_outlook` line 117 (reads real DB column): covered/no-op, correctly not a defect — verified ✓
- `manifestation_grammar` line 184 (hardcoded 'empirical' but SQL-filtered): covered/no-op — verified ✓
- `query_insight_embeddings.ts` mode=nearest: new sibling found by spec, covered in §2b — verified: SQL at lines 116-126 selects `u.rank_consequence` with no `evidence_grade` and no suppression; `result.rows` returned raw at lines 128-141 ✓
- `mi_sambandha.py`, `mi_pramana.py`: excluded — different tables, different MCP surfaces; DIAGNOSIS confirmed these use bound SQL parameters not hardcoded literals ✓
- MC-010 (register_p1_synthesis.ts:419,440,456,487): excluded — different consumer path (verdict_summary/bodha_domain_reading_get), different function; spec never opens mi_darshana.py ✓

All sibling sites covered or excluded with stated reasons.

## Q5 — Recurrence guard

Exit test (§3) is co-located with the fix in Vitest suite. It directly asserts that `rank_consequence` is null when `evidence_grade='structural'` and `evidence_grade='prior_only'`. Any future edit to `query_insights.ts` that removes or bypasses the suppression map fails test cases 1 and 2 immediately. This detects the actual defect class (serving a numeric under non-empirical evidence_grade), not a weak proxy. Adequate.

## Q7 — Unverified assumptions / file:line citations

All key citations verified against main-ro source:
- `query_insights.ts:138` (`insight_units: insightResult.rows`): VERIFIED — line 138 is exactly this, no transform ✓
- `query_insights.ts` lines 127-144 (try block / handler body): VERIFIED — lines 127-151 ✓
- `query_insight_embeddings.ts` lines 116-127 (mode=nearest SQL): VERIFIED — SQL at lines 116-126, `query()` call at line 127, `rank_consequence` in SELECT, no `evidence_grade`, raw `result.rows` returned at line 133 ✓
- `mi_darshana.py:215`: VERIFIED — `"empirical" if n >= 5 else "prior_only"` ✓
- `mi_darshana.py:247`: VERIFIED — `"structural"` literal for load_bearing rows ✓
- `mi_darshana.py:366`: VERIFIED — `"structural"` literal for verdict_object no_evidence branch ✓
- `mi_darshana.py:509`: VERIFIED — `"structural"` literal for verdict_object main branch ✓
- `register_p1_synthesis.ts:570`: VERIFIED — `callRegistryCapability('marsys://tool/L5/query_insights', ...)` ✓
- `register_p1_synthesis.ts:578-580` (calibration_status/mode/note wrap): VERIFIED ✓
- `stage8_spec.py:136` (P3-b precedent, baseline_is_synthetic suppression): VERIFIED — `"expected_count": None if window.get("baseline_is_synthetic") else float(window["expected_count"])` ✓
- `register_p1_synthesis.ts` trimTopEvidence helper reading `provenance_chain.ranked_evidence[].salience` (lines 508-538): VERIFIED — function at lines 520-539 reads `.salience` from ranked_evidence; nulling whole provenance_chain would break it; spec correctly nulls only `.grade` sub-key ✓

Minor: DIAGNOSIS.md cited the `wrapped =` block at 'lines 559-564' but actual source places it at lines 577-582. This is a DIAGNOSIS line-number error (~17 lines off); the content is correct and the SPEC's own citation (`:570`) is accurate. No spec element rests on the wrong line number.

writer_asset / data_delta / RS-A: Not applicable — spec is a pure read-boundary change; no writer opened, no DB rows mutated, no rebuild required. Correctly omitted.

## Named deficiencies

None.

## Verdict: COMPLETE
