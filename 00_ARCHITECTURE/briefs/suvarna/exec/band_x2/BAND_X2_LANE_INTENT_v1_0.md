---
artifact: BAND_X2_LANE_INTENT
version: "1.2"
status: DRAFT-FOR-REVIEW (SS rulings a-d of 2026-10-02 applied)
produced_by: exec-suvarna (worker lane)
date: 2026-10-02
decision: SS N-62 (decision sheet L1 v1.2): Q-L1-16(c) = Track I I-28; X2 = Track I I-29 (both MANDATORY before S-L1; provisional until J1; (R) items)
branch: suvarna/land/TI-l1-band-x2-001 (from origin/main 925e96a5d)
execution: code + tests + docs on a local branch (draft PR #2890 carries the pushed state; this version is local commits on top, pushed by the coordinator after review). NO migration, NO registry write, NO database write (the database was read as the read-only reader only).
changelog:
  - "1.2 (2026-10-02): SS follow-up: the Sun conjunct of the ga_medical registry clause and the writer's Sun advisory / canonical FORENSIC log are REMOVED too (chart-specific assertions; an integrity clause must be true for any chart); replaced by tests/test_ga_medical_sun_golden.py. Decision recorded: both Saturn and Sun chart-specific assertions are removed from writer and clause; integrity clauses are chart-independent."
  - "1.1 (2026-10-02): SS rulings applied. (a) the ga_medical Saturn FORENSIC guard is REMOVED from the writer (not weakened) and replaced by a golden test; (b) the dasha peak/weak cut points 0.65 / 0.35 moved, values unchanged, into ga_condition_bands.py as the separately named DASHA_PERIOD_CONDITION_CUTS; (c) the ga_medical / ga_vastu registry clause texts are marked migration 1252 (to be written at the owner's line; intent only) with the ordering rule, and the medical clause's Saturn conjunct is removed too; (d) the canonical-scoped fallback clause now states why it is scoped and that it widens in S-L1b. Digests re-generated; E6 pins re-moved; supplementary test groups finished."
  - "1.0 (2026-10-02): first version."
---

# Band table (I-28) and D1-fallback visibility (I-29 / X2): lane intent

Contents: 1 what was ruled · 2 facts found (the duplicated cut points) · 3 design: the band table · 4 design: X2 · 5 files and tests · 6 old-vs-new on the three charts · 7 evidence queries · 8 digests moved · 9 registry changes to apply LATER by migration (exact SQL, dry-run) · 10 consumers · 11 detector coverage and attribution hooks · 12 decisions for SS · 13 Not verified.

## 1. What was ruled

Decision sheet L1 v1.2 (`origin/suvarna/land/A-L1-decisions-001`), all read in full for the parts below:

- **I-28 / Q-L1-16(c)** (mandatory before S-L1): "ONE band table at `ga_condition`, cut points 0.4 / 0.7, read by both writers (`ga_medical`, `ga_vastu`); NULL score = NULL / `unknown`, never `neutral`." The sheet's recommendation adds: "the label vocabularies may differ, the cut points may not"; thresholds are labelled project conventions (`unsourced`); effect: (R) the 15 canonical medical rows (5 on the third chart) between 0.6 and 0.7 move from "mild" to "moderate", vāstu unchanged.
- **I-29 / X2** (mandatory before S-L1; canonical in S-L1, the other two charts in S-L1b): "a D1-fallback row is made visible (served field and Dens facet) and an integrity clause fails a fallback on a chart that has divisionals." Finding F-7: `varga_dignity_composite` NULL and `varga_fallback_used = true` on all 90 rows of two charts.
- Q-L1-17: `ga_condition` is kept "subject to X2". Q-L1-16(a) (tier constants, sibling module `brahmagyan/verification_tiers.py`, PR #2854) is a different lane; this lane emits no tier and does not depend on it.

## 2. Facts found (read-only)

### 2.1 The duplicated cut points, and where they disagree

At `origin/main` 925e96a5d, over the SAME `ga_condition_composite.condition_score`:

| writer | code | < 0.4 | 0.4 to 0.6 | 0.6 to 0.7 | >= 0.7 | NULL |
|---|---|---|---|---|---|---|
| `ga_vastu_writer.compute_direction_impact` | `< 0.4`, `< 0.7` | weakened | neutral | neutral | strengthened | **'neutral' (invented)** |
| `ga_medical_writer.indication_strength_from_score` | `< 0.4`, `<= 0.6` | strong | moderate | **mild** | mild | 'unknown' |

They disagree on 0.6 to 0.7 (medical "mild" = well-placed, vāstu "neutral" = middle) and on NULL. The label polarity is opposite by design (a LOW score is a "strong" medical indication and a "weakened" vāstu direction); only the cut points are to be shared.

Three further places hold the same numbers, and they are NOT code the writers import:

1. **The registry `integrity_check_sql` of `ga_medical` (migration 740) and `ga_vastu` (migrations 741/924)** each re-derive the label with their own `CASE` over the cut points (`<0.4`, `<=0.6` / `<0.7`, NULL -> `'unknown'` / `'neutral'`) and a Saturn conjunct on the medical clause (`Saturn ... indication_strength <> 'mild'` must not exist). Live text read 2026-10-02 equals the migration text. After this lane's writers run, **both live clauses FAIL** (section 9). SQL cannot import a Python table, so the cut points stay duplicated there; they are handled as a registry change to apply with the writer deploy.
2. `ga_condition_writer._PEAK_CONDITION_THRESHOLD = 0.65` and `_WEAK_CONDITION_THRESHOLD = 0.35` gate which mahadasha periods are stored as peak/weak in `peak_dasha_periods` / `weak_dasha_periods`. A different concept from the three-band label, over the same score. **SS ruling 2026-10-02 (decision b):** moved, values unchanged, into `ga_condition_bands.py` as the SEPARATELY named `DASHA_PERIOD_CONDITION_CUTS` (provenance `unsourced`, a project convention); they do NOT merge into 0.4 / 0.7; `ga_condition_writer` imports them from there (its old module names are kept as aliases). No output change (section 3).
3. L2 `bo_pratijna_v4_engine.OCCURRENCE_BANDS` / `CONDITION_BANDS` and `ph_muhurta` `_STRONG_THRESHOLD = 0.75` are bands over THEIR OWN computed quantities (occurrence 0 to 1, a 0 to 10 affliction scale, a muhūrta score), not over `ga_condition_composite.condition_score`. Not duplicates; no change.

### 2.2 Where `neutral` was invented

Only `ga_vastu_writer.compute_direction_impact(None)` returned `'neutral'` for a NULL score (and the registry clause 741/924 asserted it). `ga_medical` already returned `'unknown'`. Other `neutral` strings in `ga_condition_writer.py` are dignity/friendship vocabulary ("neutral_sign", panchadha) and a lajjitadi context fallback, unrelated to the score. No stored row takes the NULL path today (no `condition_score` is NULL on any of the 135 composite rows), so the fix changes zero stored rows; it removes a latent invention.

### 2.3 A trap the sheet's effect line did not name: the Saturn FORENSIC guard (REMOVED, SS ruling a)

`ga_medical_writer` raised `AssertionError` for the canonical Lahiri build unless Saturn's `indication_strength == 'mild'` (score > 0.6). The measured canonical Saturn scores are **0.6800 / 0.6831 / 0.6915 / 0.6972** (all five ayanamshas below 0.7), i.e. MID band, "moderate", under the ruled table. A literal 0.7 cut with the old guard would **halt every canonical `ga_medical` build** on a number the ruling moved, not on a Saturn regression. **SS ruling (a), 2026-10-02: the guard is REMOVED from the writer entirely** (the first version of this lane had weakened it to "not in the LOW band"; that was rejected, and the weakened form is gone too). Why: a build-halting assertion about one chart's label, inside a writer that runs for every chart, tied to an unsourced cut point, is not a FORENSIC anchor; the seven anchors are positional. What it was protecting is now pinned by a golden test (section 3), so a future change shows in CI rather than as a production halt.

### 2.4 Root cause of the X2 fallback (read-only; the sheet said "not established")

- `ga_condition_composite`: 45 rows each for the three charts; the two fallback charts' composites were written **2026-08-06 04:12-04:16Z (Abhinandan 1c826d5a)** and **2026-07-27 09:02Z (third chart cb73cd3d)**; the canonical composite 2026-09-07 20:31Z.
- `chart_divisionals` for those charts existed BEFORE those writes: created 2026-07-26 06:36Z (1c826d5a) and 2026-07-27 08:39Z (cb73cd3d), 23,542 rows each (read as the reader, RLS now off). `varga_position` / `varga_dignity` rows are present for every graha (1,450 / 1,305 per fallback chart).
- On ALL 90 fallback rows `varga_dignity_spread` is **populated** (non-NULL) while `varga_dignity_composite` is NULL. The spread is built from `chart_divisionals` in the same call, so the divisional rows were visible to the writer at write time. **This is not the 2026-09-18 RLS window** (that began 6 to 7 weeks later) and not an absent table.
- The cause is the **F-C8 defect, fixed 2026-09-06 by PR #1853 (commit 1c102f525)**: `chart_divisionals.dignity` stores Title-Case bare labels ("Enemy"), `DIGNITY_SCORES` was keyed `enemy_sign`, so every per-varga fallback lookup missed and `_compute_varga_composite` returned None on every row of every chart, which made `compute_condition_score_v1` substitute D1 dignity and record `varga_fallback_used = true`. The canonical chart was rebuilt AFTER the fix (2026-09-07: composite non-null, flag false on 45/45); the other two charts were never rebuilt (migration 902's header already says they carry "pre-F-C8-writer output").
- Why nothing caught it: the flag was only a JSON key that nothing read; no code asked "does this chart have divisionals?" (N.8).
- Offline confirmation: re-deriving the composite from the STORED `varga_dignity_spread` with the post-F-C8 writer functions reproduces **45 of 45 canonical stored `condition_score`s exactly** (tolerance 1e-6), so the method is valid; on the two fallback charts it gives scores that differ on all 45 rows each (section 6C).

## 3. Design: the band table (I-28)

- **New module** `platform/python-sidecar/ga_writers/ga_condition_bands.py`, owned by `ga_condition`, imports nothing project-local. It holds: `CUT_LOW_MID = 0.4`, `CUT_MID_HIGH = 0.7`, `SCORE_BANDS` (a frozen tuple of three `ScoreBand` rows low/mid/high, `lower <= score < upper`, contiguous, asserted at import), `BAND_LOW/MID/HIGH`, `BAND_UNKNOWN = "unknown"`, and `score_band(score) -> Optional[str]` (None for NULL / NaN / non-numeric). `score_band` converts with `float()` first: `Decimal('0.4') < 0.4` is True in Python, and `ga_vastu` read the score as a `Decimal`, so a stored 0.4 would have been "weakened"; now it is "neutral" (no stored score is exactly 0.4 or 0.7, so no row is affected; the fix is a latent-bug removal).
- `ga_condition_writer` imports and re-exports the names (`cond.SCORE_BANDS is bands.SCORE_BANDS`), so "the band table is at `ga_condition`" holds as an import path too. `ga_medical_writer` and `ga_vastu_writer` import them and keep ONLY their label maps: `INDICATION_STRENGTH_BY_BAND = {low: strong, mid: moderate, high: mild}`, `DIRECTION_IMPACT_BY_BAND = {low: weakened, mid: neutral, high: strengthened}`. **No stored value is renamed.** NULL: medical `'unknown'` (unchanged), vāstu `'unknown'` (was `'neutral'`); both are a shared constant.
- **Why a new module and not the table inside `ga_condition_writer.py`:** `ga_medical`/`ga_vastu` would otherwise import the whole `ga_condition_writer` (which imports `ga_positions_writer`), widening their digest closure to that closure; and `ga_condition_writer.py` is imported by `ga_dashas_writer` for `_DIVISIONAL_DIGNITY_NORMALIZE`. The new module is imported only by the three writers and edits no L0 module (section 8).
- **Saturn guard REMOVED; golden test instead (SS ruling a).** `saturn_forensic_guard_violation` and the build-halting block are deleted from `ga_medical_writer.py`, and (SS follow-up, same test) so are the non-fatal Sun advisory `sun_forensic_guard_warning` and the whole canonical-chart FORENSIC log block (Sun/Saturn/Moon values at INFO): the writer runs for every chart and now asserts and logs nothing about one chart's values. `tests/test_ga_medical_saturn_golden.py` pins, as FIXTURES (values read with SELECT-only as the read-only reader on 2026-10-02; no live DB in the test): canonical Saturn sign Libra from `chart_facts` `graha_position`/`sign` on all five ayanamshas, `dignity_d1` exalted, `condition_score` 0.683108 (lahiri, true_chitra), 0.691486 (krishnamurti), 0.697162 (raman), 0.680000 (surya_siddhanta_classical); the resulting band under the ruled 0.4 / 0.7 table (MID on all five), the new medical label ('moderate'; the stored pre-lane label was 'mild'), vāstu 'neutral' (unchanged), and that the closest score sits 0.002838 below the 0.7 edge (so any move of the edge, the scores or the band logic fails CI). It also asserts the writer has no `saturn_forensic_guard_violation`, no `FORENSIC VIOLATION` and no `raise AssertionError`. NB the score lives in `ga_condition_composite.condition_score`, not in `chart_facts`; the sign is the `chart_facts` part.
- **Sun assertion REMOVED; golden test instead (SS follow-up).** What the registry conjunct and the writer advisory asserted: for chart 482012f1-..., ayanamsha lahiri_chitrapaksha, graha Sun, `condition_score < 0.4 -> indication_strength 'strong'` (the registry clause FAILED if the stored label differed; the writer only logged an advisory, and logged Sun/Saturn/Moon values with "expected ..." text). `tests/test_ga_medical_sun_golden.py` pins the fixtures read SELECT-only on 2026-10-02: Sun sign Capricorn (`chart_facts` `graha_position`/`sign`, fact_subject SUN, all five ayanamshas), `dignity_d1` `enemy_sign` (NOT debilitated: Sun debilitates in Libra), `condition_score` 0.303784 (lahiri, true_chitra), 0.302703 (krishnamurti), 0.317568 (raman), 0.286622 (surya_siddhanta_classical). **Result, stated rather than assumed: the old claim HOLDS on all five ayanamshas under the ruled 0.4 / 0.7 table**: every Sun score is in the LOW band, medical 'strong' (stored value unchanged by this lane), vāstu 'weakened' (unchanged); the closest score to the 0.4 edge is raman at 0.317568 (0.082432 below), pinned. The test also asserts the writer has no Sun advisory, no `FORENSIC ADVISORY`, and that the clause SQL body contains no chart id, ayanamsha, 'Sun' or 'Saturn' literal. The old F-E5 unit test file (`tests/test_ga_medical_f_e5_sun_forensic_guard.py`, which tested the removed function) is deleted.
- **Dasha peak/weak cut points (SS ruling b).** `DASHA_PERIOD_CONDITION_CUTS` (frozen `DashaPeriodConditionCuts`: `peak_at_or_above = 0.65`, `weak_at_or_below = 0.35`, `provenance = "unsourced"`) lives in `ga_condition_bands.py` beside, and separate from, `SCORE_BANDS`. `ga_condition_writer` imports it; `_PEAK_CONDITION_THRESHOLD` / `_WEAK_CONDITION_THRESHOLD` remain as aliases of it (existing tests import them). No output change, proven by `tests/test_ga_condition_dasha_cuts.py`: over a 0.0005 score sweep plus both edges and NULL, the classification `_load_dasha_periods` produces equals the previous hard-coded 0.65 / 0.35 rule, and the period payloads at the edges are unchanged. It is a different concept from the three-band label and is NOT merged into 0.4 / 0.7 (a test pins that the values are disjoint from the band edges).
- Not changed: the formula, weights, `condition_score` values.

## 4. Design: X2 (I-29)

1. **Stored field.** The flag already exists: `condition_score_breakdown.varga_fallback_used` (true on 90 rows, false on the canonical 45). Added in the same JSON: `varga_fallback_reason = "no_divisionals_for_chart"`, written only when the fallback is used (which, after the guard, means the chart genuinely has no divisional rows). **No new column**: a column needs a migration (forbidden here; follow-up D6).
2. **Served field + Dens facet** (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts`): every row carries top-level `varga_fallback_used` (true / false / **null when the flag is absent**, never coerced to false) and `varga_fallback_reason`; `varga_fallback_used` is a declared input filter and a `density_contract.facets` entry (`['graha','ayanamsha_id','varga_fallback_used']`); the response counts D1-fallback rows separately (`d1_fallback_rows_in_page`, `d1_fallback_total_matching` over the full filtered set, null if the count did not return it) with a `d1_fallback_note` (CLAUDE.md N.6 item 1: never flattened in with divisional-based rows). The empty-reason text names the new filter.
3. **Writer-side guard (the detector).** In `build_ga_condition_substep`, when `compute_condition_score_v1` reports `varga_fallback_used` (a score is actually being computed on D1 alone), `assert_fallback_legitimate` asks the table: `count_visible_divisional_rows(chart, ayanamsha, graha)` over `fact_category IN ('varga_position','varga_dignity')`. Visible rows > 0 raises `VargaFallbackWithDivisionalsError` (this is the F-C8 class: a stored label the composite could not score; also an exception swallowed by `_load_varga_dignity_spread`). Zero rows AND `row_security_active('public.chart_divisionals')` for the build role also raises (an empty read under active RLS proves nothing: the 2026-09-18 incident class). It passes ONLY on a trustworthy "no divisionals" and then stores the visible flag + reason. The guard sits BEFORE the composite DELETE/INSERT, so a refused fallback writes nothing. A failing count query is not swallowed (fail closed).
4. **Verifier side.** `FALLBACK_VIOLATION_PREDICATE_SQL` + `fallback_integrity_violations(conn, chart_id=None)` read the stored rows for the same claim (flag true AND the chart has divisional rows for that (chart, ayanamsha, graha)); the registry clause (section 9) uses the same predicate, byte-identical (a test pins the equality with this document).
5. **Canonical chart impact: none.** The canonical composite already reads divisional dignity on 45/45; the guard never fires there. The two fallback charts (S-L1b) cannot be rebuilt by the writer until their composites can read divisionals; with the fixed writer they will (F-C8 is fixed), and the guard converts any recurrence into a build failure.

## 5. Files and tests

New: `ga_writers/ga_condition_bands.py`; `tests/test_ga_condition_band_table.py` (38 tests after the Saturn-guard tests were removed); `tests/test_ga_condition_band_clause_texts.py` (6 tests, pins the clause texts of section 9); `tests/test_ga_condition_fallback_guard.py` (13 tests); `tests/test_ga_medical_saturn_golden.py` (17 tests, the Saturn golden fixtures); `tests/test_ga_medical_sun_golden.py` (12 tests, the Sun golden fixtures); `tests/test_ga_condition_dasha_cuts.py` (5 tests, the dasha cut table and the no-output-change equality); `exec/s_l1_attribution_hooks/band_table.json`, `ga_condition_fallback.json`; this folder: this document, `band_x2_old_vs_new.py`, `old_vs_new_output_2026-10-02.txt`, `registry_clause_texts/*.sql` (NOT applied).
Edited: `ga_condition_writer.py`, `ga_medical_writer.py`, `ga_vastu_writer.py`; `get_condition_composite.ts` + its test (6 new); `pipeline/orchestrator/writers/__tests__/test_ga_medical.py` (the 0.61 boundary case moves to "moderate"; 0.7 added) and `test_ga_vastu.py` (NULL -> 'unknown'); regenerated `platform/src/generated/nirmana-writer-digests.json`; E6 re-pin of ga_condition line numbers (`asset_declarations.json`, `test_e6_1_declarations.py`, as commit 271290c25 did); census regeneration (section 8).

Golden/boundary coverage: 0.0, 0.3999999, 0.4, 0.4000001, 0.5, 0.6, 0.65, 0.6999999, 0.7, 0.7000001, 1.0, out-of-range, NULL, NaN, non-numeric, `Decimal('0.4')`, `Decimal('0.700000')`, numeric strings; table contiguity on a 0.01 grid (every score in exactly one band); identity `cond.SCORE_BANDS is med.SCORE_BANDS is vas.SCORE_BANDS`; an AST test that neither consumer's executable code contains 0.4 / 0.6 / 0.7; both label maps cover exactly the band names; medical and vastu agree on the band of every score on a 0.001 grid; stored label values unchanged; NULL never 'neutral'. Fallback: guard raises with divisionals present, passes when genuinely absent, refuses an RLS-blind empty read, fails closed on a failing read; the build writes nothing when refused (F-C8-class unscorable label and a swallowed-failure None), flags and reasons when legitimate, never consults the guard when the composite is usable; the verifier returns violators and scopes by chart.

## 6. Old-vs-new on the three charts (offline, read-only; `band_x2_old_vs_new.py`, full output in `old_vs_new_output_2026-10-02.txt`)

Method: SELECT-only dumps (section 7) of `ga_condition_composite`, `ga_medical`, `ga_vastu_planet_direction_map`; the pre-change functions re-implemented in the script; the new functions imported from the writers. **A. Reproduction:** the OLD function over the stored composite score reproduces the stored label on **135/135 medical and 120/120 vāstu rows** (0 mismatches; the vāstu `condition_score` copy equals the composite score on all 120). So "old" is exactly what is stored.

**B. The band table alone (stored scores unchanged), stored -> new:**

| table.column | canonical 482012f1 | Abhinandan 1c826d5a | third cb73cd3d |
|---|---|---|---|
| `ga_medical.indication_strength` (45 rows each) | **15 change, all mild -> moderate** | 0 | **5 change, all mild -> moderate** |
| `ga_vastu_planet_direction_map.direction_impact` (40 rows each, Ketu skipped) | 0 | 0 | 0 |
| rows whose `condition_score` is NULL (the old vāstu 'neutral' path) | 0 | 0 | 0 |

Canonical medical rows that change (the scores 0.6 to 0.7): Saturn x5 (0.6800 surya_siddhanta, 0.6831 lahiri/true_chitra, 0.6915 krishnamurti, 0.6972 raman), Rahu x5 (0.6858 to 0.6980), Ketu x4 (0.6953; none in surya_siddhanta), Jupiter raman x1 (0.6934). Third chart: Venus x5 (0.640 to 0.665). Matches the sheet's "15 canonical, 5 on the third chart". No FORENSIC anchor is touched (anchors are sign / nakshatra / panchanga facts). The `condition_score`, the band names, and every other medical/vāstu column are unchanged.

Canonical stored bands (new table): low 5, mid 35, high 5 (of 45); the 5 canonical rows at 0.7 or above keep "mild" (medical) / "strengthened" (vāstu).

**C. X2 scenario (an OFFLINE REPRODUCTION, not a rebuild result):** re-deriving every composite from its stored `varga_dignity_spread` with the post-F-C8 writer functions:

| chart | composite rows | reproduced equal to stored | score would change |
|---|---|---|---|
| canonical 482012f1 | 45 | **45** | 0 |
| Abhinandan 1c826d5a | 45 | 0 | 45 |
| third cb73cd3d | 45 | 0 | 45 |

For the two fallback charts, bands stored -> re-derived: Abhinandan high 1 -> high, **high 6 -> mid**, low 24 -> low, mid 14 -> mid; third chart low 10 -> low, mid 35 -> mid. Combined effect on stored labels after S-L1b (band table AND X2 together; they cannot be separated by this method): Abhinandan 6 medical rows mild -> moderate and 6 vāstu rows strengthened -> neutral; third chart 5 medical rows mild -> moderate, 0 vāstu. These are inference from stored spreads; the divisional rows could differ at rebuild (and Q-L1-01 widens the `chart_divisionals` key, F-A2).

## 7. Evidence queries (read-only, as the read-only reader; no write)

```sql
-- X2 root cause: when were the composites and the divisionals written; is the spread populated where the composite is NULL
select left(chart_id::text,8), min(computed_at), max(computed_at), count(*) from ga_condition_composite group by 1;
select left(chart_id::text,8), count(*), min(created_at), max(created_at), count(distinct build_id) from chart_divisionals group by 1;
select left(chart_id::text,8), count(*), count(varga_dignity_spread), count(varga_dignity_composite),
       count(*) filter (where condition_score_breakdown->>'varga_fallback_used'='true'), count(*) filter (where condition_score is null)
  from ga_condition_composite group by 1;
select left(chart_id::text,8), fact_category, fact_key, count(*) from chart_divisionals
 where fact_category in ('varga_position','varga_dignity') group by 1,2,3 order by 1,2,3;
select row_security_active('chart_divisionals'), (select count(*) from chart_divisionals);   -- f | 71476
-- dumps for the old-vs-new script (json_agg of): ga_condition_composite (scores, spread, breakdown), ga_medical (indication_strength), ga_vastu_planet_direction_map
-- live registry clauses: select integrity_check_sql from asset_registry where asset_id in ('ga_condition','ga_medical','ga_vastu')
```
Results are quoted in section 2.4 and 6.

## 8. Digests moved; pins; census

`provenance_inventory --output` before vs after (re-run after SS rulings a-d, against both the pristine base and the pushed HEAD 77f7a219a): **3 writer digests moved: `ga_condition`, `ga_medical`, `ga_vastu`** (L1 only). `probe_digest` unchanged; no writer added or removed; **no L0 (`bg_*`), L2 (`bo_*`), L3 (`ka_*`) asset moved**, `verification_vocab.py` and every other L0 module untouched. (Importers of `ga_condition_writer.py`, e.g. `ga_dashas_writer`, did not move: the inventory's closure does not follow them.) `ga_condition` is `asset_frozen` against its live generation (migration 902 note): this change unfreezes it by design; the S-L1 rebuild re-freezes it.

Pins: `platform/src/generated/nirmana-analysis-layer-pins.json` was NOT regenerated: `python -m scripts.generate.nirmana_analysis_layer_pins --check` already reports L1, L2 and L3 slices stale and many "artifact commit must be an ancestor of HEAD" errors in this checkout, including L2 and L3 slices no digest of which moved here; the pin regeneration is a convergence-time step that needs a reviewed commit and a database. E6 declaration line pins for `ga_condition` (citation sites 1117 -> 1250, 1391 -> 1524, column list 1201 -> 1334; served read `get_condition_composite.ts:91 -> 121`) were re-pinned; the AST site counts did not change.

Generated artifacts (second commit of the branch): `npm run codegen:capability-estate-census:check` demanded regeneration (writer-digest inventory hash, `get_condition_composite` descriptor), done with `--generated-at=2026-10-01T23:25:07.000Z` (the UTC time of the first code commit) and `--source-revision=18a95a75cdb60b297429cdca3aef1bcbdaed5e20` (that code commit); the diff is the new `varga_fallback_used` input in the census plus four source sha256s. `npm run codegen:capability-knowledge:check` also went stale (new input and description of the tool) and was regenerated with the same `--generated-at` (`content_hash sha256:0cbfae11...`, 182 SCUs; the diff is the tool description, the new optional input, and the two hashes). The vidhi and signal-glossary mirror checks were already current. After the SS-rulings commit (7f9f8541f1c879e6b8a2c01c73715dbd198f502c) the census went stale again (digest inventory hash) and was regenerated with `--generated-at=2026-10-01T23:51:10.000Z --source-revision=7f9f8541f1c879e6b8a2c01c73715dbd198f502c`; the knowledge snapshot stayed current. Re-check after regeneration: all four `:check` commands OK; `vitest run src/lib/retrieval/registry src/generated` 2253 passed, `vitest run tests/unit` 1598 passed.

## 9. Registry changes to apply LATER by migration (NOT applied; no migration in this branch)

**Migration number 1252 is allocated for these clause changes ("migration 1252, to be written at the owner's line; intent only").** Nothing here is a migration file; every text in `registry_clause_texts/` carries that header.

**Ordering rule (SS ruling c).** Apply the clause changes BEFORE `ga_medical` / `ga_vastu` are rebuilt in S-L1, and WITH OR AFTER the writer deploy. An OLD writer under the NEW clause, or a NEW writer under the OLD clause, FAILS the post-write integrity gate (the migration-902 failure mode): the old medical writer stores 'mild' for 0.6 to 0.7 and the new clause rejects it; the new writer stores 'moderate' (and, for a NULL score, vāstu 'unknown') and the old clause rejects it.

Exact assembled texts (live clause + the change, with the 1252 intent header and ordering rule as leading SQL comments; the dry-runs are unchanged by the header) are in `registry_clause_texts/` with SHA-256:

| file | sha256 |
|---|---|
| `ga_condition_integrity_scoped_canonical_NOT_APPLIED.sql` | `9c9541f95e4433842f361353b5ce8c7c473a24636d370458d129a9453d8980ba` |
| `ga_condition_integrity_table_wide_NOT_APPLIED.sql` | `4856f55dde3a757074615d48660e1e679affdff2a1e621f58a99709784902e33` |
| `ga_medical_integrity_NOT_APPLIED.sql` | `f2d2176a0bb8ee69f195ef4ee051dc78ef9da994cb3de6c96f064a11b6f94b2b` |
| `ga_vastu_integrity_NOT_APPLIED.sql` | `e07bcd082259ba3f3f051fba84c661c076ce095de2f49a3a03e2dde4c9a44d85` |

### 9.1 `ga_condition`: add conjuncts (e) and (f) to the live clause (migration 902's text), before `AS integrity_passed`

Variant **S (canonical-scoped; the S-L1 form)** mirrors conjunct (a)'s existing scope. **Why it is scoped (SS ruling d):** a table-wide (e) FAILS today on the 90 stale D1-fallback rows of the other two charts (1c826d5a, cb73cd3d), which the S-L1 canonical dispatch never touches (the integrity SQL takes no chart parameter), repeating the migration-902 incident. **It WIDENS to all charts (variant W) as a REQUIRED step of S-L1b**, the same item as fixing `ga_dashas`' canonical-scoped integrity SQL (migration 882) and conjunct (a) of this same clause. The scoped text says this in its own SQL comment.

```sql
  -- (e) X2 / I-29: a composite row that used the D1 fallback (breakdown.varga_fallback_used) on a
  -- chart that HAS divisional rows for that (chart, ayanamsha, graha) is a failure. Same claim the
  -- writer's assert_fallback_legitimate enforces at write time, read here from the stored rows.
  AND NOT EXISTS (
    SELECT 1 FROM ga_condition_composite gc
    WHERE gc.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND COALESCE((gc.condition_score_breakdown->>'varga_fallback_used') = 'true', false)
      AND EXISTS (
        SELECT 1 FROM chart_divisionals cd
        WHERE cd.chart_id = gc.chart_id AND cd.ayanamsha_id = gc.ayanamsha_id AND cd.graha = gc.graha
          AND cd.fact_category IN ('varga_position', 'varga_dignity')
      )
  )
  -- (f) the detector must be able to SEE chart_divisionals: if row-level security applies to the
  -- checking role and the table reads empty, conjunct (e) would pass vacuously (the 2026-09-18
  -- incident class), so the whole check fails closed instead.
  AND (
    NOT row_security_active('public.chart_divisionals')
    OR EXISTS (SELECT 1 FROM chart_divisionals LIMIT 1)
  )
```

Variant **W (table-wide)** is the same (e) without the `gc.chart_id = '482012f1-...'` line (`WHERE` then the `COALESCE` predicate).

Dry-run on today's data as the read-only reader (2026-10-02; `psql -f` of the assembled texts; read-only):

| text | result |
|---|---|
| live clause (migration 902) | `t` |
| variant S | `t` (canonical has 0 fallback rows) |
| variant W | **`f`** (45 violating rows on 1c826d5a + 45 on cb73cd3d = 90, exactly X2's 90 rows) |
| variant S with the canonical composite overlaid by a CTE flipping `varga_fallback_used` to true (mutation proof: the clause CAN fail) | **`f`** |
| conjunct (f) inputs | `row_security_active('chart_divisionals')` = false; 71,476 rows visible |

### 9.2 `ga_medical`: the live clause FAILS after the new writer unless these two edits are applied (migration 740 text)

(b): `WHEN c.condition_score <= 0.6 THEN 'moderate'` becomes `WHEN c.condition_score < 0.7 THEN 'moderate'`.
(c) **Both chart-specific conjuncts REMOVED (SS rulings a and the Sun follow-up).** Migration 740's part (c) held two: `chart_id = '482012f1-...' AND ayanamsha_id = 'lahiri_chitrapaksha' AND graha = 'Saturn' AND indication_strength <> 'mild'` and the same with `graha = 'Sun' AND indication_strength <> 'strong'`. Each asserted a label about ONE chart's value (Saturn: 'mild' at score > 0.6; Sun: condition_score < 0.4 -> 'strong'), tied to an unsourced cut point; the weakened "not in the LOW band" form is not offered either. **An asset's integrity clause must be true for any chart:** the new clause has only (a) the tier / disclosure constants and (b) label = the band-table rule, with no chart id, ayanamsha or graha literal in the SQL body (a test pins that). Saturn's and Sun's canonical scores, bands and labels are pinned by golden tests instead (`tests/test_ga_medical_saturn_golden.py`, `tests/test_ga_medical_sun_golden.py`). (Note, not changed here: conjunct (a) of the ga_condition clause (migration 902) and the scoped variant (e) are also canonical-scoped by design; widening them is the required S-L1b step in section 9.1.)
Dry-run (re-run on the final texts): live clause `t` on today's data; new clause `f` on today's STALE rows (20 rows disagree: 15 canonical + 5 third chart); new clause with `ga_medical` overlaid by what the new writer would store (labels recomputed from the stored scores) `t`.

### 9.3 `ga_vastu`: one edit (migration 924 text)

(c): `WHEN c.condition_score IS NULL THEN 'neutral'` becomes `WHEN c.condition_score IS NULL THEN 'unknown'`, plus the comment lines that state the NULL rule.
Dry-run: new clause `t` on today's data (no NULL scores) and `t` on the overlay of the new writer's labels.

### 9.4 Other registry facts (no change needed, listed so nothing is assumed)

`ga_condition`/`ga_medical`/`ga_vastu` `count_sql`, `target_floor` (2,880 / 45 / 40) and `depends_on` are unaffected (row counts do not change). The output-digest specs (migrations 894 / 916 / 917) are over columns and keep working; the digest VALUES for `ga_medical` rows change on the canonical chart (15 values), which is the intended effect, not a spec change. I-30 (ownership / multi-table declaration of `ga_condition`) is a different lane.

## 10. Consumers of the band values

- **Written:** `ga_medical.indication_strength` (all charts, 45 rows each), `ga_vastu_planet_direction_map.direction_impact` (40 rows each). `ga_condition_composite.condition_score` itself is unchanged.
- **Served (platform):** `get_medical_indications.ts` (selects `indication_strength` verbatim), `get_vastu_directions.ts` (selects `direction_impact` verbatim, joins remedies), `get_condition_composite.ts` (the new served field), `source_query_availability.ts` (knowledge probes over `ga_medical` / `ga_vastu_planet_direction_map` / `ga_condition_composite`). None interprets the label strings, so no served code needed a change for the value changes; vāstu rows with `direction_impact = 'unknown'` can now appear only when a composite row is missing/NULL (none today). MCP descriptions (`ganita_medical_get`, `ganita_vastu_get`, `ganita_condition_get`-family surface text) say "weakened / neutral / strengthened" for vāstu and do not mention the NULL case; unchanged by this lane.
- **L2 / L4 readers of `ga_condition_composite`:** `ph_muhurta` reads the NUMERIC `condition_score` (own `_STRONG_THRESHOLD`), not a band; `bo_pratijna_v4_engine` computes its own condition. No `bo_*` writer reads `ga_medical.indication_strength` or `ga_vastu.direction_impact` (repo grep for `FROM ga_medical`, `ga_vastu_planet_direction_map`: only the served modules and the knowledge-query file above). A canonical rebuild of `ga_medical` / `ga_vastu` therefore changes no L2 signal.

## 11. Detector coverage and attribution hooks

`flip_detector.py` (branch `TI-ephemeris-flip-report-001`) reads only `chart_facts`, `chart_divisionals`, `chart_dashas`, `panchanga_daily`. **The three outputs this lane changes (`ga_condition_composite.condition_score_breakdown` and `.condition_score` on the two S-L1b charts, `ga_medical.indication_strength`, `ga_vastu_planet_direction_map.direction_impact`) are in tables the detector does not read**, so after S-L1 it can neither attribute nor miss them. The two hook files carry the honest statement of that in `description` and a real, falsifiable regression claim in `may_change` (the floored per-varga avastha rows `ga_condition` re-emits in `chart_facts`: `expected_count {exact: 0}`; disjoint category sets so the two lanes never co-claim a change). Both validate: `flip_detector.py --validate-hooks --require-lanes band_table,ga_condition_fallback,argala,gandanta,karaka_roles` -> valid, exit 0; `test_flip_detector.py` 12 passed (from a scratch copy of that branch's detector and the hook files).
Recommendation (D5): extend the detector's `TABLES` with `ga_condition_composite`, `ga_medical`, `ga_vastu_planet_direction_map` (a change on that other branch; not done here).

## 12. Decisions for SS

- **D1 (Saturn and Sun chart-specific assertions): RULED (SS, 2026-10-02): both REMOVED** from the writer and from the registry clause text, not weakened; replaced by golden tests (section 3: Saturn and Sun). Integrity clauses are chart-independent (section 9.2).
- **D2 (third cut-point pair): RULED (SS, 2026-10-02):** moved, values unchanged, into its own table `DASHA_PERIOD_CONDITION_CUTS`; not merged with 0.4 / 0.7 (section 3).
- **D3 (SQL duplicates):** the cut points remain written out in the two registry integrity clauses (SQL cannot import the Python table). A migration author must keep them in step. `tests/test_ga_condition_band_table.py` pins the clause TEXTS in `registry_clause_texts/` to the band table's cut points and NULL label (so the texts to be migrated cannot drift from the writers); it cannot see the live registry rows.
- **D4 (clause scope): RULED (SS, 2026-10-02):** apply (e)+(f) in variant S for S-L1; widening to W is a REQUIRED step of S-L1b (section 9.1). Migration 1252 is allocated for the clause changes; ordering rule in section 9.
- **D5:** extend the flip detector's table list (section 11).
- **D6 (stored column):** X2's stored field is the existing JSON flag + a new `varga_fallback_reason` key; a real boolean column would need a migration (not done; the served field derives from the JSON key).
- **D7:** one canonical Abhinandan row has `condition_score = 0` (surya_siddhanta Mercury); unchanged, a stored fact of the stale fallback build.

## 13. Not verified

- No rebuild was run; nothing was dispatched; the three writers were exercised only by DB-free tests with fake connections. The S-L1 behaviour (a real `ga_condition` / `ga_medical` / `ga_vastu` build against production) is unverified; in particular the guard's two read queries (`count(*)` over `chart_divisionals`, `row_security_active`) were checked against a fake cursor and, as plain SELECTs, against the reader, but not run through the builder role's connection.
- Whether the builder role (`data_plane_builder`) sees `chart_divisionals` rows after the RLS fix at build time: read-only evidence is only for the reader role (RLS off, 71,476 rows visible, `row_security_active` false).
- The X2 scenario (section 6C) is an inference from stored spreads, not a rebuild; the S-L1b scores can differ if the divisional rows differ.
- The registry clause texts were dry-run only (read-only SELECT of the assembled text); no migration was authored, applied or tested through the migration runner, and the deploy-time application of whatever migration carries them was not verified.
- `capability_estate_census.json` was regenerated with `--source-revision` of this branch's code commit; the Dens.served census verdict for `ga_condition` after the select/facet change was not re-measured (the E6 declaration tests pass).
- `nirmana_analysis_layer_pins --check` fails in this checkout independently of this lane (L2/L3 slices stale and missing ancestors); not re-pinned.
- **Supplementary test groups (finished 2026-10-02, foreground, per file group, `PYTHONPATH=.` from `platform/python-sidecar`):** exact commands and counts are in the PR text. One unrelated group had 3 failures in `tests/l3/gochara/test_wp10_cutover.py` (Kāla gochara cutover subprocess scripts, no import of any ga_* module, not touched by this branch; not run against the base to prove it pre-existing). An earlier whole-`tests/` run under heavy machine load reported 20 failures including `test_wave_scheduler.py` (timing tests); that file passes 10/10 in isolation and in the chunked run, so those were load flakes (the 20-name list was not retained).
- The cut points 0.4 / 0.7 and the `varga_fallback_reason` key are project conventions (`unsourced`); no classical passage supports them.
- Whether the sheet's I-29 "Dens facet" is meant to be the `density_contract.facets` entry (done) or an additional census Dens criterion: I implemented the former; the census `Dens.served` criterion itself (a tier column in the served select) is a different, existing check and I did not add a tier column to the select.
