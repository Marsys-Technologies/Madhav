# Lane 1c SERVICES-census — shard-1c-b2 (dasha services)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Chart: 482012f1-710e-4a25-994a-93821f5871aa.
Wire: POST :3000/api/mcp/primitives/<tool>; compute :8000. Probed 2026-07-12.

## Cross-cutting infrastructure facts
- `get_dashas` is **full-pipeline-only** ("Tool not in surgical whitelist") — served-only-by-down-pipeline (LCA-2). NOT reachable surgically. Every named dasha service whose test_spec routes through get_dashas is actually reachable (or not) only via the surgical `query_dasha_periods` primitive.
- `query_dasha_periods` DB ground truth (chart_dashas, this chart), system_id → rows:
  ashtottari 32960 · chara_karaka 155135 · kalachakra 35265 · mudda 102373 · naisargika 21945 · vimshottari 45882 · vimshottari_kp 5760 · yogini 83740.
  **No narayana, no shoola rows** — DATA-PLANE non-existence confirmed (matches get_dashas.ts "never landed" comment).
- Default window is cap<=3, 2021-07-11..2031-07-11 (audit-date-relative ±10y), fields=compact.

## SILENT-FALLBACK DEFECTS (cross-cutting, affect multiple services)
1. **Unknown `system` value → silent `facets_applied.system:"all"` dump.** `system:"narayana"` and `system:"shoola"` both return ok:true with facets_applied.system="all" and rows beginning with ashtottari — NO error, NO warning that the requested system does not exist. A consuming LLM asking for narayana/shoola receives a mixed all-systems dump it will mistake for the requested schedule. Class 5 DISHONEST + class 6 UNUSABLE; masks a class-1 UNREACHABLE-BY-NONEXISTENCE data gap.
2. **Wrong param name `system_id` silently ignored → returns vimshottari default.** `{"system_id":"kalachakra"}` → invocation_params echoes `system_id:kalachakra` back (looks honored) but facets_applied.system=vimshottari and rows are vimshottari. A caller using the natural `system_id` key (the DB column name!) gets vimshottari for ANY requested system, silently. Class 2 WRONG + class 5 DISHONEST. High severity — the payload lies about what it served.

## Per-service verdicts

### 1. Ashtottari — REACHABLE / USABLE (PASS)
`query_dasha_periods {system:"ashtottari"}` → ok:true, facets.system=ashtottari, L1 Mercury MD 2013-02-04→2030-02-04, two_pass_verified, citation_ref present. DB 32960 rows. Self-describing, synthesizable. get_dashas path is full-pipeline-only but surgical primitive serves it fully. compute_reachable: true. GRADE: PASS.

### 2. Chara (Jaimini) — DEAD named endpoints / data reachable via generic (FAIL for named service)
- Dedicated surgical tools `jaimini_chara_dasha` AND `jaimini_chara_dasha_full`: both "Retrieval tool not found in registry" = **DEAD-19 (LCA-1)** — in surgical whitelist but TOOL_NAME_TO_URI missing. Class 1 UNREACHABLE (retrieval plane, registry misconfig).
- :8000 compute `/jaimini_drishti/chara_dasha` and `/chara_dasha/full`: routed (exist in openapi) but **broken** — "[EXTERNAL_COMPUTATION_REQUIRED] ... DATABASE_URL not set. Refusing to substitute fallback longitudes (M-8 fix)." Compute service cannot reach DB; correctly refuses to fabricate (B.10-compliant) but is non-functional.
- Generic `query_dasha_periods {system:"chara_karaka"}` → ok:true, 155135 rows, level_1 lord "Cancer" (rashi-based, lord_sign null as expected for rashi dasha). Data IS reachable this way.
- Net: the two NAMED chara services (dedicated MCP tools + dedicated compute endpoints) are all non-functional; data only reachable via the generic dasha primitive under a different tool name not implied by the chara service description → class 9 UNGOVERNED JUDGMENT (undocumented substitute path). compute_reachable: true (generic only). GRADE: FAIL (named service).

### 3. Narayana — UNREACHABLE-BY-NONEXISTENCE (FAIL)
Never landed in chart_dashas (0 rows; confirmed via group-by). Only reachable path per test_spec is offline CLI compute_narayana.py (not a served surface). `query_dasha_periods {system:"narayana"}` silently returns "all" dump (see defect 1). Class 1 UNREACHABLE-BY-NONEXISTENCE (data plane) + class 5 (masking). compute_reachable: false. GRADE: FAIL.

### 4. Shoola (Niryana Shoola) — UNREACHABLE-BY-NONEXISTENCE (FAIL)
L0 catalog/metadata entry only (canonical_id niryana_shoola); never landed in chart_dashas (0 rows). Silent "all" fallback as with narayana. Class 1 UNREACHABLE-BY-NONEXISTENCE + class 5. compute_reachable: false. GRADE: FAIL.

### 5. Kalachakra — REACHABLE / USABLE (PASS)
`query_dasha_periods {system:"kalachakra"}` → ok:true, facets.system=kalachakra, L1 lord "Sagittarius" (rashi/pada-based, lord_sign null — expected), start 2015-06-03. DB 35265 rows. Synthesizable. compute_reachable: true. GRADE: PASS.

### 6. Mudda (annual/varshphal) — REACHABLE / USABLE (PASS)
`query_dasha_periods {system:"mudda"}` → ok:true, facets.system=mudda, L1 lord Saturn/Libra 2021-02-04→2022-02-04 (1-yr annual periods, correct for varshphal). DB 102373 rows. Synthesizable. compute_reachable: true. GRADE: PASS.

## Summary
PASS: ashtottari, kalachakra, mudda. FAIL: chara (dead named endpoints), narayana (never landed), shoola (never landed).
Anchor rediscovery: LCA-1 (DEAD-19 jaimini_chara tools), LCA-2 (get_dashas full-pipeline-only) both independently reproduced.
