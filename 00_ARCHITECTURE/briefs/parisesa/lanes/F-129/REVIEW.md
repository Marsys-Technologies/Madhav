---
lane: F-129
stream: S4-VACA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-129/SPEC.md, F-129/DIAGNOSIS.md (no REVIEW_LEADS.md present).
Source verified against `/Users/Dev/par-night/main-ro`:
- `register_p1_synthesis.ts` lines 814–868 (defect site + assignment)
- `bo_anveshana.py` lines 377–433 (`_make_discovery`), 490–510, 562–590, 607–648 (`surface=` templates)
- `query_discoveries.ts` lines 100–200 (sibling reference pattern)
- `query_mechanisms.ts` lines 138–157 (second sibling)

Exit test traced line-by-line against current source (pure source-inspection test — no DB required).

## Q1-Q5, Q7

**Q1 — Mechanism vs symptom:** MECHANISM. §1 and §2 identify that `surface_reading` is `bo_anveshana.py`'s internal epistemic-pair label (stored to `bodha_discoveries.surface_reading` via `_make_discovery` at line 415), never designed as user-facing prose. The spec targets the query-authoring defect — wrong column selected and aliased to `statement` — not merely the symptom (bad output strings). Mechanism-level.

**Q2 — Diagnosis claim coverage:** All 9 sub-claims map to spec elements (§7 coverage table is complete):
- (a) raw signal_type_id tokens in statement → §2 removes `surface_reading AS statement` + §3 asserts absence
- (b) 20 rows collapse to 5 template shapes → §2 selects `hypothesis_text` (domain-qualified per bo_anveshana.py:502,641)
- (c) synth_chart_brief_get / top_discoveries target → §2 fixes `discResult` query specifically
- Mechanism (surface/depth epistemic pair) → §1 root-cause + §2 "Why"
- Richer fields already in same DB row → §2 fix selects them + §6 no rebuild needed
- query_discoveries.ts reference pattern → §2 diff mirrors it
- Sibling count 0 → §4 full census table, no exclusions
- F-135 disjoint in same file → §6 dependencies
- Narrow fix, no migration, no rebuild → §6

**Q3 — Exit test genuinely fails today:** YES — traced line-by-line against main-ro.
- Test 1: `expect(src).not.toMatch(/surface_reading\s+AS\s+statement/i)` — line 816 contains exactly `surface_reading AS statement` → `.not.toMatch()` FAILS (red).
- Test 2: Anchor regex `const discLimit[\s\S]{0,1000}LIMIT \$2[\s\S]{0,60}`, [chart_id` — `const discLimit` appears exactly once (line 814); block is ~350 chars to `LIMIT $2`; suffix `\n        `, [chart_id` is ~21 chars (within 60-char bound). Block is matched but does NOT contain `hypothesis_text` (SELECT only has `surface_reading AS statement`, `affected_domains_array AS domains`, `composite_discovery_rank AS salience_score`) → `toMatch(/hypothesis_text/)` FAILS (red).
- Test 3 (recurrence guard): `expect(src).not.toMatch(/\b\w+_reading\s+AS\s+statement\b/i)` — line 816 matches pattern → FAILS (red).
All three `it()` blocks are red on today's code. After fix, none of the three defect conditions hold.

**Q4 — Sibling coverage:** COMPLETE. Two siblings found by diagnosis; both verified against main-ro:
1. `query_discoveries.ts:110–114` — verified: selects `surface_reading`, `depth_reading`, `surface_depth_delta`, `hypothesis_text`, `why_an_acharya_misses_it` each under its own honest column name; no `AS statement` alias anywhere. Confirmed NOT defective — correct reference pattern.
2. `query_mechanisms.ts:144–150` — verified: queries `bodha_mechanisms` (different table with columns `mechanism_id`, `mechanism_name`, `mechanism_class`, `valence`, `citation_human`, etc.). No `surface_reading` column, no `AS statement` alias exists on this table. Confirmed NOT defective — different data schema.
No sibling exclusions without stated reason. Census is complete.

**Q5 — Recurrence guard:** STRONG, fails-closed. The guard (`not.toMatch(/\b\w+_reading\s+AS\s+statement\b/i)`) covers the defect class: any column matching `*_reading` aliased to `statement` in `register_p1_synthesis.ts`, not just `surface_reading`. This is not a weak proxy — it directly catches the structural pattern that caused the defect. Permanent test suite member; any future query authoring that reintroduces the mislabeling pattern fails CI immediately.

**Q7 — Citation accuracy:** ALL verified against main-ro source.
- `register_p1_synthesis.ts:816` — `surface_reading AS statement` confirmed at exactly line 816. ✓
- `register_p1_synthesis.ts:868` — `top_discoveries: discResult.rows` confirmed at exactly line 868. ✓
- `bo_anveshana.py:499` — `surface=f"Signal {cand['signal_type_id']} with low visibility (salience {cand['surface_salience']:.3f})"` confirmed. ✓
- `bo_anveshana.py:575` — `surface=f"Signal {sig_info['signal_type_id']} appears unremarkable to pattern inspection"` confirmed. ✓
- `bo_anveshana.py:638` — `surface=f"Appears as one of many {anom['signal_type_class']} signals"` confirmed. ✓
- `bo_anveshana.py:415` — `"surface_reading": surface` in `_make_discovery` return dict confirmed. ✓
- `bo_anveshana.py:418` — `"hypothesis_text": hypothesis` confirmed. ✓
- `bo_anveshana.py:502,641` — hypothesis text templates confirmed at those exact lines. ✓
- `query_discoveries.ts:110–114` — honest-field SELECT (surface_reading, depth_reading, hypothesis_text, why_an_acharya_misses_it) confirmed. ✓
- `query_mechanisms.ts:144–150` — different table/schema confirmed. ✓

No `writer_asset`, `data_delta`, or RS-A entries to validate (serving-layer TypeScript change only; §6 confirms data already correct in DB, no rebuild required).

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE
