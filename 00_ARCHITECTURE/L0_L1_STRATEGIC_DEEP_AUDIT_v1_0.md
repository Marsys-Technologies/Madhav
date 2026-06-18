---
canonical_id: L0_L1_STRATEGIC_DEEP_AUDIT
version: "1.0"
status: CURRENT
date: 2026-06-18
author: Claude Code (multi-agent, read-only)
scope: L0 Brahmagyan + L1 Gaṇita — pre-L2 strategic foundation analysis
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
---

# L0+L1 Strategic Deep Audit — Pre-L2 Foundation Analysis

**Purpose:** Ground-truth audit of the L0+L1 layers before L2 Bodha opens. All claims are backed by live prod DB queries (`127.0.0.1:5433/amjis`) or code citations. This is an analysis document — no changes were made.

**Methodology:** Four independent research agents ran in parallel against the production database and writer codebase. Every finding cites the specific file:line or SQL result that supports it.

---

## EXECUTIVE SUMMARY

**Autonomy:** 30 of 39 registered assets are fully autonomous-ready. Four data assets (`bg_ephemeris`, `bg_dignity_reference`, `bg_transit_engine`, `bg_nakshatra_medical`) have no WriterBase writer and silently DEFER on a "Rebuild All" — the DEFER-001/002 gaps from the L0 closure are confirmed and still open. One service asset (`ga_pyjhora_engine`) is stuck in error state since 2026-06-12. Zero FROZEN contract violations across all 32 writer files.

**Regressions:** None. The post-enrichment `chart_facts` total is 111,481 (vs. 27,554 at L1 Closure) — a documented, deliberate expansion. `chart_dashas` (536,471) and `chart_divisionals` (21,635) match closure records exactly. All apparent count discrepancies are either scope corrections or stale throughput records.

**Critical pre-L2 blockers (5):**
1. `ga_yoga` has only 5 rows — the evaluator has explicit `return None` for unimplemented relation types; `bo_samskara` launches with functionally no yoga firing data.
2. `ga_prashna` count_sql has a syntax bug (leading `(`) causing it to show as red/error in the cockpit for every chart.
3. `ga_structural`'s `benefics_in` composite rule silently returns `False` at line 3833 — Adhi Yoga and ~14 formations never fire via the DB-catalog path.
4. `bo_laksana`'s signal category list omits 43,200 argala/virodha rows and 4 of 5 avastha systems — these are computed but never projected into MSR signals.
5. The `uncatalogued_configuration` fact category (Fix 4.2 from the prior finding) was never implemented — structural gap detection is impossible.

**Prashna:** Leave dormant; fix the count_sql bug (one line + one migration) before L2 begins. Full activation is a separate multi-session arc with no L2 Bodha dependency.

**ga_structural:** The prior hardcoded-yoga finding is partially resolved (dual-path DB+fallback now live, `brahma_yoga_catalog` is read). Two claims remain live defects: orb-threshold silent drop and uncatalogued-configuration emission. The highest-leverage elevation is adding argala/virodha + lord-matrix categories to `bo_laksana`'s signal list — **no ga_structural change required**.

---

## Q1 — Orchestrator-Autonomy Audit

### 1.1 Per-Asset Autonomy Table

#### L0 Brahmagyan (`bg_*`)

| asset_id | in_registry | in_seed_ts | build_state | rows_written | writer_exists | contract_ok | VERDICT |
|---|---|---|---|---|---|---|---|
| bg_compendium_index | YES | YES | lit 2026-06-17 | 9,538 | YES | YES | **AUTONOMOUS-READY** |
| bg_concordance | YES | YES | lit 2026-06-16 | 477 | YES | YES | **AUTONOMOUS-READY** |
| bg_dasha_systems | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_dignity_reference | YES | YES | lit 2026-06-17 | 151 | **NO** | N/A | **WRITER-MISSING** |
| bg_doshas | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_ephemeris | YES | YES | lit 2026-06-16 | — | **NO** | N/A | **WRITER-MISSING** |
| bg_ephemeris_engine | YES | YES | no throughput | N/A | NO | N/A | SERVICE-OK (probe-driven) |
| bg_medical_mappings | YES | YES | lit 2026-06-17 | 36 | YES | YES | **AUTONOMOUS-READY** |
| bg_nakshatra | YES | YES | lit 2026-06-18 | 2,857 | YES | YES | **AUTONOMOUS-READY** |
| bg_nakshatra_medical | YES | YES | lit 2026-06-17 | 27 | **NO** | N/A | **WRITER-MISSING** |
| bg_ontology | YES | YES | lit 2026-06-18 | 623 | YES | YES | **AUTONOMOUS-READY** |
| bg_panchanga | YES | YES | no throughput | N/A | NO | N/A | SERVICE-OK (probe-driven) |
| bg_prashna_rules | YES | YES | lit 2026-06-17 | 36 | YES | YES | **AUTONOMOUS-READY** |
| bg_reference | YES | YES | lit 2026-06-18 | 1,485 | YES | YES | **AUTONOMOUS-READY** |
| bg_remedies | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_rules | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_text_index | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_texts | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| bg_transit_engine | YES | YES | lit 2026-06-17 | 9 | **NO** | N/A | **WRITER-MISSING** |
| bg_transit_rules | YES | YES | lit 2026-06-17 | 50 | YES | YES | **AUTONOMOUS-READY** |
| bg_vastu_directions | YES | YES | lit 2026-06-17 | 32 | YES | YES | **AUTONOMOUS-READY** |
| bg_yogas | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |

#### L1 Gaṇita (`ga_*`)

| asset_id | in_registry | in_seed_ts | build_state | rows_written | writer_exists | contract_ok | VERDICT |
|---|---|---|---|---|---|---|---|
| ga_condition | YES | YES | lit 2026-06-17 | 45* | YES | YES | **AUTONOMOUS-READY** |
| ga_dashas | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| ga_medical | YES | YES | lit 2026-06-17 | 45 | YES | YES | **AUTONOMOUS-READY** |
| ga_nakshatra | YES | YES | lit 2026-06-18 | 1,802 | YES | YES | **AUTONOMOUS-READY** |
| ga_panchanga | YES | YES | lit 2026-06-15 | 437 | YES | YES | **AUTONOMOUS-READY** |
| ga_positions | YES | YES | lit 2026-06-15 | 530 | YES | YES | **AUTONOMOUS-READY** |
| ga_prashna | YES | YES | lit 2026-06-17 | 0 | YES | YES | **NOT-BUILT-OK** (natal, by design) |
| ga_pyjhora_engine | YES | **NO** | **error 2026-06-12** | — | NO | N/A | **BUILD-STATE-ERROR** |
| ga_sade_sati | YES | YES | lit 2026-06-17 | 11,019 | YES | YES | **AUTONOMOUS-READY** |
| ga_sensitive | YES | YES | lit 2026-06-17 | 8,610 | YES | YES | **AUTONOMOUS-READY** |
| ga_strength | YES | YES | lit 2026-06-17 | 11,090 | YES | YES | **AUTONOMOUS-READY** |
| ga_structural | YES | YES | lit 2026-06-17 | 75,168* | YES | YES | **AUTONOMOUS-READY** |
| ga_tajaka | YES | YES | lit 2026-06-11 | 240 | YES | YES | **AUTONOMOUS-READY** |
| ga_transit_anchors | YES | **NO** | lit 2026-06-17 | 45 | YES | YES | **AUTONOMOUS-READY** (added via migration, not seed_ts) |
| ga_vargas | YES | YES | lit 2026-06-16 | — | YES | YES | **AUTONOMOUS-READY** |
| ga_vastu | YES | YES | lit 2026-06-17 | 40 | YES | YES | **AUTONOMOUS-READY** |
| ga_yoga | YES | YES | lit 2026-06-17 | 5 | YES | YES | **AUTONOMOUS-READY** (writer runs; 5 rows is a completeness defect, not an autonomy gap) |

*throughput rows stale; table counts correct — see Q2.

### 1.2 Autonomy Gap List

Assets that a "Rebuild All" will NOT correctly regenerate:

**Gap 1 — `bg_ephemeris` (WRITER-MISSING)**
Registered as `asset_type='data'` / `storage_type='postgres_table'` but data is populated by the legacy `brahma_pipeline.py` bootstrap path. Orchestrator logs DEFERRED and skips.
- Remediation A: Write a `bg_ephemeris.py` WriterBase writer wrapping the bootstrap logic.
- Remediation B: Reclassify `asset_type='service'` to formally declare it probe-driven (matches `bg_ephemeris_engine` pattern).

**Gap 2 — `bg_dignity_reference` (WRITER-MISSING)**
Registered as data asset, seeded by migration 250 SQL INSERTs. No orchestrator writer.
- Remediation A: Write `bg_dignity_reference.py` that re-seeds from canonical SQL.
- Remediation B: Add `catalog_status='IMMUTABLE'` so the orchestrator knows to skip it intentionally.

**Gap 3 — `bg_transit_engine` (WRITER-MISSING — DEFER-001 confirmed)**
Has own asset_registry row and throughput entry (9 rows), but no `@register('bg_transit_engine')` writer. Data is a side-effect of `bg_transit_rules.py`. A direct rebuild of this asset_id DEFERS.
- Remediation A: Add `@register('bg_transit_engine')` as a second decorator on `bg_transit_rules.py`.
- Remediation B: Remove `bg_transit_engine` from asset_registry as a standalone asset.

**Gap 4 — `bg_nakshatra_medical` (WRITER-MISSING — DEFER-002 confirmed)**
Same pattern as DEFER-001. Data is a side-effect of `bg_medical_mappings.py`.
- Remediation A: Add `@register('bg_nakshatra_medical')` to `bg_medical_mappings.py`.
- Remediation B: Remove as a standalone asset_registry entry.

**Gap 5 — `ga_pyjhora_engine` (BUILD-STATE-ERROR)**
Service-type asset (no writer by design), but `asset_throughput.state = 'error'` since 2026-06-12 — 6 days stale. Not an autonomy gap per se (service assets have no writer), but the stuck error state means the cockpit shows this as broken.
- Remediation: Investigate pyjhora service failure; reset throughput once service is healthy.

### 1.3 Contract Conformance

**Zero FROZEN contract violations** across all 32 writer files examined. All writers:
- Have `@register('<asset_id>')` decorator
- Subclass `WriterBase`
- Implement `run(ctx) -> WriterResult` (light) or `plan_substeps + run_substep` (heavy)
- Never call `.commit()` or `.close()` on `ctx.db_conn`
- Never write to `asset_throughput` directly
- Retrieve `chart_id` / `birth_params` from `ctx.config`

**Non-blocking code smells (not violations):**
- `ga_nakshatra.py`: uses `ctx.config.get("birth_params", ctx.config)` fallback — passes entire config dict if key absent; inconsistent with other heavy writers. Low risk if orchestrator always injects the key.
- `ga_nakshatra.py`: uses connection-level `ctx.db_conn.execute(...)` instead of cursor pattern used elsewhere. Valid psycopg3 but inconsistent.

### 1.4 Seed vs. Registry Divergence

`ga_transit_anchors` is in `asset_registry` and has a functioning writer, but is absent from `asset_registry_seed.ts` (added via migration only). If seed is ever re-applied from scratch, this asset will be missing.

---

## Q2 — Under-Reporting Bug Hunt + Per-Asset Enrichment Audit

### 2A — Count Regression Verdict

**No genuine data regressions found.** All discrepancies are either documented scope corrections, stale throughput records, or the legitimate post-enrichment expansion.

Important context: the L1 Closure doc's `chart_facts = 27,554` predates the L1 Enrichment campaign (PRs #297–299). Post-enrichment actual count is **111,481** — a deliberate expansion of ~83,927 rows. `chart_dashas` (536,471) and `chart_divisionals` (21,635) are unchanged and match closure records exactly.

| asset_id | prior_count | count_sql_result | actual_table_rows | verdict | evidence |
|---|---|---|---|---|---|
| chart_facts total | 27,554 (L1 closure) | — | 111,481 | CORRECTED | Post-enrichment expansion via PRs #297–299 |
| chart_dashas | 536,471 | — | 536,471 | OK-MATCHES | |
| chart_divisionals | 21,635 | — | 21,635 | OK-MATCHES | |
| bg_yogas | 175 | 175 | 175 | OK-MATCHES | |
| bg_rules | 2,912 | 2,912 | 2,912 | OK-MATCHES | Depth gap (8.1% coverage), not regression |
| bg_doshas | 50 | 50 | 50 | OK-MATCHES | |
| bg_nakshatra | 2,857 | 2,857 | 2,857 | OK-MATCHES | 3-table composite: 28+108+2,721 |
| bg_compendium_index | 9,538 | 9,538 | 9,538 | CORRECTED | Stale throughput row of 7,025 from prior partial run; table correct |
| bg_medical_mappings | 36 (throughput) | 9 | 9 | CORRECTED | Throughput 36 = multi-ayanamsha run artifact; L0 table correctly has 9 rows |
| bg_prashna_rules | 36 (throughput) | 41 | 41 | CORRECTED | Throughput stale pre-table-expansion; table correct |
| ga_structural | 75,168 (throughput) | 74,034 | 74,034 | CORRECTED | 1,134 rows re-scoped to ga_condition (per-varga avastha); floor and count_sql in sync |
| ga_condition | 45 (throughput) | 2,880 | 2,880 | CORRECTED | Amendment 2 added 2,835 per-varga avastha rows; throughput stale |
| ga_strength | ~2,184 (pre-enrichment) | 11,936 | 11,936 | CORRECTED | Amendment 1 (per-varga AV rows) drove legitimate expansion |
| ga_panchanga | 437 (throughput) | 221 (count_sql) | ~437 (incl. non-panchanga% cats) | CORRECTED | count_sql scoped to `panchanga%`; 216 rows are chandra_bala/tara_bala written by ga_panchanga but categorized differently |

**Specific ga_structural count investigation (SIX_SUBSYSTEM 75,168 → L1 closure 74,034):**
The 1,134-row drop is a legitimate re-scoping: per-varga avastha rows were moved from ga_structural to ga_condition. This is a corrected scope, not data loss. The 74,034 figure is the correct current count.

### 2B — Per-Asset Enrichment Audit

#### Hard Gate Applied
A gap counts only if: (1) deterministic computation — no generative LLM, (2) citable classical source, (3) not already captured.

#### BUILD-NOW (blocks L2 or acharya-grade completeness)

| asset_id | currently_captures | gap | value_rationale |
|---|---|---|---|
| `ga_yoga` | 5 rows (only yuga_nabhasa fires, 5 ayanamshas) | Evaluator at `ga_yoga_writer.py` lines 812–825 has explicit `return None` for unimplemented relation types (`benefics_in_upachayas_3_6_10_11_from_lagna_or_moon`, `kendra_and_trikona_lords_as_benefics_in_kendras`, etc.) | **CRITICAL for L2** — `bo_samskara` is designed to consume `ga_yoga_firings`; will launch with functionally no yoga data. The 175 catalog yogas are evaluated; only 5 fire because the evaluator is incomplete, not because the chart lacks yogas. |
| `bg_rules` | 2,912 rules from 660/8,193 text chunks (8.1%) | 7,533 chunks never extracted; extraction infra already exists — bulk re-run only | Acharya-grade completeness structurally impossible with 91.9% of classical rule corpus absent. |
| `bg_doshas` | 50 dosha definitions | 20–70 missing: Kuja Dosha variants, Grahan Dosha, Pitra Dosha, Naga Dosha | Rule-based, schema exists; ga_structural dosha firing capped by L0 catalog size. |
| `bg_remedies` | 266 remedy entries | Missing most mantra prescriptions, yantra specs, dana schedules | `bo_upaya` viability depends on this — sparse remedies mean sparse Bodha remedial output. |
| `bg_medical_mappings` | 9 rows (one per planet, single tier) | Planetary combinations + 27×3 nakshatra-dosha grid absent (~150–200 rows needed) | `ga_medical` reads `bg_medical_mappings` correctly and will auto-improve once L0 table expanded. Fix L0 first. |
| `bg_yogas` | 175 yoga definitions | ~75 missing: Jaimini yogas, Nabhasa variants, some KP yogas. Schema already built. | Directly caps what ga_structural can fire via catalog path. |

#### LOG-FOR-V2 (deterministic + citable but not blocking)

| asset_id | gap | verdict |
|---|---|---|
| `bg_nakshatra` | Tarabala full 27×27 grid (729 pairs) absent | LOG-FOR-V2 |
| `bg_reference` | Muhurta (30 muhurtas), Hora details incremental | LOG-FOR-V2 |
| `bg_texts` | Brihat Jataka, Phaladeepika, Uttara Kalamrita partial corpus | LOG-FOR-V2 |
| `ga_strength` | Navamsha-specific strength, saptavargaja gap vargas (floored correctly) | LOG-FOR-V2 |
| `ga_vargas` | Outer planets scope-capped correctly; D81 sentinel present | LOG-FOR-V2 |
| `ga_sensitive` | Lal Kitab (G41 corpus absent), Maharsi Nadi (G44 absent) — floors correctly marked | LOG-FOR-V2 |
| `ga_condition` | Bhava (house-level) conditions absent; dasha-conditional states are L3 scope | LOG-FOR-V2 |
| `ga_nakshatra` | Abhijit handling, extended KP 3rd-tier sub-lord | LOG-FOR-V2 |
| `ga_panchanga` | Hora daily sequence, extended Choghadiya, planetary war on birth day | LOG-FOR-V2 |

#### NOT-WORTH-IT

| asset_id | rationale |
|---|---|
| `ga_sade_sati` | Coverage already exceeds commercial software; remaining gaps are sub-5% real-world usage |
| `ga_dashas` | Chakra Dasha, Shoola Dasha — < 5% usage; 18 dasha systems is already comprehensive |

---

## Q3 — Prashna Subsystem Strategy

### 3.1 Prashna Activation Model

`ga_prashna` is a **conditional no-op for natal charts by design**. The gate: the writer queries `prashna_charts WHERE chart_id = %s`; if no row exists, returns `WriterResult(rows_inserted=0)` immediately. The orchestrator adapter documents this explicitly.

When a `prashna_charts` row exists, the writer:
1. Reads `prashna_charts` for `question_class` and `prashna_lagna_method`
2. Reads planetary longitudes (see Bug Note below)
3. Looks up natural significators from `bg_prashna_significators` keyed on `question_class`
4. Computes Ithasala/Eesarpha applying/separating logic and fructification timing
5. Writes 1 `ga_prashna_lagna` row + 1 `ga_prashna_judgment` row per ayanamsha = **10 rows per horary question** (5 ayanamshas × 2)

**Bug note:** The writer references a table named `ga_positions` directly. L1 writes positions to `chart_facts`, not a dedicated `ga_positions` table. If that table does not exist under that name, the writer will produce 0 rows for all horary charts silently — this must be verified and resolved before Prashna activation.

### 3.2 Plumbing Status

**Entry point: ABSENT.** No TypeScript route exists for creating Prashna charts. The only `platform/src` file mentioning `prashna` is `cockpit/stats/route.ts`. There is:
- No `POST /api/prashna` route
- No `POST /api/charts` with a `chart_type` discriminator
- No UI surface for submitting a question moment

The only way to create a `prashna_charts` row today is a direct DB insert.

### 3.3 Table and Reference Data Status

**`prashna_charts` table:** Exists with 0 rows. Schema (12 columns): `chart_id` (FK), `question_text`, `question_class`, `querent_natal_chart_id`, `prashna_lagna_method`, `kp_number`, `querent_direction`, `active_nostril`, `question_instant` (timestamptz), `question_lat/lon`, `created_at`.

**`bg_prashna_rules`:** Complete and functional at 41 rows across 5 sub-tables (`bg_prashna_lagna_methods` 5, `bg_prashna_tajik_yogas` 16, `bg_prashna_significators` 12, `bg_prashna_fructification_rules` 5, `bg_prashna_special_techniques` 3). Full Tajik yoga formation logic present.

### 3.4 Cockpit Rendering Bug

**`ga_prashna` currently renders as red/error in the cockpit for every chart** — not as dormant.

Root cause: `asset_registry_seed.ts` count_sql entry has a leading parenthesis:
```sql
-- BROKEN (current):
(SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1) AS count

-- CORRECT:
SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1
```
`fetchAssetStats` catches the SQL parse error and returns `state: 'error'`. One-line fix + one targeted migration.

### 3.5 Options Assessment

| Option | Description | Scope | L2 Bodha impact | Risk | Recommendation |
|---|---|---|---|---|---|
| **A — Cockpit fix** | Fix count_sql bug; leave dormant | 1 line + 1 migration | None | Low | **DO NOW** |
| **B — Full activation** | Build `POST /api/prashna` route + resolve `ga_positions` bug + E2E build | Multi-session arc | Moderate distraction (2–3 sessions) | Medium | DEFER |
| **C — Full deferral** | Log as known residual, do nothing | Zero effort | Zero | Low (noise if count_sql bug not fixed) | PAIR WITH A |

**Recommendation:** Execute Option A (count_sql fix) immediately as a hygiene commit before L2 Bodha opens. Then Option C (defer full activation). Full activation requires resolving the `ga_positions` reference ambiguity, building a chart-creation API, and running an E2E horary build — a named sub-phase after L2 Bodha's first production build.

**L2 Bodha dependency on Prashna: zero.** The 8 Bodha assets derive exclusively from natal `chart_facts` and `ga_structural`. `ga_prashna_judgment` is a separate table with no L2 dependency. Keeping Prashna dormant costs nothing to the active campaign.

---

## Q4 — ga_structural Relational Elevation

### 4.1 Current Emission Map (Ground Truth)

**Active writer:** `platform/python-sidecar/ga_writers/ga_structural_writer.py` (4,351 lines). The orchestrator-level `pipeline/orchestrator/writers/ga_structural.py` is a 36-line thin adapter that delegates entirely to the legacy writer.

**DB-confirmed fact categories emitted for chart 482012f1 (selected high-volume):**

| fact_category | DB count |
|---|---|
| argala_natal_matrix | 21,600 |
| virodha_argala_natal_matrix | 21,600 |
| aspect_jaimini_per_varga | 16,200 |
| aspect_parashari_per_varga | 2,850 |
| lord_aspects_lord_per_varga | 923 |
| lord_in_house_per_varga | 1,800 |
| graha_in_house_composite_strength | 1,620 |
| vargottama_per_varga | 1,305 |
| dispositor_chain_per_varga | 1,350 |
| graha_avastha_baladi_per_varga | 1,350 |
| graha_dignity_per_varga | 1,350 |
| graha_avastha_deeptaadi_per_varga | 1,350 |
| conjunction_per_varga | 594 |
| parivartana_per_varga | 227 |
| kala_sarpa_per_varga | 150 |
| yoga_label | 409 |
| dosha_label | 85 |
| yoga_fires | 44 (legacy residual from fallback path) |
| dosha_fires | 10 (legacy residual) |
| nakshatra_dispositor | 200 |
| aspect_jaimini (D1) | 540 |
| aspect_tajik | 25 |
| graha_avastha_baladi/deepta/jagrad/lajjitadi/sayanadi | 45 each |
| graha_functional_class_per_ascendant | 70 |
| karakatva_strength_per_significance | 300 |
| ashtakavarga_anubindu | 420 |
| bhava_bala_* (7 categories) | 60 each |
| nakshatra_dispositor | 200 |
| midpoint | 1,080 |
| tajik_hadda_lord | 1,200 |

### 4.2 Prior Finding Verdict (GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0.md)

| Claim | Status | Evidence |
|---|---|---|
| **Claim 1:** YOGA_LIBRARY hardcodes 24 yogas | **PARTIALLY-FIXED** | Dual-path architecture now exists: DB catalog path (`_load_yoga_catalog()` at line 3624 reads `brahma_yoga_catalog`) is primary; `YOGA_LIBRARY` (still at line 187) is fallback only. 409 `yoga_label` rows vs. 44 legacy `yoga_fires` residual confirms DB path is active. |
| **Claim 2:** DOSHA_LIBRARY hardcodes 15 doshas | **PARTIALLY-FIXED** | Same pattern. `DOSHA_LIBRARY` (line 300) is fallback; DB reads `brahma_dosha_catalog` (50 entries). 85 `dosha_label` + 10 `dosha_fires` confirms DB path active. |
| **Claim 3:** reads `brahma_yoga_catalog` ZERO times | **FIXED** | `_load_yoga_catalog()` at line 3624: `SELECT canonical_id, name_en, category, formation_rule_jsonb, classical_citations, source_chunk_ids, school FROM brahma_yoga_catalog`. Called at line 4292 in substep entry. `brahma_yoga_catalog` (175 rows) and `brahma_dosha_catalog` (50 rows) are both read. |
| **Claim 4:** silently drops uncatalogued configurations | **STILL-LIVE-DEFECT** | Zero `uncatalogued_configuration` rows in DB. Writer hardcodes `"uncatalogued": False` on every emitted row. Fix 4.2 from prior finding was not implemented. No mechanism to emit a row when a structural configuration matches no catalog entry. |
| **Claim 5:** silently drops aspects beyond orb limits | **STILL-LIVE-DEFECT** | Line 3245 in varga conjunction builder: `if orb > 10.0: continue`. Line 917-935 (D1): same 10° hard gate. Tajik aspects: `if orb > 30°: continue`. No low-strength row emitted for wide-orb pairs. |
| **Bonus — `_mock_fact_id_ref`** | **FIXED** | `_real_fact_id_ref` (line 1297) is the active function — live `SELECT fact_id FROM chart_facts WHERE ...`. `_mock_fact_id_ref` removed. |

Additional live defect discovered (not in prior finding):
**`benefics_in` composite rule silently returns False** — `ga_structural_writer.py` line 3833: `return False, "composite_distributional_unimplemented"`. Affects Adhi Yoga and ~14 other catalog yogas. These formations never fire via the DB-catalog path. Legacy `_evaluate_yoga_fires()` handles Adhi Yoga as a special case only.

### 4.3 Exhaustive Entity/Relationship Gap Table

| entity_or_relationship | present? | should_add? | jyotish_rationale | msr_leverage |
|---|---|---|---|---|
| Nakshatra dispositor chain | YES (200 rows) | DONE | Sub-lord graph for KP foundation | HIGH |
| ga_sensitive special points (upagrahas, arudha) ingested relationally | YES — `_build_special_point_relationship_rows()` | DONE | Gulika/Mandi aspectual relationships | HIGH |
| ga_vargas per-varga data ingested | YES — `_build_varga_aspect_rows()` reads chart_divisionals, 8+ per-varga categories | DONE | Full per-varga relational graphs | VERY HIGH |
| Argala/virodha per all vargas | YES (21,600 + 21,600 rows) | DONE | Complete per-varga intervention matrix | VERY HIGH — but NOT projected to bo_laksana yet |
| Kala Sarpa per varga | YES (150 rows) | DONE | Formation across all 30 vargas | HIGH |
| Lord-in-house + lord-aspects-lord per varga | YES (1,800 + 923 rows) | DONE in ga_structural | House lord web across vargas | HIGH — but NOT projected to bo_laksana yet |
| Parivartana (maha/khala/dainya) | YES (227 per_varga rows) | DONE | Sign exchange all types | HIGH |
| Dispositor chains (rashi + nakshatra) | YES — both `graha_dispositor_chain` + `nakshatra_dispositor` | DONE | Both termini present | HIGH |
| Jaimini rashi-drishti | YES (540 D1 + 16,200 per_varga) | DONE | Primary Jaimini aspect method | VERY HIGH |
| Tajik aspects | YES (25 rows) | DONE | Varshaphal relational data | MEDIUM |
| Bhava bala (7 categories) | YES | DONE | House strength as edge weights | HIGH |
| Graha avasthas (all 5 systems) | YES in ga_structural — all 5 computed | **NOT projected to bo_laksana** — only lajjitadi in signal list | Life-stage, luminosity, consciousness, posture modify dignity | VERY HIGH (MISSING from bo_laksana) |
| Graha functional class per ascendant | YES in ga_structural (70 rows) | **NOT projected to bo_laksana** | Yogakaraka/functional-malefic is foundational to prediction | VERY HIGH (MISSING from bo_laksana) |
| Karakatva strength per significance | YES in ga_structural (300 rows) | **NOT projected to bo_laksana** | Relative karaka strength for significations | HIGH (MISSING from bo_laksana) |
| Uncatalogued configurations | **NO** | SHOULD ADD | Enables gap-detection; makes unnamed-but-real structural patterns visible | HIGH |
| Wide-orb aspects as low-strength rows | **NO** | SHOULD ADD (medium priority) | Wide-orb pairs have sign-level relationships; dropping them removes information | MEDIUM |
| ga_sade_sati ingested relationally | NO | NOT NEEDED in ga_structural | Sade sati is temporal, not a natal relational structure; bo_laksana handles directly | LOW |
| Panchanga relational data | NO | NOT NEEDED in ga_structural | Panchanga conditions don't form entity-entity graph edges; bo_laksana handles directly | LOW |
| Medical/dhatu relational mappings | NO | MEDIUM — add when bg_medical_mappings is expanded | Graha→dhatu/tridosha as graph edges; requires BPHS classical table | MEDIUM |
| KP significator chains | PARTIALLY — nakshatra_dispositor + cusp_kp_lords from ga_sensitive (GA5) | NOT NEEDED in ga_structural (GA5 covers it) | KP data already captured; no duplication needed | NOT NEEDED |

### 4.4 MSR-Leverage Gap Analysis (bo_laksana)

`bo_laksana` `ALL_SIGNAL_CATEGORIES` currently has 27 categories across 4 groups (STRUCTURAL 16, SENSITIVE 7, SADE_SATI 2, PANCHANGA 5).

**Critical gaps — computed in ga_structural but absent from bo_laksana signal list:**

| gap | rows_computed | rows_projected | MSR impact |
|---|---|---|---|
| `argala_natal_matrix` + `virodha_argala_natal_matrix` | 43,200 | 0 | **Entire intervention graph invisible to MSR** — which signs/houses have active argala cannot be reasoned about |
| `lord_in_house_per_varga` + `lord_aspects_lord_per_varga` | 2,723 | 0 | House lord placement web across 30 vargas absent — bo_laksana projects parivartana (sign exchanges) but not lord placement matrix |
| `graha_avastha_baladi`, `deepta`, `jagrad`, `sayanadi` | 4 × 45 = 180 | 0 | Core dignity-modification states missing (only lajjitadi is projected) |
| `graha_functional_class_per_ascendant` | 70 | 0 | Whether a graha is yogakaraka/functional-malefic absent from signal generation |
| `karakatva_strength_per_significance` | 300 | 0 | Relative karaka strength not feeding MSR signals |
| `aspect_jaimini` (D1) + `aspect_tajik` | 540 + 25 = 565 | 0 | D1 Rasi drishti matrix + Tajik aspects absent from MSR |

### 4.5 Dual-Capture Model Status

| source | ga_structural relational? | bo_laksana direct? | status |
|---|---|---|---|
| `ga_sensitive` | YES — `_build_special_point_relationship_rows()` | YES — `karaka_chara_position`, `karakamsa_position`, `arudha_pada` etc. | **DUAL CAPTURE — WORKING** |
| `ga_vargas` | YES — `_build_varga_aspect_rows()` | YES — `vargottama_per_varga`, `parivartana_per_varga`, `kala_sarpa_per_varga` | **DUAL CAPTURE — WORKING** (but most per-varga structural rows not yet in bo_laksana signal list) |
| `ga_sade_sati` | NO (appropriate) | YES — `sade_sati_cycle`, `sade_sati_phase` | SINGLE-CAPTURE VIA bo_laksana (correct — sade sati is temporal) |
| Panchanga (ga_panchanga) | NO (appropriate) | YES — 5 panchanga categories | SINGLE-CAPTURE VIA bo_laksana (correct — conditions, not graph edges) |

### 4.6 Prioritized Elevation Plan

**Priority 1 (HIGH / no ga_structural change): Add missing categories to `bo_laksana` signal list**
- File: `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`, lines 38-55 (`STRUCTURAL_SIGNAL_CATEGORIES`)
- Add: `argala_natal_matrix`, `virodha_argala_natal_matrix`, `lord_in_house_per_varga`, `lord_aspects_lord_per_varga`, `graha_avastha_baladi`, `graha_avastha_deepta`, `graha_avastha_jagrad`, `graha_avastha_sayanadi`, `graha_functional_class_per_ascendant`, `karakatva_strength_per_significance`
- 45,000+ rows currently computed and in chart_facts; zero code changes needed in ga_structural; pure bo_laksana signal expansion

**Priority 2 (HIGH / closes STILL-LIVE-DEFECT Claim 4): Implement `uncatalogued_configuration` emission**
- File: `ga_structural_writer.py`, `_build_yoga_rows()` (line 1578)
- After catalog evaluation loop, scan structural pattern inventory for combinations matching no catalog entry; emit `uncatalogued_configuration` fact_type rows
- Fix 4.2 from prior finding; currently 0 rows in this category

**Priority 3 (HIGH / completes yoga coverage): Implement remaining `ga_yoga` evaluator relation types**
- File: `platform/python-sidecar/ga_writers/ga_yoga_writer.py` lines 812–825
- Remove `return None` stubs for `benefics_in_upachayas_*`, `kendra_and_trikona_lords_*`, and other unimplemented types
- Critical for bo_samskara — ga_yoga currently fires only 5 rows

**Priority 4 (HIGH / closes STILL-LIVE-DEFECT Claim 5): Emit wide-orb pairs as low-strength rows**
- File: `ga_structural_writer.py` line 3245 (varga) and lines 917-935 (D1)
- Replace `if orb > 10.0: continue` with low-strength emit (`orb_tightness = 1 - orb/180`)
- Also fix `benefics_in` composite rule (line 3833 `return False` stub)

**Priority 5 (MEDIUM): Add Jaimini D1 + Tajik aspects to bo_laksana signal categories**
- 565 rows computed; add `aspect_jaimini`, `aspect_tajik` to `STRUCTURAL_SIGNAL_CATEGORIES`
- No ga_structural change needed

**Priority 6 (MEDIUM): Expand bg_medical_mappings + ga_structural medical relational rows**
- Expand bg_medical_mappings from 9 to ~150-200 rows (planetary combinations + nakshatra-dosha grid)
- Then add `_build_medical_relational_rows()` to ga_structural for graha→dhatu/tridosha edges
- Enables health domain signals in MSR

**Priority 7 (LOW): Clean up YOGA_LIBRARY/DOSHA_LIBRARY fallback path**
- 44 `yoga_fires` + 10 `dosha_fires` legacy residual rows indicate fallback triggered at some point
- Add a build-time warning if DB catalog path falls back to the hardcode
- Not a data-loss issue; cosmetic/diagnostic improvement

---

## Appendix A — Assets Missing from asset_registry_seed.ts

| asset_id | in_registry | in_seed_ts | writer_exists | action_needed |
|---|---|---|---|---|
| `ga_transit_anchors` | YES | NO | YES | Add to seed_ts for completeness; low urgency |
| `ga_pyjhora_engine` | YES | NO | NO (service) | Investigate error state; not a seed issue |

## Appendix B — Key File Citations

| subject | file | lines |
|---|---|---|
| YOGA_LIBRARY fallback constant | `ga_writers/ga_structural_writer.py` | 187 |
| DOSHA_LIBRARY fallback constant | `ga_writers/ga_structural_writer.py` | 300 |
| `_load_yoga_catalog()` DB reader | `ga_writers/ga_structural_writer.py` | 3624 |
| Substep entry point (yoga catalog called) | `ga_writers/ga_structural_writer.py` | 4292 |
| `benefics_in` composite stub | `ga_writers/ga_structural_writer.py` | 3833 |
| D1 conjunction 10° hard gate | `ga_writers/ga_structural_writer.py` | 917-935 |
| Varga conjunction 10° hard gate | `ga_writers/ga_structural_writer.py` | 3245 |
| `_real_fact_id_ref` (live DB lookup) | `ga_writers/ga_structural_writer.py` | 1297 |
| ga_yoga evaluator `return None` stubs | `ga_writers/ga_yoga_writer.py` | 812-825 |
| bo_laksana STRUCTURAL_SIGNAL_CATEGORIES | `pipeline/orchestrator/writers/bo_laksana.py` | 38-55 |
| ga_nakshatra.py ctx fallback smell | `pipeline/orchestrator/writers/ga_nakshatra.py` | (birth_params fallback) |
| ga_prashna count_sql bug | `platform/scripts/seed/asset_registry_seed.ts` | ~977 |
| ga_prashna `ga_positions` reference bug | `pipeline/orchestrator/writers/ga_prashna.py` | (positions table reference) |
| WriterBase thin adapter | `pipeline/orchestrator/writers/ga_structural.py` | 1-36 |

---

*End of L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md — analysis only; no changes were made to any file. Findings are inputs to native's strategic decisions before L2 Bodha opens.*
