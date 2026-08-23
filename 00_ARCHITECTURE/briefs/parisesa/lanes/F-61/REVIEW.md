---
lane: F-61
stream: S5_MULA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-61/SPEC.md, F-61/DIAGNOSIS.md, F-61/repro_raw.json (present), no REVIEW_LEADS.md.
Verified source at /Users/Dev/par-night/main-ro/platform/python-sidecar/ga_writers/ga_structural_writer.py:
- Lines 1425–1448: saptavargaja block — read verbatim, `value_num=None` confirmed at line 1435.
- Lines 1643–1678: `_build_vimsopaka_ext_rows` function — read verbatim, `value_num=None` confirmed at line 1664.
- Lines 1683–1706: `_get_divisional_constituent_ids` helper — read verbatim, returns only IDs (no values).
- Line 1707+: no `_get_divisional_values` function present (grep returned no matches — confirmed absent).
Exit test file `__tests__/test_ga_structural_saptavargaja_aggregate.py` does not exist (glob confirmed).
Stream derived from CL02_CENSUS.md: F-61 is listed in S5 MŪLA group (F-04, F-05, F-22, F-61, F-70).

## Q1 — Mechanism vs. symptom

COMPLETE. SPEC §1 and §2 address the mechanism directly: `_build_shadbala_extension_rows` hardcodes `value_num=None` (line 1435) and `_build_vimsopaka_ext_rows` does the same (line 1664); the aggregation step promised by both `fact_key` names (`saptavargaja_score`, `vimsopaka_total`) was never written. The fix adds a new helper `_get_divisional_values` that fetches both UUIDs and `fact_value_num` values and returns their sum, then replaces the two call sites. This is mechanism-level, not symptom-level.

## Q2 — Diagnosis sub-claims mapped

All diagnosis sub-claims map to spec elements (verified against §7 Coverage Table):
- (a) null fact_value_num/fact_value_text for every graha/ayanamsha → §2 Changes 2+3 set `value_num=saptavargaja_total`/`vimsopaka_total`.
- (b) jsonb key named `constituent_fact_ids` holds `chart_divisionals.id` values (naming mismatch) → §2 Changes 2+3 rename to `constituent_divisional_ids`.
- (c) per-varga values correct, SUN sum=93.75 → §3 exit test asserts `total == 93.75` using the exact 6 values.
- (d) no MCP path resolves the raw `chart_divisionals.id` pointers → §2 removes the broken pointer pattern entirely, replaces with scalar.
- Sibling `vimsopaka_bala_per_graha.vimsopaka_total` same null defect → §2 Change 3 + §4 explicit coverage.
- §N.8 Earned-Signal: `saptavargaja_score` / `vimsopaka_total` labels unearned → §2 Changes 2+3 write the aggregation code path.
- `graha_in_house_composite_strength.bphs_weighted` checked-not-affected → §4 excluded with reason (correctly implemented).
- GA3 vimsopaka categories flagged-not-ruled-out → §4 excluded with written reason (not confirmed defective).

No unmapped sub-claims.

## Q3 — Exit test genuinely fails on current code

Traced line-by-line against current source:

1. `test_get_divisional_values_returns_ids_and_sum`: calls `sut._get_divisional_values(...)` — function absent in current source (grep confirmed no matches) → `AttributeError` → FAIL on current code. ✓

2. `test_get_divisional_values_vimsopaka`: same absent helper → `AttributeError` → FAIL. ✓

3. `test_no_hardcoded_value_num_none_in_saptavargaja_block`: `inspect.getsource(_build_shadbala_extension_rows)` captures source including line 1433 (`"graha_saptavargaja_bala_component"`) and line 1435 (`value_num=None`). `sapta_start` finds the string; `sapta_block` starts there and includes `value_num=None`. Assertion `"value_num=None" not in sapta_block` → FAIL. ✓

4. `test_no_hardcoded_value_num_none_in_vimsopaka_block`: `inspect.getsource(_build_vimsopaka_ext_rows)` includes line 1664 (`value_num=None`). Assertion fails → FAIL. ✓

After fix: helper exists and returns `(ids, 93.75)` / `(ids, 5.0)` from fake cursor; `value_num=saptavargaja_total` / `value_num=vimsopaka_total` replaces hardcoded None; all 4 assertions pass. ✓

## Q4 — Sibling sites

Two confirmed defect sites, both covered:
1. `graha_saptavargaja_bala_component.saptavargaja_score` — `_build_shadbala_extension_rows` line 1425–1448 (primary). Fixed by Change 2.
2. `vimsopaka_bala_per_graha.vimsopaka_total` — `_build_vimsopaka_ext_rows` lines 1658–1677 (confirmed sibling, live-reproduced in diagnosis). Fixed by Change 3.

Exclusions with stated reasons:
- `graha_in_house_composite_strength.bphs_weighted`: excluded — diagnosis confirmed correctly implemented (uses real `chart_facts.fact_id` via `_load_shadbala_and_bhava_fact_ids`). Source verified: this function correctly computes a real weighted value.
- GA3-level vimsopaka categories (`graha_vimsopaka_dasavarga/shadvarga/shodasavarga`): excluded — diagnosis itself flags these as "not checked in this pass, flagged not ruled out" and "appeared with populated fact_value_num in earlier exploration"; SPEC correctly excludes with matching reason (not confirmed defective).

## Q5 — Recurrence guard

Substantive. Tests 3 and 4 use `inspect.getsource` to assert the literal string `"value_num=None"` is absent from both builder blocks. This detects the exact defect class (hardcoded null in aggregate-score slots), not a weak proxy. A future revert to either call site would immediately fail these tests in CI. The return-type annotation `tuple[list[str], float | None]` and the docstring on `_get_divisional_values` stating "Replaces `_get_divisional_constituent_ids` calls in aggregate-score blocks" make the intent auditable.

Note: test 3 uses a substring-search approach starting from `graha_saptavargaja_bala_component` within `_build_shadbala_extension_rows`. This correctly scopes the check to the aggregate-score block and avoids false positives from other `value_num=None` usages elsewhere in the same function.

## Q7 — Unverified citations

All `file:line` citations verified against `/Users/Dev/par-night/main-ro`:
- `ga_structural_writer.py` lines 1425–1448 (saptavargaja block): VERIFIED — exact code quoted in SPEC/DIAGNOSIS matches source. `value_num=None` at line 1435.
- `ga_structural_writer.py` lines 1643–1678 (`_build_vimsopaka_ext_rows`): VERIFIED — function boundary confirmed, `value_num=None` at line 1664, docstring claiming aggregation at line 1652 confirmed.
- `ga_structural_writer.py` lines 1683–1706 (`_get_divisional_constituent_ids`): VERIFIED — function exists, returns only `id` UUIDs, no `fact_value_num`.
- "insert near line 1707, after `_get_divisional_constituent_ids`": VERIFIED — line 1706 is the last line of `_get_divisional_constituent_ids`; line 1707 begins a blank line before `_real_fact_id_ref`. Insertion point accurate.
- SUN saptavargaja sum 93.75: VERIFIED by arithmetic on the 6 diagnosis values (7.5+30.0+3.75+22.5+7.5+22.5=93.75). ✓
- `writer_asset: ga_structural`: VERIFIED — `ga_structural_writer.py` is the sole file changed.
- `data_delta: narrow`: VERIFIED — exactly 2 fact categories, existing rows updated (null→scalar), no schema change, no new rows. Consistent with PROTOCOL Level-1 `light` asset scoping for G1.

Minor citation variance (not a deficiency): DIAGNOSIS cites `_build_vimsopaka_ext_rows` function boundary as 1643–1678; SPEC cites inner loop body as 1658–1677. Both point to the same code; the difference is function vs. loop-body granularity. No impact on fix correctness.

## writer_asset / data_delta accuracy

`writer_asset: ga_structural` — confirmed, matches `ga_structural_writer.py` (rebuild group G1 per PROTOCOL). Note: PROTOCOL's G1 seed entry cites only F-62, but F-61 touches the same asset; conductor should add F-61 to G1 for the level-1 rebuild gate. SPEC correctly states shadow run required (PROTOCOL Level-0 mandate for writer-layer lanes).

`data_delta: narrow` — confirmed correct. ~90 rows, null→scalar transition only, no new rows, no schema change.

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE

All line citations verified. Mechanism addressed (not symptom). Exit test fails on all 4 assertions against current source, passes after fix. Both confirmed sibling sites covered; all exclusions carry stated reasons matching diagnosis. Recurrence guard is substantive source-inspection, not proxy. No unverified assumptions found. `writer_asset`/`data_delta` accurate.
