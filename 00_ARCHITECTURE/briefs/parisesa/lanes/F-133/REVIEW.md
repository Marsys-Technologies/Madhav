---
lane: F-133
stream: S5 MULA
stage: R (REVIEW) — draft, pending ratification
reviewer: DRAFT
verdict: PENDING
drafted_by: pool-3
draft_verdict: COMPLETE
---

## Method

Read: PROTOCOL.md, F-133/SPEC.md (status: REVISED, cycle 3), F-133/DIAGNOSIS.md, existing REVIEW.md (pool-1, prior INCOMPLETE-RETURN citing D1). No REVIEW_LEADS.md present. Verified all cited source locations against main-ro:
- `mitigation.py:700-706` — confirmed exact signature (no `date_range` param)
- `mitigation.py:780-781` — confirmed `window_start`/`window_end` in SELECT, no WHERE predicate
- `mitigation.py:833-848` — confirmed `provenance_envelope` dict, no `date_range_filter_applied` field
- `outlook.py:142-144` — confirmed `_fetch_mitigations(chart_id: str)`, no `date_range` arg
- `outlook.py:161` — confirmed `mitigation_map(conn, chart_id)` with no `date_range`
- `outlook.py:428-431` — confirmed `date_range` dict computed from `horizon_months`
- `outlook.py:439` — confirmed `_fetch_mitigations(chart_id)` call site, no `date_range` passed
- `phala_outlook.ts:59` — confirmed `recover: { instrument: 'bodha_remedies_get', hint: 'full mitigation/remedy list' }` (explicit section, does NOT use `autoDetectTrimmableSections`)
- `register_p1_aliases.ts:1800` — confirmed `dualOutput(data, 'phala_outlook_get')` (alias uses `autoDetectTrimmableSections` fallback)
- `response_budget.ts:527` — confirmed old hint text: `call ${toolName} again with a narrower filter/date_range, or a smaller top_k/limit, to reach the rest of "${path}"` (F-09 not yet merged in main-ro)

Traced exit tests against current source to verify RED behavior.

## Q1 — Mechanism vs symptom

PASS. Spec correctly identifies the structural mechanism: `date_range` is absent from `mitigation_map()`'s parameter list entirely (not unthreaded at the call site — also unfixable there until the function signature gains the parameter). Fix prescribes adding the parameter, the SQL interval-overlap predicate (mirroring `anchors.py`), and threading `date_range` through `_fetch_mitigations()` and its call site. End-to-end call chain addressed.

## Q2 — Diagnosis claims map to spec elements

All DIAGNOSIS claims map to SPEC elements. Coverage table §7 is complete:
- §1 live repro 8/10 outside horizon → exit test §3 (fabricated rows, same overlap logic) ✓
- §2a anchors correctly scoped → excluded, no code change ✓
- §2b mitigations NOT horizon-scoped → §2a: param + SQL WHERE overlap predicate ✓
- §2c row predates native birth by 17.8 years → OUT1 (window_end 1968-09-21) asserted absent ✓
- §2d no disclosure (PH-4-2) → §2a item 3: `date_range_filter_applied` + `date_range` added to `provenance_envelope` ✓
- §2d misleading trim_report hint → post-fix: `date_range` IS applied, hint becomes accurate; no Python edit needed; F-09 separately addresses schema-neutral language; MUST NOT touch `response_budget.ts` ✓
- §3 mechanism `_fetch_mitigations` missing arg → §2b items 1–3 ✓
- §3 mechanism `mitigation_map` no param, no predicate → §2a items 1–3 ✓
- §4 all siblings (5 sites) → §4 table with stated exclusion reasons ✓
- §5 S5 alias verified clean → files_to_change are Python sidecar only, no TS alias change ✓
- `response_budget.ts:527` hint → excluded; no edit needed; delegated to F-09 ✓

Prior D1 deficiency ("§2b item 4 directs builder to edit hint text in Python files") is resolved: revised §2b item 4 now explicitly states no hint-text edit is required in any Python file, explains why the hint becomes accurate post-fix, and instructs builder MUST NOT touch `response_budget.ts`.

## Q3 — Exit test fails on current code

CONFIRMED by source trace.

`test_mitigation_map_filters_by_date_range`: calls `mitigation_map(mock_conn, 'fake-chart-id', date_range={...})`. Current `mitigation.py:700-706` signature has `anchor_id`, `mitigation_type`, `limit` but NO `date_range` → `TypeError: mitigation_map() got an unexpected keyword argument 'date_range'`. RED ✓

`test_mitigation_map_no_date_range_returns_all`: calls `mitigation_map(mock_conn, 'fake-chart-id')` then asserts `result['provenance_envelope']['date_range_filter_applied'] is False`. Current provenance_envelope (lines 833-848) has no `date_range_filter_applied` field → `KeyError`. RED ✓

`test_mitigation_map_has_date_range_param` (recurrence guard): `inspect.signature(mitigation_map)` — `date_range` not in current params → `AssertionError`. RED ✓

Note: Tests use mocks — SQL predicate logic not independently executed. Shadow run (Level-0) covers live probe. Acceptable per PROTOCOL.

## Q4 — Sibling sites

All sibling sites from DIAGNOSIS §4 present in SPEC §4 with stated exclusion reasons:
- `query_phala_calibration.ts` — same table, same defect shape; bundled with F-08 per PAR-F-08-NEEDS-LEASE precedent; PAR-F-133-SIBLING-TO-F-08 flag raised ✓
- `query_prospective_ledger.ts` — different table, not live-reproduced; flagged for future CL-03 census ✓
- `query_predictive_anchors.ts` — different defect shape (categorical tier, not absent predicate) ✓
- PH-4-4 `_fetch_auspicious_windows` — confirmed correctly windowed in source; excluded ✓
- `muhurta.py::fetch_muhurta_windows` — caller validates `date_range` before query; excluded ✓

## Q5 — Recurrence guard

PASS. `test_mitigation_map_has_date_range_param` uses `inspect.signature` to assert `date_range` is in `mitigation_map()`'s declared parameters. Directly detects the exact defect class (structural parameter absence). Fail-closed: removing the parameter immediately breaks CI. Strong guard.

## Q7 — Citation accuracy / unverified assumptions

All cited file:line references verified against main-ro current source:
- `mitigation.py:700-706` — CONFIRMED signature exactly as quoted ✓
- `mitigation.py:780-781` — CONFIRMED `window_start`, `window_end` in SELECT, no WHERE predicate ✓
- `mitigation.py:833-848` — CONFIRMED `provenance_envelope` dict, no `date_range_filter_applied` ✓
- `outlook.py:142-170` — CONFIRMED `_fetch_mitigations(chart_id: str)`, bare `mitigation_map(conn, chart_id)` at 161 ✓
- `outlook.py:428-431` — CONFIRMED `date_range` dict computed from `horizon_months` ✓
- `outlook.py:439` — CONFIRMED `_fetch_mitigations(chart_id)`, no `date_range` ✓
- `phala_outlook.ts:59` — CONFIRMED `hint: 'full mitigation/remedy list'` (explicit section, no `date_range`) ✓
- `register_p1_aliases.ts:1800` — CONFIRMED `dualOutput(data, 'phala_outlook_get')` (alias path uses `autoDetectTrimmableSections`) ✓
- `response_budget.ts:527` — CONFIRMED old hint text mentioning `date_range` (F-09 pending merge) ✓
- "No DB migration" claim — CONFIRMED (`window_start`/`window_end` already selected columns on current table) ✓
- `rs_class: RS-B`, `writer_asset: null`, `data_delta: narrow` — CONFIRMED (Python serving layer only, no GA/BO writer, two files only) ✓
- SPEC claim that `outlook.py` and `mitigation.py` contain no `trim_report`/`recover_via`/hint construction — CONFIRMED by source inspection ✓

No unverified assumptions found. All §2d hint-path reasoning is verified: alias uses `dualOutput` → `autoDetectTrimmableSections` → hint at `response_budget.ts:527`; direct-tool path uses explicit sections in `phala_outlook.ts` with non-`date_range` hint. Post-fix the hint becomes accurate for the alias path since `date_range` will indeed be applied.

## Named deficiencies

None. Prior D1 is resolved by the cycle-3 revision.

## Verdict: COMPLETE
