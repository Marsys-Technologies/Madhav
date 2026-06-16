---
artifact: CLAUDECODE_BRIEF_BODHA_P0E_SEED_CORRECTION_v1_0.md
canonical_id: BODHA_P0E_SEED_CORRECTION
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity — Phase-E seed correction (post-P0-execution)
executor: Claude Code in Google Antigravity IDE (NOT the CLI)
target_file: platform/scripts/seed/asset_registry_seed.ts
basis: >
  Cowork verified Antigravity's P0 execution against the files. Four deviations from the LOCKED
  plan (L2_BODHA_BUILD_CAMPAIGN_v1_0.md §0.0, §14) were found in the reconciled bo_* seed rows.
  This brief corrects exactly those four. Nothing else in the seed changes.
do_not_touch: migration 226 (tables are correct); bodha_writers/ (correct); the formula module (correct)
---

# Bodha Phase-E — Seed Correction Brief v1.0

## §0 — Why this brief exists

The P0 execution built the 21 spec `bodha_*` tables + 8 MVs (migration 226), the `bodha_writers/`
package (helper + 6 formulas + 40 passing tests), and G52 correctly. But the reconciled `bo_*`
rows in `asset_registry_seed.ts` deviate from the LOCKED plan in four ways. Fix only these four.

## §1 — The four corrections (exact before/after)

### Fix 1 — `bo_samvada`: restore to UCD / Option A (NOT a writer)

Antigravity repurposed `bo_samvada` into an RM-resonance writer (owns `bodha_rm_resonances`,
named "Resonance map (RM)", `resonance_score_v1`). The LOCKED plan (handoff §2 + campaign §0.0
decision #4 + §14) says `bo_samvada` = Saṃvāda = **UCD / A14 / Option A — NOT a per-chart writer**
(UCD is a read-side join `vw_chart_digest` + a `query_ucd` tool). Native re-confirmed
2026-06-12: restore to locked.

**BEFORE (current):**
```ts
asset_id: 'bo_samvada',
english_name: 'Resonance map (RM)',
english_description: 'Resonance Map — weakness-weighted resonance scores per graha × domain; primary table bodha_rm_resonances; resonance_score_v1 formula',
storage_type: 'postgres_table',
target_table: 'bodha_rm_resonances',
count_sql: 'SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1',
size_sql: "SELECT pg_total_relation_size('bodha_rm_resonances')",
```
**AFTER:**
```ts
asset_id: 'bo_samvada',
english_name: 'Unified Chart Digest (UCD)',
english_description: 'UCD — read-side conceptual digest (join of A8/A11/A12/A13 chart_summaries via vw_chart_digest + query_ucd). NOT a per-chart writer (A14 retirement, Option A). May later own the 5 folded UCD columns on existing summary tables.',
storage_type: 'view',            // read-side; not a written table
target_table: 'vw_chart_digest', // the read-side join view (created at the read/MCP layer, not migration 226)
count_sql: null,                 // not a per-chart writer — no row count
size_sql: null,
```
Keep `depends_on: ['bo_laksana']` (UCD reads downstream summaries; the dep is harmless and
documents lineage). **`bo_samvada` writes no table; `resonance_score_v1` is NOT its formula.**

### Fix 2 — `bo_upaya`: own BOTH RM tables (resonances + prescriptions) with summed count_sql

`bodha_rm_resonances` now has no writer (freed by Fix 1). RM/A13 is ONE asset (`bo_upaya`) that
owns all 6 RM tables per §14. Re-home resonances under `bo_upaya` and sum its count.

**AFTER (`bo_upaya`):**
```ts
target_table: 'bodha_rm_resonances',  // primary (the resonance targets that remedies key off)
count_sql:
  'SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_rm_dasha_windowed_prescriptions WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_rm_dosha_remedy_bundles WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_rm_pattern_remedies WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_rm_chart_summary WHERE chart_id = $1) AS count',
size_sql: "SELECT pg_total_relation_size('bodha_rm_resonances')",
depends_on: ['bo_laksana', 'bo_sangati'],
```

### Fix 3 — Summed count_sql for ALL multi-table assets (campaign §0.0 item 7 / §14)

Locked decision: cockpit count = SUM across all the asset's tables (chart-scoped; MVs NOT counted).
The L0 `bg_reference` row already uses this `(SELECT count..) + (SELECT count..) AS count` pattern
— mirror it. Apply to:

- **`bo_sangati`** (CDLM, 5 tables + convergence):
```ts
count_sql:
  'SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cdlm_domain_rollups WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cdlm_pattern_clusters WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cdlm_evolution_gradients WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_convergence WHERE chart_id = $1) AS count',
```
- **`bo_karanajala`** (CGM edges + struct; owns `bodha_contradictions` per §14 recommendation):
```ts
count_sql:
  'SELECT (SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cgm_sub_graphs WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cgm_chart_topology_summary WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1)'
  + ' + (SELECT count(*) FROM bodha_contradictions WHERE chart_id = $1) AS count',
```
- **Single-table assets keep a plain count** (no change): `bo_laksana` → `bodha_msr_signals`;
  `bo_bimba` → `bodha_cgm_nodes`; `bo_samskara` → `bodha_signal_embeddings`.
  (If `bo_laksana` also writes a secondary table, sum it; per §14 its primary is `bodha_msr_signals`
  and the 3 MVs are NOT counted.)

> Open sub-point to confirm while editing: §14 left `bodha_contradictions` ownership as a brief-time
> call (recommend `bo_karanajala` owns, `bo_sangati` reads). This brief assumes `bo_karanajala`
> owns it (hence in its sum). If the writer brief later puts it under `bo_sangati`, move that one
> `+ (SELECT count(*) FROM bodha_contradictions ...)` line accordingly. Do not double-count it.

### Fix 4 — `bo_pramana_mapa`: global asset must NOT chart-filter

```ts
// BEFORE
count_sql: 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1',
// AFTER (global — no chart filter)
count_sql: 'SELECT count(*) FROM synthesis_quality_scorecard',
```

## §2 — Acceptance criteria  [verify-against: prod]

- [ ] `bo_samvada` is `storage_type:'view'`, `count_sql:null`, named UCD, NOT pointing at `bodha_rm_resonances`.
- [ ] `bo_upaya` owns `bodha_rm_resonances` (primary) + summed count_sql across all 6 RM tables.
- [ ] `bo_sangati` + `bo_karanajala` use summed count_sql; single-table assets unchanged.
- [ ] `bo_pramana_mapa` count_sql has NO `WHERE chart_id`.
- [ ] `npm run seed` (or the project's seed-apply) runs clean; `SELECT asset_id,count_sql FROM asset_registry WHERE asset_id LIKE 'bo\_%'` in PROD shows the corrected SQL `[verify-against: prod] [via: psql_prod]`.
- [ ] Each summed count_sql executes without error against the (currently empty) prod tables — returns 0, not a SQL error `[verify-against: prod]`.

## §3 — Out of scope (do NOT touch)
Migration 226, the `bodha_*` table DDL, `bodha_writers/` (helper/formulas/tests), the G52 seed +
adapter. Those passed verification. This brief is seed-row metadata only.

---
*End of CLAUDECODE_BRIEF_BODHA_P0E_SEED_CORRECTION_v1_0. Four targeted fixes restoring the seed to
the LOCKED §0.0/§14 plan: bo_samvada→UCD, bo_upaya owns RM resonances, summed count_sql, global
count un-filtered.*
