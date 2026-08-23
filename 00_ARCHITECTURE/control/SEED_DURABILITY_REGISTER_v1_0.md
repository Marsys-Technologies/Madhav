---
canonical_id: SEED_DURABILITY_REGISTER
version: 1.0
status: CURRENT
generated_at: 2026-08-23T06:36:35Z
campaign: NIRMĀṆA — Track M0, task M0-T29
authored_by: KĀRAKA (M0-T29). NOT self-certified — I16/H7. PARĪKṢAKA verifies.
regenerate: python3 00_ARCHITECTURE/control/seed_durability/seed_durability_register.py
---

# SEED DURABILITY REGISTER v1.0

**The question.** A repair written straight to `asset_registry` survives only if its
column is absent from `asset_registry_seed.ts`'s `ON CONFLICT (asset_id) DO UPDATE SET`
list. A column in that list is restored from `EXCLUDED` on the next seed run. A green
resting on such a column is a green a re-seed silently undoes — strictly worse than a
red, because nothing announces its expiry.

M0-T27 built the post-reseed projection that made this measurable, and declared its own
bound: it modelled **4 of the 23** seed-overwritten columns and was therefore a LOWER
BOUND. This register closes that gap.

## 0 — Headline, and this register's own bound

- **Columns modelled / columns a re-seed writes: 23/23.**
- Cells a re-seed would change today: **260**, across **96** distinct assets.
- Cells this register could not determine (`UNKNOWN`): **0**.
- Live `asset_registry`: 128 rows × 40 columns; seed entries parsed: 127.

**The honest summary, stated before the detail:** most of what this campaign has
repaired is durable, and the register did not have to hunt for that answer. The four
Asset-Catalogue-Contract columns (`domain`, `rung`, `superseded_by`,
`data_disposition`), `has_substeps`, `has_writer`, `integrity_check_sql`,
`clear_tables`, `service_health` and `writer_timeout_seconds` are **not written by the
seed at all** — no INSERT, no UPDATE. Repairs to them cannot be reverted by a re-seed.
Two real exposures remain, both already named by M0-T27 and both re-measured
independently here (§3), plus a third this register found while modelling the other 19
columns (§3.6). Everything else is prose and labels.

## 1 — What the seed writes: the complete column list

Parsed from the text of `platform/scripts/seed/asset_registry_seed.ts` (D-13: never imported, never executed — its `main()` runs the upsert, and D-17 records that it refuses dry-run requests too). Evidence line numbers are that file's.

The `INSERT INTO asset_registry ( … )` column list (:3274) names **25** columns. The `ON CONFLICT (asset_id) DO UPDATE SET` body (:3283) names **23**.

### 1.1 — Group A · written on INSERT only

Set once when the seed creates a row; never touched again on a re-run.

| column | evidence |
|---|---|
| `asset_id` | the conflict key itself (`ON CONFLICT (asset_id)`, :3283) |
| `estimated_seconds` | present in the INSERT list (:3274-3281), absent from the DO UPDATE SET body (:3283-3319). The interface comments it `always null — measured on first build` (:43) |

### 1.2 — Group B · written on `ON CONFLICT DO UPDATE` — **the dangerous set**

**21 columns**, each assigned unconditionally from `EXCLUDED`. Anything hand-written into one of these is reverted on the next seed run unless it happens to equal what the seed would write.

| column | consequence class | rows a re-seed changes today |
|---|---|---|
| `scope` | CORRECTNESS | 1 |
| `asset_type` | CONTRACT | 6 |
| `asset_kind` | CONTRACT | 2 |
| `layer` | CONTRACT | 0 |
| `provides_apis` | CONTRACT | 0 |
| `storage_type` | CONTRACT | 0 |
| `count_sql` | OPERATIONAL | 28 |
| `target_floor` | OPERATIONAL | 27 |
| `depends_on` | OPERATIONAL | 25 |
| `target_table` | OPERATIONAL | 3 |
| `health_probe` | OPERATIONAL | 0 |
| `volume_explanation` | COSMETIC | 47 |
| `english_description` | COSMETIC | 23 |
| `layer_index` | COSMETIC | 21 |
| `layer_name` | COSMETIC | 20 |
| `sanskrit_name` | COSMETIC | 20 |
| `sort_order` | COSMETIC | 10 |
| `english_name` | COSMETIC | 8 |
| `size_sql` | COSMETIC | 7 |
| `expected_volume_formula` | COSMETIC | 6 |
| `expected_volume_inputs` | COSMETIC | 1 |

Three of these are not simple `EXCLUDED` copies — the seed **derives** the value in `main()` before binding it, and a column absent from a seed entry is therefore **written with a default, not left alone**. This is the single most reversible mistake in reading the file and the reason the asset_kind finding is real:

```ts
const assetType  = asset.asset_type  ?? 'data'                                  // :3267
const assetKind  = asset.asset_kind  ?? 'data'                                  // :3268
const layerName  = asset.layer_name  ?? layerNames[asset.layer]  ?? asset.layer  // :3269
const layerIndex = asset.layer_index ?? layerIndices[asset.layer] ?? null        // :3270
const catalogStatus = asset.catalog_status
                   ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')       // :3271
```

Two further pre-upsert mutations of the in-memory `ASSETS` array are modelled here:

- `:3222-3231` — pre-flight `to_regclass(target_table)`; any asset whose declared target table is absent from the target DB has `is_active` forced to `false` **before** the upsert binds it.
- `:3205` — `mi_jivanaghatana.expected_volume_inputs` is overwritten with a live `FILE_COUNT` of the LEL file (measured here: **56**).

### 1.3 — Group C · guarded by a `CASE` that preserves the DB value

**2 columns**: `catalog_status`, `is_active`.
This is the existing precedent for a durable-by-construction column, and the pattern any fix to Group B would follow. The file explains itself, verbatim (:3299-3312):

```sql
-- MR-06 (PARISHKARA cutover durability): RETIRED guard.
-- A RETIRED asset (e.g. ka_gochara_sweep post W6.4 cutover) must NEVER
-- be resurrected by a re-seed. If the existing DB row is already RETIRED,
-- preserve that status and the corresponding is_active=false rather than
-- blindly overwriting with whatever the seed says. This is the ON-CONFLICT
-- analogue of migration 563's one-way transition: CURRENT→RETIRED is
-- irreversible by the seed; only an explicit native-authorized migration
-- can reverse it.
catalog_status = CASE WHEN asset_registry.catalog_status = 'RETIRED'
                      THEN asset_registry.catalog_status
                      ELSE EXCLUDED.catalog_status END,
is_active = CASE WHEN asset_registry.catalog_status = 'RETIRED'
                 THEN asset_registry.is_active
                 ELSE EXCLUDED.is_active END,
```

Read what the guard actually covers: it is keyed on `catalog_status = 'RETIRED'` and nothing else. It protects a RETIRED row's status and activity. It does **not** protect any other column of a RETIRED row, and it protects **nothing** on a CURRENT or DRAFT row. An honest note on its current state: the one RETIRED row live today (`ka_gochara_sweep`) is also declared `RETIRED` / `is_active: false` in the seed itself, so the guard agrees with `EXCLUDED` and has **not been exercised** — it is correct, and it is currently untested by production data.

### 1.4 — Group D · never written by the seed at all

**15 live columns** appear in neither the INSERT list nor the DO UPDATE body. A repair to one of these cannot be reverted by a re-seed. This is where most of the campaign's repair work landed.

`clear_tables`, `created_at`, `data_disposition`, `domain`, `has_substeps`, `has_writer`, `integrity_check_sql`, `last_invoked_at`, `last_selftest_at`, `rebuild_on_probe_fail`, `rung`, `selftest_detail`, `service_health`, `superseded_by`, `writer_timeout_seconds`

The compensating hazard, and it is real: because the seed never *inserts* these columns either, **any asset the seed newly creates lands with all of them at their DB default** — NULL unless a NOT NULL/DEFAULT says otherwise. Today's rows are safe; future rows are not covered by anything in the seed.

## 2 — Per column: would a re-seed change a live row, and which?

The core measurement. For each of the 23 seed-written columns, the value the seed would write for each asset (defaults and derivations applied) is compared against the live value. Comparison is type-normalised: `jsonb` against the seed's `JSON.stringify` output, `text[]` as an ordered list, numerics as numbers.

| column | class | changed | seed fills a live NULL | seed NULLs a live value | both non-null, differ | UNKNOWN |
|---|---|---:|---:|---:|---:|---:|
| `volume_explanation` | unconditional | **47** | 41 | 0 | 6 | 0 |
| `count_sql` | unconditional | **28** | 0 | 2 | 26 | 0 |
| `target_floor` | unconditional | **27** | 3 | 14 | 10 | 0 |
| `depends_on` | unconditional | **25** | 0 | 0 | 25 | 0 |
| `english_description` | unconditional | **23** | 0 | 0 | 23 | 0 |
| `layer_index` | unconditional | **21** | 15 | 0 | 6 | 0 |
| `layer_name` | unconditional | **20** | 15 | 0 | 5 | 0 |
| `sanskrit_name` | unconditional | **20** | 0 | 0 | 20 | 0 |
| `sort_order` | unconditional | **10** | 0 | 0 | 10 | 0 |
| `english_name` | unconditional | **8** | 0 | 0 | 8 | 0 |
| `size_sql` | unconditional | **7** | 7 | 0 | 0 | 0 |
| `asset_type` | unconditional | **6** | 0 | 0 | 6 | 0 |
| `expected_volume_formula` | unconditional | **6** | 6 | 0 | 0 | 0 |
| `catalog_status` | CASE-guarded | **4** | 0 | 0 | 4 | 0 |
| `target_table` | unconditional | **3** | 2 | 0 | 1 | 0 |
| `asset_kind` | unconditional | **2** | 0 | 0 | 2 | 0 |
| `expected_volume_inputs` | unconditional | **1** | 1 | 0 | 0 | 0 |
| `is_active` | CASE-guarded | **1** | 0 | 0 | 1 | 0 |
| `scope` | unconditional | **1** | 0 | 0 | 1 | 0 |
| `health_probe` | unconditional | **0** | 0 | 0 | 0 | 0 |
| `layer` | unconditional | **0** | 0 | 0 | 0 | 0 |
| `provides_apis` | unconditional | **0** | 0 | 0 | 0 | 0 |
| `storage_type` | unconditional | **0** | 0 | 0 | 0 | 0 |

Four columns — `health_probe`, `layer`, `provides_apis`, `storage_type` — are byte-identical between seed and live on every asset. They are in the dangerous set, but nothing currently diverges on them.

`direction` is mechanical, not a judgment: it reports which side is NULL, never which side is *right*. Where a cleanliness test exists in the campaign's own writing (migration 590 defines a well-formed `layer_index` as `^L[0-5]$`) it is applied and reported; nowhere else is a direction called good or bad.

**A second, weaker reading for the two SQL columns**, because a raw byte-difference count would overstate them: of `count_sql`'s 28 changed cells, **3** differ only in whitespace or keyword case — leaving **25 that are genuinely different queries**. For `size_sql` the figure is 0 of 7. Both readings are in the JSON; neither is treated as the authoritative one, because a re-seed writes different bytes in either case.

### 2.1 — Every divergent cell

The full list is machine-readable in `SEED_DURABILITY_REGISTER_v1_0.json` under `divergent_cells` (asset, column, live value, seed value, direction, and whether the seed entry *declared* the key or fell through to a default). Reproduced here are the cells in the CORRECTNESS, CONTRACT and OPERATIONAL classes — the prose/label columns are left to the JSON.

| asset | column | live | a re-seed writes | direction |
|---|---|---|---|---|
| `mi_jivanaghatana` | `scope` | `per_chart` | `global` | both non-null, values differ |
| `bg_ephemeris_engine` | `asset_kind` | `service` | `data` | both non-null, values differ |
| `bg_panchanga` | `asset_kind` | `service` | `data` | both non-null, values differ |
| `ka_dasha_kala` | `asset_type` | `service` | `data` | both non-null, values differ |
| `ka_graha_sancara` | `asset_type` | `service` | `data` | both non-null, values differ |
| `ka_muhurta_seva` | `asset_type` | `service` | `data` | both non-null, values differ |
| `ka_tulana` | `asset_type` | `service` | `data` | both non-null, values differ |
| `mi_abhilekha` | `asset_type` | `service` | `data` | both non-null, values differ |
| `mi_seva` | `asset_type` | `service` | `data` | both non-null, values differ |
| `bo_cdlm_summary` | `catalog_status` | `DRAFT` | `CURRENT` | both non-null, values differ |
| `bo_chart_gestalt` | `catalog_status` | `DRAFT` | `CURRENT` | both non-null, values differ |
| `ga_vichara` | `catalog_status` | `DRAFT` | `CURRENT` | both non-null, values differ |
| `ka_kshetra` | `catalog_status` | `CURRENT` | `DRAFT` | both non-null, values differ |
| `bg_class_priors` | `count_sql` | `SELECT COUNT(*) FROM brahma_class_priors` | `SELECT count(*) FROM brahma_class_priors` | both non-null, values differ |
| `bg_formula_constants` | `count_sql` | `SELECT COUNT(*) FROM brahma_formula_constants WHERE class != 'conflation_bug'` | `SELECT count(*) FROM brahma_formula_constants` | both non-null, values differ |
| `bg_ghatana` | `count_sql` | `SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count` | `SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count` | both non-null, values differ |
| `bg_reference` | `count_sql` | `SELECT
  (SELECT count(*) FROM reference_planets) +
  (SELECT count(*) FROM reference_signs) +
  (SELECT count(*) FROM reference_aspects) +
  (SELECT count(*) F…[+361]` | `SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM refe…[+471]` | both non-null, values differ |
| `bg_sky_calendar` | `count_sql` | `SELECT COUNT(*) FROM bg_sky_calendar` | `SELECT COUNT(*) FROM bg_sky_events` | both non-null, values differ |
| `bg_texts` | `count_sql` | `SELECT
  (SELECT count(*) FROM classical_texts) +
  (SELECT count(*) FROM classical_text_chunks) AS count` | `SELECT count(*) FROM classical_text_chunks` | both non-null, values differ |
| `bg_yogas` | `count_sql` | `SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_y…[+14]` | `SELECT count(*) FROM brahma_yoga_catalog` | both non-null, values differ |
| `bo_karanajala` | `count_sql` | `SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1` | `SELECT (SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1) + (SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1) AS count` | both non-null, values differ |
| `bo_laksana` | `count_sql` | `SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ANY(ARRAY[
     'yoga','dosha','sade_sati','panchanga','karaka_alignment','tr…[+184]` | `SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1` | both non-null, values differ |
| `bo_pratijna` | `count_sql` | `SELECT COUNT(*) FROM bodha_pratijna WHERE chart_id=$1` | `SELECT count(*) FROM bodha_pratijna WHERE chart_id = $1` | both non-null, values differ |
| `bo_sangati` | `count_sql` | `SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1` | `SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1) + (SELECT count(*) FROM bodha_convergence WHERE chart_id = $1) + (SELECT count(*) FROM bodha_…[+44]` | both non-null, values differ |
| `bo_upaya` | `count_sql` | `
SELECT (
  (SELECT count(*) FROM bodha_rm_resonances           WHERE chart_id = $1) +
  (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1…[+13]` | `SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1) + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1) AS count` | both non-null, values differ |
| `ga_condition` | `count_sql` | `SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1)
       + (SELECT count(*) FROM chart_facts
          WHERE chart_id = $1
            AN…[+234]` | `SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1) + (SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'graha_a…[+29]` | both non-null, values differ |
| `ga_panchanga` | `count_sql` | `
SELECT count(*) AS count
FROM   chart_facts
WHERE  chart_id = $1
  AND  (
         fact_category LIKE 'panchanga%'
      OR fact_category = 'bhadra_flag'
     …[+203]` | `SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'panchanga%'` | both non-null, values differ |
| `ga_prashna` | `count_sql` | `
SELECT (
  (SELECT COUNT(*) FROM ga_prashna_lagna    WHERE chart_id = $1) +
  (SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1)
) AS count
` | `SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1` | both non-null, values differ |
| `ka_avadhi` | `count_sql` | `SELECT COUNT(*) FROM kala_avadhi WHERE chart_id=$1` | `SELECT count(*) FROM kala_avadhi WHERE chart_id = $1` | both non-null, values differ |
| `ka_taranga` | `count_sql` | `SELECT COUNT(*) FROM kala_taranga WHERE chart_id=$1` | `SELECT count(*) FROM kala_taranga WHERE chart_id = $1` | both non-null, values differ |
| `mi_abhilekha` | `count_sql` | `SELECT count(*) FROM mimamsa_journal WHERE chart_id = $1` | *(null)* | seed NULLS a live value |
| `mi_adhilepa` | `count_sql` | `SELECT
  (SELECT count(*) FROM mimamsa_load_bearing           WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_convergence_adjustment WHERE chart_id = $1)…[+243]` | `SELECT count(*) FROM mimamsa_signal_adjustment WHERE chart_id = $1` | both non-null, values differ |
| `mi_bhara` | `count_sql` | `SELECT COUNT(*) FROM kala_field_skill WHERE chart_id = $1` | `SELECT count(*) FROM kala_field_skill WHERE chart_id = $1` | both non-null, values differ |
| `mi_bhavisya` | `count_sql` | `SELECT (SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_manifestation_sets WHERE chart_id = $1) AS count` | `SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1` | both non-null, values differ |
| `mi_darshana` | `count_sql` | `SELECT (SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_insight_embeddings WHERE chart_id = $1) AS count` | `SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1` | both non-null, values differ |
| `mi_jivanaghatana` | `count_sql` | `SELECT count(*) FROM mimamsa_event_provenance WHERE chart_id = $1` | `SELECT count(*) FROM mimamsa_event_provenance` | both non-null, values differ |
| `mi_kula` | `count_sql` | `SELECT
  (SELECT count(*) FROM mimamsa_signal_families) +
  (SELECT count(*) FROM mimamsa_negative_controls) AS count` | `SELECT count(*) FROM mimamsa_signal_families` | both non-null, values differ |
| `mi_pariksha` | `count_sql` | `SELECT (SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_attribution WHERE chart_id = $1) + (SELECT count(*) FROM mimam…[+44]` | `SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1` | both non-null, values differ |
| `mi_pramana` | `count_sql` | `SELECT (SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_reliability WHERE chart_id = $1) AS count` | `SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1` | both non-null, values differ |
| `mi_seva` | `count_sql` | `SELECT count(*) FROM mimamsa_preferences` | *(null)* | seed NULLS a live value |
| `ph_rectification` | `count_sql` | `SELECT (SELECT count(*) FROM phala_rectification WHERE chart_id = $1) + (SELECT count(*) FROM phala_rectification_best WHERE chart_id = $1) AS count` | `SELECT count(*) FROM phala_rectification WHERE chart_id = $1` | both non-null, values differ |
| `bo_anveshana` | `depends_on` | `["bo_sangati", "bo_karanajala", "bo_samskara", "bo_drishti", "bo_bimba", "bo_laksana"]` | `["bo_sangati", "bo_karanajala", "bo_samskara", "bo_drishti"]` | both non-null, values differ |
| `bo_karanajala` | `depends_on` | `["bo_laksana", "bo_bimba", "ga_positions"]` | `["bo_laksana", "bo_bimba"]` | both non-null, values differ |
| `bo_laksana` | `depends_on` | `["bg_rules", "ga_positions", "ga_strength", "ga_sensitive", "ga_panchanga", "ga_sade_sati", "ga_structural", "ga_nakshatra", "ga_condition", "ga_vargas", "ga_vi…[+7]` | `["ga_structural", "ga_vichara", "bg_rules"]` | both non-null, values differ |
| `bo_pramana_mapa` | `depends_on` | `["bo_upaya", "bo_drishti", "bo_anveshana", "bo_laksana", "bo_sangati", "bo_bimba", "bo_karanajala", "bo_samskara"]` | `["bo_upaya", "bo_drishti", "bo_anveshana"]` | both non-null, values differ |
| `bo_pratijna` | `depends_on` | `["bo_laksana", "bo_sangati"]` | `["bo_laksana", "bg_ghatana"]` | both non-null, values differ |
| `bo_samvada` | `depends_on` | `["bo_laksana", "bo_karanajala", "bo_upaya", "bo_sangati", "bo_pramana_mapa"]` | `["bo_laksana"]` | both non-null, values differ |
| `bo_sangati` | `depends_on` | `["bo_laksana", "bo_karanajala"]` | `["bo_laksana"]` | both non-null, values differ |
| `ga_sade_sati` | `depends_on` | `["ga_positions", "ga_strength", "ga_panchanga", "ga_vargas", "ga_dashas", "ga_structural", "ga_nakshatra"]` | `["ga_positions", "ga_strength", "ga_panchanga", "ga_vargas", "ga_dashas", "ga_structural"]` | both non-null, values differ |
| `ga_strength` | `depends_on` | `["ga_positions", "ga_vargas"]` | `["ga_positions"]` | both non-null, values differ |
| `ga_structural` | `depends_on` | `["ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions", "ga_sensitive", "ga_strength", "ga_vargas"]` | `["ga_positions", "ga_strength", "ga_panchanga", "ga_sensitive", "ga_vargas", "ga_dashas", "ga_nakshatra"]` | both non-null, values differ |
| `ga_tajaka` | `depends_on` | `["ga_positions", "ga_dashas", "ga_sensitive"]` | `["ga_positions", "ga_dashas"]` | both non-null, values differ |
| `ka_bhavishya_lekha` | `depends_on` | `["ka_kala_darshana", "ka_vighnakara", "ka_sangam", "bo_laksana"]` | `["ka_kala_darshana", "ka_vighnakara"]` | both non-null, values differ |
| `ka_jivana_parva` | `depends_on` | `["ka_kala_darshana", "ka_dasha_kala", "ka_sangam", "ka_yojaka", "ga_dashas"]` | `["ka_kala_darshana", "ka_dasha_kala"]` | both non-null, values differ |
| `ka_kalasutra` | `depends_on` | `["ka_yojaka", "ka_sangam", "bo_laksana"]` | `["ka_yojaka", "ka_sangam"]` | both non-null, values differ |
| `ka_sangam` | `depends_on` | `["ka_yojaka", "ka_dasha_kala", "ka_gochara", "ka_muhurta_seva", "bo_laksana", "ga_dashas", "ga_strength", "ga_positions", "ga_tajaka", "bg_transit_rules"]` | `["ka_yojaka", "ka_dasha_kala", "ka_gochara", "ka_muhurta_seva"]` | both non-null, values differ |
| `ka_vedha_gochara` | `depends_on` | `["ga_positions", "bg_ephemeris", "bg_transit_rules", "bg_sarvatobhadra_grid", "bg_vedha_malefic_scale", "bg_phaladeepika_latta"]` | `["ga_positions", "bg_ephemeris", "bg_transit_rules"]` | both non-null, values differ |
| `ka_vighnakara` | `depends_on` | `["ka_sangam", "ka_gochara", "ka_muhurta_seva", "ga_positions"]` | `["ka_sangam", "ka_gochara", "ka_muhurta_seva"]` | both non-null, values differ |
| `mi_adhilepa` | `depends_on` | `["mi_gunanaka", "bo_laksana", "ka_sangam", "ph_nimitta", "ga_positions"]` | `["mi_gunanaka"]` | both non-null, values differ |
| `mi_bhavisya` | `depends_on` | `["ph_pramana", "ph_nimitta", "ph_phaladesa", "mi_kula", "mi_jivanaghatana", "bo_laksana"]` | `["ph_pramana", "ph_nimitta", "ph_phaladesa", "mi_kula", "mi_jivanaghatana"]` | both non-null, values differ |
| `mi_sambandha` | `depends_on` | `["mi_pramana", "mi_pariksha", "mi_bhavisya"]` | `["mi_pramana", "mi_pariksha"]` | both non-null, values differ |
| `ph_muhurta` | `depends_on` | `["ph_nimitta", "ka_kalasutra", "ga_panchanga", "ka_vighnakara", "ga_condition", "ka_gochara", "ga_positions", "ka_sangam"]` | `["ph_nimitta", "ka_kalasutra", "ga_panchanga"]` | both non-null, values differ |
| `ph_nimitta` | `depends_on` | `["ka_sangam", "ka_bhavishya_lekha", "bo_bimba", "bo_samskara", "bo_karanajala", "bo_sangati", "bo_anveshana", "bo_cgm_paths", "bo_laksana"]` | `["ka_sangam", "ka_bhavishya_lekha", "bo_bimba", "bo_samskara", "bo_karanajala", "bo_sangati"]` | both non-null, values differ |
| `ph_phaladesa` | `depends_on` | `["ph_nimitta", "ph_muhurta", "ph_pratikara", "ph_suddha_sodhana", "ph_sankrama", "ph_pramana", "bo_laksana"]` | `["ph_nimitta", "ph_muhurta", "ph_pratikara", "ph_suddha_sodhana", "ph_sankrama", "ph_pramana"]` | both non-null, values differ |
| `ph_pratikara` | `depends_on` | `["ph_nimitta", "bo_upaya", "ka_vighnakara", "ka_sangam"]` | `["ph_nimitta", "bo_upaya", "ka_vighnakara"]` | both non-null, values differ |
| `ph_suddha_sodhana` | `depends_on` | `["ph_sodhana", "ph_nimitta"]` | `["ph_sodhana"]` | both non-null, values differ |
| `bg_sky_calendar` | `is_active` | `true` | `false` | both non-null, values differ · guard: pre-flight forced false |
| `bg_class_priors` | `target_floor` | *(null)* | `164` | seed FILLS a live NULL |
| `bg_formula_constants` | `target_floor` | *(null)* | `14` | seed FILLS a live NULL |
| `bg_ghatana` | `target_floor` | *(null)* | `34` | seed FILLS a live NULL |
| `bg_parihara_rules` | `target_floor` | `447` | `439` | both non-null, values differ |
| `bo_anveshana` | `target_floor` | `500` | `5770` | both non-null, values differ |
| `bo_cdlm_summary` | `target_floor` | `1` | `5` | both non-null, values differ |
| `bo_cgm_paths` | `target_floor` | `9` | `5` | both non-null, values differ |
| `bo_chart_gestalt` | `target_floor` | `1` | `5` | both non-null, values differ |
| `bo_laksana` | `target_floor` | `60000` | `66738` | both non-null, values differ |
| `bo_pratijna` | `target_floor` | `0` | `110` | both non-null, values differ |
| `bo_samskara` | `target_floor` | `60000` | `66738` | both non-null, values differ |
| `bo_sangati` | `target_floor` | `70` | `84` | both non-null, values differ |
| `ga_vargas` | `target_floor` | `22092` | `21635` | both non-null, values differ |
| `ka_dasha_kala` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `ka_tulana` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_abhilekha` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_adhilepa` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_bhavisya` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_darshana` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_gunanaka` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_jivanaghatana` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_kula` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_pariksha` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_pramana` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_sambandha` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_seva` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `mi_vistara` | `target_floor` | `0` | *(null)* | seed NULLS a live value |
| `bo_cdlm_summary` | `target_table` | *(null)* | `bodha_cdlm_chart_summary` | seed FILLS a live NULL |
| `bo_chart_gestalt` | `target_table` | *(null)* | `bodha_chart_gestalt` | seed FILLS a live NULL |
| `mi_adhilepa` | `target_table` | `mimamsa_load_bearing` | `mimamsa_signal_adjustment` | both non-null, values differ |

## 3 — Per campaign repair: durable or not

### 3.1 — `has_substeps` (M0-T20, 12 rows) — **DURABLE**

- Columns: `has_substeps`
- In the seed's `DO UPDATE SET` list: none
- Not written by the seed at all: `has_substeps`
- Rows a re-seed would change: **0**

**Verdict.** DURABLE — the column is absent from the seed's INSERT list entirely, so no seed run reads or writes it

**Consequence if reverted.** CORRECTNESS. has_substeps gates asset_runner.py's substep-plan-completeness predicate (CLAUDE.md §N.8 instance 4): plan_complete is initialised True and only recomputed inside `if has_substeps:`. A false-negative flag switches the detector OFF and lets `lit` be written on a proxy — the H4/I5 defect class.

Verified independently of M0-T27 rather than inherited from it. The check is not "the projection did not fire" but the stronger structural one: `has_substeps` is not in the seed's INSERT column list, so no seed run can name it in an assignment. Live rows with `has_substeps IS TRUE` today: **26**.

One caveat that belongs to Group D, not to this repair: an asset the seed newly inserts lands with `has_substeps` NULL, and a NULL is falsy at `asset_runner.py`'s `if has_substeps:`. The repair is durable; the *coverage* of future rows is not enforced by anything.

### 3.2 — `asset_kind` / `asset_type` (M0-T21, 6 rows) — **REVERTED on all 8 divergent rows**

- Columns: `asset_kind`, `asset_type`
- In the seed's `DO UPDATE SET` list: `asset_kind`, `asset_type`
- Not written by the seed at all: none
- Rows a re-seed would change: **8**

**Verdict.** REVERTED — both columns are in the unconditional DO UPDATE SET list and the seed supplies a `?? 'data'` default for each, so an entry that omits the key is written with 'data', not left alone

**Consequence if reverted.** CORRECTNESS-ADJACENT. asset_kind/asset_type drive per-kind catalogue-contract rules (which required fields apply) and service-vs-data routing. Reverting a 'service' to 'data' re-opens the contract violations M0-T21 closed.

Independently re-measured; agrees with M0-T27's figure. The mechanism is the `?? 'data'` default at `:3267-3268`, and it is the reason the count is 8 rather than 6: **not one of the eight seed entries declares the key at all**. Every one of these reversions is a default being actively written over a correct value, not a stale literal.

- `asset_kind` → `'data'`: `bg_ephemeris_engine`, `bg_panchanga`
- `asset_type` → `'data'`: `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`, `mi_abhilekha`, `mi_seva`

### 3.3 — `domain` / `rung` (migration 590, 128 rows) — **columns durable, the PAIR is not**

- Columns: `domain`, `rung`
- In the seed's `DO UPDATE SET` list: none
- Not written by the seed at all: `domain`, `rung`
- Rows a re-seed would change: **0**

**Verdict.** domain/rung themselves are DURABLE (neither is written by the seed at all) — but the PAIR is not: 1 row(s) would end up internally inconsistent because `scope` moves under them

**Consequence if reverted.** CORRECTNESS. domain is the planner's split axis (plan §6.2) and rung is the layer-ladder position (§8.4). A domain that contradicts its own scope makes contract rule C-18/C-19 fire and makes I13's 'which rung owns this asset' question answerable two different ways.

`domain` and `rung` are in Group D — the seed writes neither, so migration 590's backfill cannot be reverted. The exposure is one level indirect and is the finding M0-T27 surfaced:

| asset | live scope | seed writes scope | live domain | domain implied by the new scope | consistent after a re-seed |
|---|---|---|---|---|---|
| `mi_jivanaghatana` | `per_chart` | `global` | `chart` | `shared` | **NO** |

`scope` is seed-owned and `domain` is not, and 590 derived `domain` *from* `scope`. A re-seed moves one half of the pair and leaves the other, and the row then answers the same question two different ways. M0's acceptance criterion 11 passes on `domain`/`rung` being present — which stays true — while the value it presents becomes wrong. That is exactly the failure shape this register exists to name.

Note the asymmetry that makes it survivable: the reverse repair is *not* available. Writing `scope='per_chart'` into the DB does not stick either — it is the seed-owned half. The durable fix is in the seed file or in a CASE guard, not in a DB write.

### 3.4 — `has_writer` (generator-only, no rows written) — **confirmed safe**

- Columns: `has_writer`
- In the seed's `DO UPDATE SET` list: none
- Not written by the seed at all: `has_writer`
- Rows a re-seed would change: **0**

**Verdict.** DURABLE (vacuously) — the column is not in the seed's INSERT or DO UPDATE list, and no rows were written by the campaign

**Consequence if reverted.** n/a — nothing to revert; no rows written.

Confirmed rather than assumed: `has_writer` is in Group D (absent from both seed column lists), and the column exists live with 128 non-NULL rows — i.e. it is populated by something other than the seed. Nothing for a re-seed to revert.

### 3.5 — `layer_index` / `layer_name` (Phase 0.5a — **NOT YET PERFORMED**)

- Columns: `layer_index`, `layer_name`
- In the seed's `DO UPDATE SET` list: `layer_index`, `layer_name`
- Not written by the seed at all: none
- Rows a re-seed would change: **41**

**Verdict.** NOT YET PERFORMED — and the measurement says the risk here runs the OPPOSITE way to the asset_kind case. Both columns are seed-owned, but on all 41 divergent cells the seed's derived value is the CLEAN one. Phase 0.5a is durable so long as it writes exactly what `layerIndices[layer]` / `layerNames[layer]` produce, diacritics included; a repair that invents its own form is reverted. 0 dirty row(s) have no seed entry and are out of the seed's reach entirely.

**Consequence if reverted.** COSMETIC. layer_index is a display/ordering label; migration 590 explicitly REFUSED to derive `rung` from it precisely because it is dirty, so no gate reads it. A reversion here is a label going wrong, not a detector switching off — categorically less serious than has_substeps or the scope/domain pair.

Held pending this question, so what follows is a projection of a repair that does not exist yet. The measurement points the opposite way to §3.2, and saying so is the point of the exercise:

- `layer_index` divergent cells: **21**. The seed's value is well-formed `^L[0-5]$` on **21** of them; the live value on **0**.
- `layer_name` divergent cells: **20**, of which 15 are the seed filling a live NULL.

Both columns are seed-owned, so a repair here *is* reachable by the seed — but on every divergent cell the seed already holds the clean value. A Phase 0.5a repair that writes exactly what `layerIndices[layer]` / `layerNames[layer]` produce is durable by agreement; one that invents its own form is reverted on the next run. The diacritics are load-bearing: the seed's map carries `Gaṇita` / `Kāla` / `Mīmāṃsā` per CLAUDE.md §N.1, and several live rows carry the unaccented spelling.

Dirty rows with no seed entry at all (durable outright, and unreachable by a re-seed): **none**.

### 3.6 — Found while modelling the other 19 columns

These are not campaign repairs; they are live seed-vs-DB divergences that only became visible once every column was modelled. They are reported, not acted on.

**(a) `is_active` — a re-seed would DEACTIVATE a currently-active asset.** `bg_sky_calendar` is live `is_active = true`, but its declared `target_table` (`bg_sky_events`) is absent from production, so the pre-flight at `:3228` forces `false` before the upsert. The `CASE` guard does not save it — the row is `CURRENT`, not `RETIRED`. This is the seed working exactly as designed; it is listed because the outcome (an active asset going inactive on a routine re-seed) is not obvious from either side alone.

**(b) `target_floor` — 27 cells move, 10 of them between two non-NULL values.** CLAUDE.md §N.4 and invariant I7 both say a floor is the MEASURED achieved count, set after a build. Those measured values live in a seed-owned column. Examples: `bg_parihara_rules` 447→439, `ga_vargas` 22092→21635, `bo_laksana` 60000→66738, `bo_pratijna` 0→110. The 14 NULL-ings are all live `0` → NULL, so no non-zero measured floor is lost today — but the exposure is structural, not incidental.

**(c) `count_sql` — 28 cells move, 25 of them a genuinely different query** (the other 3 differ only in whitespace or keyword case). Two go from a live query to NULL (`mi_seva`, `mi_abhilekha`), and at least one changes the table read: `bg_sky_calendar` counts `bg_sky_calendar` live and `bg_sky_events` per the seed. §N.4's 'cockpit truth' bullet makes a correct chart-scoped `count_sql` the thing the stats route reads. This register does not judge which side is correct — only that a re-seed moves it, and that the movement is real rather than cosmetic.

**(d) `target_table` — 3 cells move**, including `mi_adhilepa` `mimamsa_load_bearing` → `mimamsa_signal_adjustment`: a re-seed would re-point the asset at a different table, which also feeds the `is_active` pre-flight in (a).

**(e) One live row has no seed entry:** `bg_gochara_citation_resolution`. A re-seed neither updates nor deletes it — every column on it is durable, and it is invisible to the seed's own consistency checks.

## 4 — Ranked by consequence

The ranking answers: *if this reversion happened silently, what would be wrong?* A reverted flag that switches a detector off is categorically worse than a reverted description, and the register refuses to present them in one flat list (CLAUDE.md §N.6).

| rank | class | what reverts | rows at risk today | state |
|---|---|---|---:|---|
| 1 | CORRECTNESS — a detector switches off | `has_substeps` | 0 | not seed-written; measured durable |
| 2 | CORRECTNESS — a pair goes internally inconsistent | `scope→domain` | 1 | MEASURED LIVE — see per_repair.domain_rung__migration_590 |
| 3 | CONTRACT — a per-kind rule set changes under the asset | `asset_kind`, `asset_type` | 8 | MEASURED LIVE |
| 4 | OPERATIONAL — build gating / floors / counting | `is_active`, `catalog_status`, `count_sql`, `target_floor`, `depends_on`, `target_table` | 88 | MEASURED LIVE |
| 5 | COSMETIC — a label goes wrong, nothing gates on it | `sanskrit_name`, `english_name`, `english_description`, `volume_explanation`, `sort_order`, `layer_name`, `layer_index` | 149 | MEASURED LIVE |

**1. CORRECTNESS — a detector switches off** — a reverted has_substeps re-disables the §N.8 substep-plan-completeness predicate, letting `lit` be written on a proxy. Nothing announces it.

**2. CORRECTNESS — a pair goes internally inconsistent** — scope is seed-owned, domain is not, and domain was derived FROM scope. A re-seed moves one and leaves the other; the row then asserts two different answers to the same question.

**3. CONTRACT — a per-kind rule set changes under the asset** — both carry a `?? 'data'` default, so an omitted key is an active write of 'data', not a no-op. A 'service' asset silently becomes 'data' and the contract rules that apply to it change.

**4. OPERATIONAL — build gating / floors / counting** — these decide whether an asset builds at all, what its cockpit count reads and what its DAG edges are. is_active and catalog_status are the TWO columns already CASE-guarded — that guard is the pattern any fix to the rest would follow.

**5. COSMETIC — a label goes wrong, nothing gates on it** — wrong text is visible and correctable; no detector reads it.

Two qualifications on the rank-5 row, so its 149 is not read as 149 problems: it includes `layer_index`/`layer_name`, and §3.5 measures the seed as holding the CLEAN value on every one of those 41 cells — a re-seed *improves* them. And 41 of `volume_explanation`'s 47 are the seed filling a live NULL. The number counts cells that MOVE, which is the only thing a projection can honestly count; it does not claim they move for the worse.

The two entries that matter for the ownership ruling are ranks 2 and 3: they are the only ones where a live divergence sits on a seed-owned column whose value a detector or contract rule reads. Rank 1 is listed first because its *consequence* is the worst, not because it is at risk — it is measured durable. Rank 4 is the largest genuinely open question and this register does not answer it: on `count_sql`, `target_floor` and `depends_on` it can say a re-seed moves 80 cells, and it cannot say which side is right. That is a judgment about ownership, not a measurement.

## 5 — Coverage, stated explicitly

- Columns a re-seed writes: **23**. Columns modelled here: **23**. Unmodelled: **0**.
- M0-T27 modelled `asset_kind`, `asset_type`, `layer`, `scope` — 4 columns — and said so. That declaration is why its result could be trusted, and this section is the same declaration for this register.
- Cells marked UNKNOWN: **0**. A cell is UNKNOWN, never "unchanged", whenever the value the seed would write could not be determined.
- Rows compared: **127**. Live rows not compared (no seed entry): `bg_gochara_citation_resolution`.

### 5.1 — What is still NOT modelled, and why it matters

- `is_active` is modelled only as far as to_regclass() can see: the pre-flight also HARD-STOPS the whole seed if more than 20 assets have absent target_tables (:3240). If that stop fires, NO column is written at all and every figure in this register is moot. The count is reported under is_active_preflight.
- `expected_volume_inputs` for `mi_jivanaghatana` is overwritten by main() (:3205) with a live FILE_COUNT of the LEL file. That evaluation is replicated in the extractor and its result is reported (lel_file_count=56); if the LEL file changes, the seed's value changes with it and this cell must be re-measured.
- Column ORDER-sensitivity in `depends_on` is compared as an ordered list, which is what Postgres text[] stores. A pure re-ordering counts as a change here — that is deliberate, not a false positive.
- This register models the seed's INSERT/UPDATE of asset_registry ONLY. The same script also upserts asset_coefficients (:3341); that table is out of scope and unmeasured.
- On the hard stop above: **1** asset(s) currently have a declared `target_table` absent from production (`bg_sky_calendar`), against a limit of 20. The seed would proceed, not stop — but that margin is a live quantity and this figure expires the moment a target table is dropped or renamed.

### 5.2 — How the seed's values were obtained without running the seed

`extract_seed_projection.mjs` slices out the `export const ASSETS: AssetDef[] = [ … ]` array **literal**, statically proves that slice inert, and evaluates only that. The proof is machine-checked on every run and the script refuses to evaluate if any check fails:

| check | result |
|---|---|
| `no_template_substitution` | True |
| `no_call_expression` | True |
| `no_free_identifiers` | True |

No module import of the seed occurs, no DB client is constructed in that process, and the seed's `main()` — the thing that actually issues `INSERT … ON CONFLICT DO UPDATE` — is never reached. `main()`'s value derivations (`?? 'data'`, the layer maps, the catalog_status default, the LEL `FILE_COUNT`, the `to_regclass` pre-flight) are **re-implemented** in the extractor and the generator against the cited line numbers, not called.

## 6 — Re-running this register

```
python3 00_ARCHITECTURE/control/seed_durability/seed_durability_register.py
```

Rewrites both `SEED_DURABILITY_REGISTER_v1_0.json` and this file. Read-only against the database (`SET default_transaction_read_only = on`; only SELECT / SET / `to_regclass` are issued) and read-only against the seed. Re-run it after **any** change to `asset_registry_seed.ts` or to `asset_registry` rather than trusting these numbers — that is the whole reason it is a generator and not a table someone typed.

Files:

| file | role |
|---|---|
| `00_ARCHITECTURE/control/seed_durability/extract_seed_projection.mjs` | slices + inertness-proves + evaluates the `ASSETS` literal; re-implements `main()`'s derivations |
| `00_ARCHITECTURE/control/seed_durability/seed_durability_register.py` | parses the upsert, projects every column against live, writes the JSON |
| `00_ARCHITECTURE/control/seed_durability/render_register_md.py` | renders this document from the JSON |

Nothing here imports or edits `m0_exit_scorecard.py`, `writer_substep_census.py` or `build_asset_control_workbook.py`. The upsert-parse is this register's own copy of M0-T27's technique, extended from 4 columns to 23; a sibling KĀRAKA holds two of those files mid-flight.

---

*Authored by KĀRAKA on task M0-T29. This document reports measurements; it does not certify them, and its author may not (I16 / charter H7). Every figure in it is produced by the generator above and none is typed in by hand.*
