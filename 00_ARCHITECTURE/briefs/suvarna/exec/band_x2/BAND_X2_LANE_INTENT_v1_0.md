---
artifact: BAND_X2_LANE_INTENT
version: "1.0"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (worker lane)
date: 2026-10-02
decision: SS N-62 (decision sheet L1 v1.2): Q-L1-16(c) = Track I I-28; X2 = Track I I-29 (both MANDATORY before S-L1; provisional until J1; (R) items)
branch: suvarna/land/TI-l1-band-x2-001 (from origin/main 925e96a5d)
execution: code + tests + docs on a local branch. NO migration, NO registry write, NO database write (the database was read as the read-only reader only), no push, no PR.
changelog:
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
2. `ga_condition_writer._PEAK_CONDITION_THRESHOLD = 0.65` and `_WEAK_CONDITION_THRESHOLD = 0.35` gate which mahadasha periods are stored as peak/weak in `peak_dasha_periods` / `weak_dasha_periods`. A different, un-ruled pair of cut points over the same score. **Not folded into the table by this lane** (the ruling names only the medical and vāstu scales); flagged for SS (section 12, D2).
3. L2 `bo_pratijna_v4_engine.OCCURRENCE_BANDS` / `CONDITION_BANDS` and `ph_muhurta` `_STRONG_THRESHOLD = 0.75` are bands over THEIR OWN computed quantities (occurrence 0 to 1, a 0 to 10 affliction scale, a muhūrta score), not over `ga_condition_composite.condition_score`. Not duplicates; no change.

### 2.2 Where `neutral` was invented

Only `ga_vastu_writer.compute_direction_impact(None)` returned `'neutral'` for a NULL score (and the registry clause 741/924 asserted it). `ga_medical` already returned `'unknown'`. Other `neutral` strings in `ga_condition_writer.py` are dignity/friendship vocabulary ("neutral_sign", panchadha) and a lajjitadi context fallback, unrelated to the score. No stored row takes the NULL path today (no `condition_score` is NULL on any of the 135 composite rows), so the fix changes zero stored rows; it removes a latent invention.

### 2.3 A trap the sheet's effect line did not name: the Saturn FORENSIC guard

`ga_medical_writer` raised `AssertionError` for the canonical Lahiri build unless Saturn's `indication_strength == 'mild'` (score > 0.6). The measured canonical Saturn scores are **0.6800 / 0.6831 / 0.6915 / 0.6972** (all five ayanamshas below 0.7), i.e. MID band, "moderate", under the ruled table. A literal 0.7 cut with the old guard would **halt every canonical `ga_medical` build** on a number the ruling moved, not on a Saturn regression. Handled in section 3 (decision D1 for SS).

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
- **Saturn FORENSIC guard (decision D1):** `ga_medical_writer.saturn_forensic_guard_violation` now asserts what the classical claim supports, "an exalted planet is not under stress": Saturn's band must exist and must not be LOW (score >= 0.4). Measured canonical Saturn is 0.680-0.697 (MID) so it passes; a NULL or < 0.4 Saturn still HALTS the build (a real detector, tested). It no longer demands "mild", which is a band-edge question (0.7), not an exaltation one. Same reasoning as the `ga_vastu` Saturn gate dropped by migration 924 (#2421).
- Not changed: the formula, weights, `condition_score` values, the dasha peak/weak thresholds (D2).

## 4. Design: X2 (I-29)

1. **Stored field.** The flag already exists: `condition_score_breakdown.varga_fallback_used` (true on 90 rows, false on the canonical 45). Added in the same JSON: `varga_fallback_reason = "no_divisionals_for_chart"`, written only when the fallback is used (which, after the guard, means the chart genuinely has no divisional rows). **No new column**: a column needs a migration (forbidden here; follow-up D6).
2. **Served field + Dens facet** (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts`): every row carries top-level `varga_fallback_used` (true / false / **null when the flag is absent**, never coerced to false) and `varga_fallback_reason`; `varga_fallback_used` is a declared input filter and a `density_contract.facets` entry (`['graha','ayanamsha_id','varga_fallback_used']`); the response counts D1-fallback rows separately (`d1_fallback_rows_in_page`, `d1_fallback_total_matching` over the full filtered set, null if the count did not return it) with a `d1_fallback_note` (CLAUDE.md N.6 item 1: never flattened in with divisional-based rows). The empty-reason text names the new filter.
3. **Writer-side guard (the detector).** In `build_ga_condition_substep`, when `compute_condition_score_v1` reports `varga_fallback_used` (a score is actually being computed on D1 alone), `assert_fallback_legitimate` asks the table: `count_visible_divisional_rows(chart, ayanamsha, graha)` over `fact_category IN ('varga_position','varga_dignity')`. Visible rows > 0 raises `VargaFallbackWithDivisionalsError` (this is the F-C8 class: a stored label the composite could not score; also an exception swallowed by `_load_varga_dignity_spread`). Zero rows AND `row_security_active('public.chart_divisionals')` for the build role also raises (an empty read under active RLS proves nothing: the 2026-09-18 incident class). It passes ONLY on a trustworthy "no divisionals" and then stores the visible flag + reason. The guard sits BEFORE the composite DELETE/INSERT, so a refused fallback writes nothing. A failing count query is not swallowed (fail closed).
4. **Verifier side.** `FALLBACK_VIOLATION_PREDICATE_SQL` + `fallback_integrity_violations(conn, chart_id=None)` read the stored rows for the same claim (flag true AND the chart has divisional rows for that (chart, ayanamsha, graha)); the registry clause (section 9) uses the same predicate, byte-identical (a test pins the equality with this document).
5. **Canonical chart impact: none.** The canonical composite already reads divisional dignity on 45/45; the guard never fires there. The two fallback charts (S-L1b) cannot be rebuilt by the writer until their composites can read divisionals; with the fixed writer they will (F-C8 is fixed), and the guard converts any recurrence into a build failure.

## 5. Files and tests

New: `ga_writers/ga_condition_bands.py`; `tests/test_ga_condition_band_table.py` (49 tests); `tests/test_ga_condition_band_clause_texts.py` (4 tests, pins the clause texts of section 9); `tests/test_ga_condition_fallback_guard.py` (13 tests); `exec/s_l1_attribution_hooks/band_table.json`, `ga_condition_fallback.json`; this folder: this document, `band_x2_old_vs_new.py`, `old_vs_new_output_2026-10-02.txt`, `registry_clause_texts/*.sql` (NOT applied).
Edited: `ga_condition_writer.py`, `ga_medical_writer.py`, `ga_vastu_writer.py`; `get_condition_composite.ts` + its test (6 new); `pipeline/orchestrator/writers/__tests__/test_ga_medical.py` (the 0.61 boundary case moves to "moderate"; 0.7 added) and `test_ga_vastu.py` (NULL -> 'unknown'); regenerated `platform/src/generated/nirmana-writer-digests.json`; E6 re-pin of ga_condition line numbers (`asset_declarations.json`, `test_e6_1_declarations.py`, as commit 271290c25 did); census regeneration (section 8).

Golden/boundary coverage: 0.0, 0.3999999, 0.4, 0.4000001, 0.5, 0.6, 0.65, 0.6999999, 0.7, 0.7000001, 1.0, out-of-range, NULL, NaN, non-numeric, `Decimal('0.4')`, `Decimal('0.700000')`, numeric strings; table contiguity on a 0.01 grid (every score in exactly one band); identity `cond.SCORE_BANDS is med.SCORE_BANDS is vas.SCORE_BANDS`; an AST test that neither consumer's executable code contains 0.4 / 0.6 / 0.7; both label maps cover exactly the band names; medical and vastu agree on the band of every score on a 0.001 grid; stored label values unchanged; NULL never 'neutral'; Saturn guard (passes 0.4, 0.68-0.7, 0.85; fires < 0.4 and NULL). Fallback: guard raises with divisionals present, passes when genuinely absent, refuses an RLS-blind empty read, fails closed on a failing read; the build writes nothing when refused (F-C8-class unscorable label and a swallowed-failure None), flags and reasons when legitimate, never consults the guard when the composite is usable; the verifier returns violators and scopes by chart.

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

`provenance_inventory --output` before vs after: **3 writer digests moved: `ga_condition`, `ga_medical`, `ga_vastu`** (L1 only). `probe_digest` unchanged; no writer added or removed; **no L0 (`bg_*`), L2 (`bo_*`), L3 (`ka_*`) asset moved**, `verification_vocab.py` and every other L0 module untouched. (Importers of `ga_condition_writer.py`, e.g. `ga_dashas_writer`, did not move: the inventory's closure does not follow them.) `ga_condition` is `asset_frozen` against its live generation (migration 902 note): this change unfreezes it by design; the S-L1 rebuild re-freezes it.

Pins: `platform/src/generated/nirmana-analysis-layer-pins.json` was NOT regenerated: `python -m scripts.generate.nirmana_analysis_layer_pins --check` already reports L1, L2 and L3 slices stale and many "artifact commit must be an ancestor of HEAD" errors in this checkout, including L2 and L3 slices no digest of which moved here; the pin regeneration is a convergence-time step that needs a reviewed commit and a database. E6 declaration line pins for `ga_condition` (citation sites 1117 -> 1250, 1391 -> 1524, column list 1201 -> 1334; served read `get_condition_composite.ts:91 -> 121`) were re-pinned; the AST site counts did not change.

## 9. Registry changes to apply LATER by migration (NOT applied; no migration in this branch)

Applying order matters: the registry clauses must be in place BEFORE `ga_medical` / `ga_vastu` are rebuilt with the new writers, or the post-write integrity gate fails (the migration-902 failure mode). Exact assembled texts (live clause + the change) are in `registry_clause_texts/` with SHA-256:

| file | sha256 |
|---|---|
| `ga_condition_integrity_scoped_canonical_NOT_APPLIED.sql` | `0f71cc59b41f02e48e3f33c1dc0e9a94f7b08b425e014c3cf330c091969b0f42` |
| `ga_condition_integrity_table_wide_NOT_APPLIED.sql` | `0f956d6ec0594d517bd3c91bbe3317738e73343957543a2e1cd0a249a774c3bc` |
| `ga_medical_integrity_NOT_APPLIED.sql` | `4f9d8c3d3416bf93ab1b2f02809033214d3804b1a9af86c9d560262fea0a8f85` |
| `ga_vastu_integrity_NOT_APPLIED.sql` | `218c764f2f328e6f0ba831ef882b08a9f1fd9931579414d1fcb04c71bc63dc22` |

### 9.1 `ga_condition`: add conjuncts (e) and (f) to the live clause (migration 902's text), before `AS integrity_passed`

Variant **S (canonical-scoped; recommended for S-L1)** mirrors conjunct (a)'s existing scope. A table-wide (e) would FAIL on the 90 stale rows of the two S-L1b charts the moment anyone dispatches `ga_condition` for the canonical chart (the integrity SQL takes no chart parameter), repeating the migration-902 incident. Widen to variant W after S-L1b.

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
(c) Saturn conjunct (FORENSIC): `AND graha = 'Saturn' AND indication_strength <> 'mild'` becomes `AND graha = 'Saturn' AND (indication_strength IS NULL OR indication_strength IN ('strong', 'unknown'))` (Saturn must not be in the LOW band; same claim as the writer guard).
Dry-run: live clause `t` on today's data; new clause `f` on today's STALE rows (20 rows disagree: 15 canonical + 5 third chart; the canonical Saturn row reads 'mild'); new clause with `ga_medical` overlaid by what the new writer would store (labels recomputed from the stored scores) `t`.

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

- **D1 (Saturn FORENSIC guard):** changed from "Saturn must be 'mild'" to "Saturn must not be in the LOW band" (section 3). Needed or every canonical `ga_medical` build halts. SS may prefer to drop the guard (as migration 924 did for vāstu) or to keep a literal-'mild' guard and move Saturn's expectation, which would contradict the ruled 0.7.
- **D2 (third cut-point pair):** `_PEAK_CONDITION_THRESHOLD 0.65` / `_WEAK_CONDITION_THRESHOLD 0.35` over the same score are not in the ruling. Folding them into the table (peak = high band, weak = low band) would change which dasha periods are stored (0.65 -> 0.7 and 0.35 -> 0.4); not done.
- **D3 (SQL duplicates):** the cut points remain written out in the two registry integrity clauses (SQL cannot import the Python table). A migration author must keep them in step. `tests/test_ga_condition_band_table.py` pins the clause TEXTS in `registry_clause_texts/` to the band table's cut points and NULL label (so the texts to be migrated cannot drift from the writers); it cannot see the live registry rows.
- **D4 (clause scope):** apply (e)+(f) in variant S now, widen to W after S-L1b.
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
- The cut points 0.4 / 0.7 and the `varga_fallback_reason` key are project conventions (`unsourced`); no classical passage supports them.
- Whether the sheet's I-29 "Dens facet" is meant to be the `density_contract.facets` entry (done) or an additional census Dens criterion: I implemented the former; the census `Dens.served` criterion itself (a tier column in the served select) is a different, existing check and I did not add a tier column to the select.
