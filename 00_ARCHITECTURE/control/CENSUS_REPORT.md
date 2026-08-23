# NIRMĀṆA M0-T1 — Six-Source Asset Census

**Generated:** 2026-08-23T09:55:22Z  
**Generator:** `00_ARCHITECTURE/control/census.py`  
**Git:** `campaign/nirmana-autonomous` @ `a9278d1ec4723f074f4610407ff19b87a129de37`  
**Database access:** READ-ONLY (SELECT only; SET statement_timeout='45s'; autocommit)  
**Status:** observations only. This document issues no verdict and certifies nothing (I16 / charter H7).

## 0 — Sources

| id | source | population |
|---|---|---|
| S1 | asset_registry (live DB) | 128 assets |
| S2 | `@register('<id>')` decorators | 129 ids (123 with a production site) |
| S3 | `platform/scripts/seed/asset_registry_seed.ts` | 127 assets |
| S4 | migrations touching `asset_registry` | 68 ids across 66 files |
| S5 | asset_throughput (live DB) | 126 distinct assets, 267 rows |
| S6 | `CAPABILITY_MANIFEST.json` | 128 entries, 0 of them asset-shaped |

**Union of all sources: 138 distinct ids.**

### Notes

- platform/migrations holds more than one .sql file at the same migration number: 294 -> 294_catalog_status_current.sql, 294_ga_vastu_target_floor.sql. Reported as an observation about the migration series; ordering/ledger consequences are not evaluated here.

### Heuristics and their honest limits

- S4 presence counts ONLY strong evidence — the token is used as an asset_id (`asset_id = 'x'`, `asset_id IN (...)`, `SET asset_id = 'x'`, or the first VALUES literal of an INSERT INTO asset_registry). Asset-shaped tokens found anywhere else in such a file are reported separately as weak matches and are NOT counted as presence: they are usually table names inside count_sql or prose in a comment. S4 can still under-match an id built by concatenation or hidden inside a dollar-quoted body.
- S2 production-vs-test split is by path: /tests/, /__tests__/, test_*.py and *_test.py are counted as test sites, everything else as production.
- Only platform/migrations/*.sql present in the working tree are scanned. That tree holds 140 numbered files at 139 distinct numbers spanning 1..590, with 451 numbers in that range absent from it. S4 is therefore structurally incomplete by a large margin and an asset's absence from S4 is weak evidence of anything.

### S6 scope — read this before reading the S6 column

`CAPABILITY_MANIFEST.json` (128 entries, declared `entry_count`=128, generated 2026-08-21T05:30:00Z) is a catalogue of **canonical governance artefacts keyed by `canonical_id`** — document paths, versions and statuses. It is not keyed by `asset_id`. The number of manifest entries whose id even has the shape of an asset_id is **0**.

Consequence: the S6 column below is `·` for every asset, and that is a true measurement of the manifest's scope, not a defect in the assets. Treating S6 as an asset source would require the manifest to gain asset entries first — a decision outside this task.

## 1 — Presence matrix

`Y` = present · `·` = absent · `?` = source UNKNOWN (unparseable)

| asset_id | S1 reg | S2 dec | S3 seed | S4 migr | S5 thru | S6 man | n | layer | catalog_status | is_active | target_table |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|---|:--:|---|
| `bad_infra_writer` | · | t | · | · | · | · | 1 | — | — | — | — |
| `bg_class_lifetime_counts` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_class_priors` |
| `bg_class_priors` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_class_priors` |
| `bg_cohort` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_synthetic_cohort` |
| `bg_compendium_index` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `brahma_compendium_index` |
| `bg_concordance` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `classical_attributions` |
| `bg_dasha_systems` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `brahma_dasha_systems` |
| `bg_dignity_reference` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_dignity_reference` |
| `bg_doshas` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_dosha_catalog` |
| `bg_ephemeris` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `ephemeris_daily` |
| `bg_ephemeris_engine` | Y | · | Y | · | Y | · | 3 | L0 | CURRENT | Y | — |
| `bg_formula_constants` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_formula_constants` |
| `bg_ghatana` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_event_ontology` |
| `bg_gochara_arcs` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_gochara_arcs` |
| `bg_gochara_citation_resolution` | Y | · | · | · | · | · | 1 | L0 | CURRENT | Y | `bg_gochara_citation_resolution` |
| `bg_kota_chakra_rings` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_kota_chakra_rings` |
| `bg_kp_sublord_division` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_kp_sublord_division` |
| `bg_medical_mappings` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_medical_mappings` |
| `bg_muhurta_lattice` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_muhurta_lattice` |
| `bg_nakshatra` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `reference_nakshatra` |
| `bg_nakshatra_medical` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_nakshatra_medical` |
| `bg_ontology` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `brahma_ontology` |
| `bg_panchanga` | Y | · | Y | · | Y | · | 3 | L0 | CURRENT | Y | — |
| `bg_parihara_rules` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_parihara_rules` |
| `bg_phaladeepika_latta` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_phaladeepika_latta` |
| `bg_prashna_rules` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | — |
| `bg_reference` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `reference_nakshatras` |
| `bg_remedies` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_remedy_corpus` |
| `bg_rules` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `sutravali_rules` |
| `bg_sarvatobhadra_grid` | Y | · | Y | · | Y | · | 3 | L0 | CURRENT | Y | `bg_sarvatobhadra_grid` |
| `bg_sign_medical` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_sign_medical` |
| `bg_sky_calendar` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_sky_events` |
| `bg_text_index` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `classical_text_chunks` |
| `bg_texts` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `classical_text_chunks` |
| `bg_transit_engine` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_transit_engine` |
| `bg_transit_rules` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_transit_rules` |
| `bg_vastu_directions` | Y | Y | Y | Y | Y | · | 5 | L0 | CURRENT | Y | `bg_vastu_directions` |
| `bg_vedha_malefic_scale` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `bg_vedha_malefic_scale` |
| `bg_vidhi_floors` | Y | Y | Y | Y | Y | · | 5 | L0 | DRAFT | Y | `vidhi_floor_items` |
| `bg_vidhi_primitives` | Y | Y | Y | Y | Y | · | 5 | L0 | DRAFT | Y | `vidhi_primitives` |
| `bg_yogas` | Y | Y | Y | · | Y | · | 4 | L0 | CURRENT | Y | `brahma_yoga_catalog` |
| `bo_anveshana` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_discoveries` |
| `bo_arudha` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_bimba` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_cgm_nodes` |
| `bo_cdlm_summary` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | — |
| `bo_cgm_motifs` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_cgm_motifs` |
| `bo_cgm_paths` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_cgm_paths` |
| `bo_chart_gestalt` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | — |
| `bo_drishti` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_question_lenses` |
| `bo_karanajala` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_cgm_edges` |
| `bo_laksana` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_msr_signals` |
| `bo_laksana_rerank` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_nakshatra_semantic` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_pramana_mapa` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `synthesis_quality_scorecard` |
| `bo_pratijna` | Y | Y | Y | · | Y | · | 4 | L2 | CURRENT | Y | `bodha_pratijna` |
| `bo_samskara` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_signal_embeddings` |
| `bo_samvada` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `vw_chart_digest` |
| `bo_sangati` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_cdlm_cells` |
| `bo_special_lagna` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_sudarshana` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_upaya` | Y | Y | Y | Y | Y | · | 5 | L2 | CURRENT | Y | `bodha_rm_resonances` |
| `bo_vargottama_dhana` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_msr_signals` |
| `bo_yantra_mechanism` | Y | Y | Y | Y | Y | · | 5 | L2 | DRAFT | Y | `bodha_mechanisms` |
| `fixture.asset_a` | · | t | · | · | · | · | 1 | — | — | — | — |
| `fixture.crashing` | · | t | · | · | · | · | 1 | — | — | — | — |
| `fixture.success` | · | t | · | · | · | · | 1 | — | — | — | — |
| `ga_ayurdaya` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `chart_facts` |
| `ga_condition` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_condition_composite` |
| `ga_dashas` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `chart_dashas` |
| `ga_medical` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_medical` |
| `ga_nakshatra` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `chart_facts` |
| `ga_panchanga` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `chart_facts` |
| `ga_positions` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `chart_facts` |
| `ga_prashna` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_prashna_judgment` |
| `ga_pyjhora_engine` | · | · | · | Y | · | · | 1 | — | — | — | — |
| `ga_sade_sati` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | — |
| `ga_sensitive` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | — |
| `ga_sensitive_degree` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `chart_facts` |
| `ga_strength` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | — |
| `ga_structural` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | — |
| `ga_tajaka` | Y | Y | Y | · | Y | · | 4 | L1 | CURRENT | Y | `l1_tajik_varsha_year_lords` |
| `ga_transit_anchors` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_transit_anchors` |
| `ga_vargas` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `chart_divisionals` |
| `ga_vastu` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_vastu_planet_direction_map` |
| `ga_vastu_planet_direction_map` | · | · | · | Y | · | · | 1 | — | — | — | — |
| `ga_vichara` | Y | Y | Y | Y | Y | · | 5 | L1 | DRAFT | Y | `chart_vichara` |
| `ga_yoga` | Y | Y | Y | Y | Y | · | 5 | L1 | CURRENT | Y | `ga_yoga_firings` |
| `ka_avadhi` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_avadhi` |
| `ka_bhavishya_lekha` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_bhavishya` |
| `ka_dasha_kala` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | — |
| `ka_gochara` | Y | Y | Y | Y | Y | · | 5 | L3 | CURRENT | Y | `kala_gochara_windows` |
| `ka_gochara_resonance` | Y | Y | Y | Y | Y | · | 5 | L3 | CURRENT | Y | `gochara_resonance_map` |
| `ka_gochara_sweep` | Y | Y | Y | Y | Y | · | 5 | L3 | RETIRED | · | `kala_gochara_windows` |
| `ka_gochara_v2_materialize` | · | · | · | Y | · | · | 1 | — | — | — | — |
| `ka_gochara_v3_century_materialize` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_gochara_windows_v2` |
| `ka_graha_sancara` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | — |
| `ka_jivana_parva` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_jivana_parva` |
| `ka_kala_darshana` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_darshana` |
| `ka_kalasutra` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_activation` |
| `ka_kota_chakra` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_kota_chakra` |
| `ka_kshetra` | Y | Y | Y | Y | Y | · | 5 | L3 | CURRENT | Y | `kala_field` |
| `ka_moorti_nirnaya` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_moorti_nirnaya` |
| `ka_muhurta_seva` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | — |
| `ka_sangam` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_convergence` |
| `ka_sudarshana_varsha` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_sudarshana_varsha` |
| `ka_taranga` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_taranga` |
| `ka_tithi_pravesha` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_tithi_pravesha` |
| `ka_transit_almanac` | · | · | · | Y | · | · | 1 | — | — | — | — |
| `ka_tulana` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | — |
| `ka_vedha_gochara` | Y | Y | Y | · | Y | · | 4 | L3 | CURRENT | Y | `kala_vedha_gochara` |
| `ka_vighnakara` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_obstruction` |
| `ka_yojaka` | Y | Y | Y | · | Y | · | 4 | L3 | DRAFT | Y | `kala_activation_predicates` |
| `lel_events` | Y | · | Y | · | · | · | 2 | mimamsa | DRAFT | Y | — |
| `mi_abhilekha` | Y | Y | Y | · | Y | · | 4 | L5 | DRAFT | Y | `mimamsa_journal` |
| `mi_adhilepa` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_load_bearing` |
| `mi_bhara` | Y | Y | Y | · | Y | · | 4 | L5 | DRAFT | Y | `kala_field_weight_versions` |
| `mi_bhavisya` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_predictions` |
| `mi_darshana` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_insight_units` |
| `mi_gunanaka` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_multipliers` |
| `mi_jivanaghatana` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_event_provenance` |
| `mi_kula` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_signal_families` |
| `mi_pariksha` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_qa_eval` |
| `mi_pramana` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_calibration` |
| `mi_sambandha` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_manifestation_grammar` |
| `mi_sankalpa` | Y | Y | Y | · | Y | · | 4 | L5 | DRAFT | Y | `mimamsa_intervention_ledger` |
| `mi_seva` | Y | Y | Y | · | Y | · | 4 | L5 | DRAFT | Y | `mimamsa_preferences` |
| `mi_vistara` | Y | Y | Y | Y | Y | · | 5 | L5 | DRAFT | Y | `mimamsa_export_log` |
| `ph_muhurta` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_muhurta` |
| `ph_nimitta` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_anchors` |
| `ph_phaladesa` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_phaladesa` |
| `ph_pramana` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_pramana` |
| `ph_pratikara` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_mitigation` |
| `ph_rectification` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_rectification` |
| `ph_sankrama` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_sankrama` |
| `ph_sodhana` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_sodhana` |
| `ph_suddha_sodhana` | Y | Y | Y | · | Y | · | 4 | L4 | DRAFT | Y | `phala_suddha_sodhana` |
| `test_infra_asset_1` | · | t | · | · | · | · | 1 | — | — | — | — |
| `test_infra_asset_dup` | · | t | · | · | · | · | 1 | — | — | — | — |

`t` in the S2 column = the id is registered only from a test fixture, never from production code.

## 2 — Three-way diff: registry vs decorators vs seed

*Orphans live in the gaps.*

- registry: **128**
- production decorators: **123** (+6 test-fixture-only ids)
- seed: **127**
- present in all three: **123**

### In registry ONLY — no writer, not in seed

**1:**

- `bg_gochara_citation_resolution` — CURRENT, is_active=True, kind=data, target_table=bg_gochara_citation_resolution

### Decorator ONLY — code registers it, catalogue has never heard of it

_none_

### Seed ONLY — seeded in the .ts, absent from live registry and from code

_none_

### Registry + writer, but NOT in the seed file

_none_

### Registry + seed, but NO production writer

**4:**

- `bg_ephemeris_engine` — CURRENT, is_active=True, kind=service, target_table=None
- `bg_panchanga` — CURRENT, is_active=True, kind=service, target_table=None
- `bg_sarvatobhadra_grid` — CURRENT, is_active=True, kind=data, target_table=bg_sarvatobhadra_grid
- `lel_events` — DRAFT, is_active=True, kind=data, target_table=None

### Writer + seed, but NOT in the live registry

_none_

### Decorator ids that exist only in test fixtures

- `bad_infra_writer`
- `fixture.asset_a`
- `fixture.crashing`
- `fixture.success`
- `test_infra_asset_1`
- `test_infra_asset_dup`

### Decorator ids that do not match the asset-id shape `^(bg|ga|bo|ka|ph|mi)_[a-z0-9_]+$`

- `bad_infra_writer` — platform/python-sidecar/pipeline/orchestrator/writers/tests/test_registry.py:32
- `fixture.asset_a` — platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_writer_registry.py:29
- `fixture.crashing` — platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_writer_registry.py:86
- `fixture.success` — platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_writer_registry.py:51
- `test_infra_asset_1` — platform/python-sidecar/pipeline/orchestrator/writers/tests/test_registry.py:8
- `test_infra_asset_dup` — platform/python-sidecar/pipeline/orchestrator/writers/tests/test_registry.py:17

### Known ONLY to a migration (S4) — no registry row, no writer, no seed entry, no throughput — 4

| asset_id | ops | migration files |
|---|---|---|
| `ga_pyjhora_engine` | DELETE | `platform/migrations/342_retire_ga_pyjhora_engine.sql` |
| `ga_vastu_planet_direction_map` | UPDATE | `platform/migrations/294_ga_vastu_target_floor.sql` |
| `ka_gochara_v2_materialize` | DELETE, INSERT, UPDATE | `platform/migrations/563_utkarsha_w64_asset_rename.sql` |
| `ka_transit_almanac` | DELETE | `platform/migrations/329_ka_transit_almanac_hard_remove.sql` |

### S4 weak matches — asset-shaped tokens in an asset_registry migration that are NOT used as an asset_id — 5

These are NOT counted as S4 presence. They are listed so the over-match is visible rather than silently absorbed; most are table names inside a `count_sql` body or identifiers mentioned in prose.

| token | in registry | migration files |
|---|:--:|---|
| `bg_vastu_direction_remedials` | · | `platform/migrations/285_asset_registry_bg_vastu.sql` |
| `ga_condition_composite` | · | `platform/migrations/252_asset_registry_ga_condition.sql`, `platform/migrations/280_ga_medical_registry.sql` |
| `ga_dashas` | Y | `platform/migrations/240_ga_yoga.sql`, `platform/migrations/252_asset_registry_ga_condition.sql`, `platform/migrations/435_ga_vichara.sql` |
| `ga_positions` | Y | `platform/migrations/252_asset_registry_ga_condition.sql`, `platform/migrations/268_ga_transit_anchors_registry.sql`, `platform/migrations/280_ga_medical_registry.sql`, `platform/migrations/291_ga_prashna_asset_registry.sql`, `platform/migrations/292_ga_nakshatra_registry.sql`, `platform/migrations/438_bo_sudarshana_asset_registry.sql`, `platform/migrations/450_bo_nakshatra_semantic_asset_registry.sql`, `platform/migrations/451_bo_arudha_asset_registry.sql`, `platform/migrations/453_bo_vargottama_dhana_asset_registry.sql` |
| `ga_yoga_firings` | · | `platform/migrations/240_ga_yoga.sql` |

## 3 — Registered but dead

A registry row with **no production `@register` writer** and **no `asset_throughput` row at all**.

Caveat stated plainly: `asset_throughput` is live build state, not an append-only history. "No throughput row now" is evidence the asset has not built recently; it is not proof it never built. This census cannot distinguish the two.

**2 assets:**

| asset_id | catalog_status | is_active | has_writer flag | kind | storage | target_table | in seed | in migrations |
|---|---|:--:|:--:|---|---|---|:--:|:--:|
| `bg_gochara_citation_resolution` | CURRENT | Y | · | data | postgres_table | `bg_gochara_citation_resolution` | · | · |
| `lel_events` | DRAFT | Y | · | data | postgres_table | — | Y | · |

### `has_writer` flag vs. an actual decorator (the registry's own claim, checked)

- `has_writer=true` but no production decorator: **0** _none_
- decorator exists but `has_writer` is not true: **2** `bg_nakshatra_medical`, `bg_transit_engine`
- `has_writer` NULL: **0** _none_

## 4 — `asset_throughput` rows on inactive / retired / unregistered assets

### Throughput rows for an asset_id with NO registry row — 0

_none_

### Throughput rows on `is_active = false` assets — 1

| asset_id | rows | states | last_built_at | rows_written total |
|---|--:|---|---|--:|
| `ka_gochara_sweep` | 3 | error | 2026-08-12T16:30:19.625456+00:00 | 4389 |

### Throughput rows on `catalog_status = RETIRED` assets — 1

| asset_id | rows | states | last_built_at | rows_written total |
|---|--:|---|---|--:|
| `ka_gochara_sweep` | 3 | error | 2026-08-12T16:30:19.625456+00:00 | 4389 |

### Throughput rows on `catalog_status = DRAFT` assets — 46

| asset_id | rows | states | last_built_at | rows_written total |
|---|--:|---|---|--:|
| `bg_vidhi_floors` | 1 | lit | 2026-08-02T13:50:03.732998+00:00 | 77 |
| `bg_vidhi_primitives` | 1 | lit | 2026-08-02T13:50:02.693503+00:00 | 37 |
| `bo_arudha` | 3 | lit | 2026-08-12T16:27:33.489037+00:00 | 69 |
| `bo_cdlm_summary` | 3 | lit, stale | 2026-08-12T16:27:32.675234+00:00 | 150 |
| `bo_chart_gestalt` | 3 | lit, stale | 2026-08-12T23:44:26.973022+00:00 | 15 |
| `bo_laksana_rerank` | 3 | lit, stale | 2026-08-12T16:47:24.459323+00:00 | 32652 |
| `bo_nakshatra_semantic` | 3 | lit | 2026-08-12T16:27:46.833919+00:00 | 135 |
| `bo_special_lagna` | 3 | lit | 2026-08-12T15:24:34.915920+00:00 | 60 |
| `bo_sudarshana` | 3 | lit | 2026-08-08T00:21:37.357375+00:00 | 135 |
| `bo_vargottama_dhana` | 3 | lit | 2026-08-08T00:22:51.583173+00:00 | 45 |
| `bo_yantra_mechanism` | 3 | lit, stale | 2026-08-12T16:30:55.841002+00:00 | 1938 |
| `ga_vichara` | 3 | lit | 2026-08-10T01:30:11.496209+00:00 | 24736 |
| `ka_bhavishya_lekha` | 3 | error, lit | 2026-08-13T01:15:54.314753+00:00 | 200 |
| `ka_dasha_kala` | 3 | lit | 2026-08-08T00:28:57.200368+00:00 | 0 |
| `ka_graha_sancara` | 1 | lit | 2026-08-02T13:50:52.041520+00:00 | 0 |
| `ka_jivana_parva` | 3 | lit, stale | 2026-08-13T01:15:55.070135+00:00 | 309 |
| `ka_kala_darshana` | 3 | lit, stale | 2026-08-13T01:15:53.303027+00:00 | 2250 |
| `ka_kalasutra` | 3 | lit, stale | 2026-08-13T01:15:50.567754+00:00 | 1006943 |
| `ka_muhurta_seva` | 1 | lit | 2026-08-02T13:50:52.126596+00:00 | 0 |
| `ka_sangam` | 3 | lit, stale | 2026-08-13T01:07:13.494312+00:00 | 65670 |
| `ka_tulana` | 3 | lit, stale | 2026-08-13T01:15:55.289687+00:00 | 0 |
| `ka_vighnakara` | 3 | lit, stale | 2026-08-13T01:08:12.911241+00:00 | 1900 |
| `ka_yojaka` | 3 | error, lit | 2026-08-12T16:31:26.111601+00:00 | 150150 |
| `mi_abhilekha` | 2 | lit, stale | 2026-08-13T01:16:30.108068+00:00 | 0 |
| `mi_adhilepa` | 3 | error, lit | 2026-08-21T02:36:53.708535+00:00 | 224751 |
| `mi_bhara` | 2 | error | 2026-08-21T02:28:16.524173+00:00 | 0 |
| `mi_bhavisya` | 2 | error, lit | 2026-08-21T02:36:53.672507+00:00 | 390 |
| `mi_darshana` | 3 | error, lit | 2026-08-21T02:36:53.753400+00:00 | 150 |
| `mi_gunanaka` | 2 | error, lit | 2026-08-21T02:36:53.690124+00:00 | 18 |
| `mi_jivanaghatana` | 2 | lit | 2026-08-08T00:18:13.998786+00:00 | 64 |
| `mi_kula` | 1 | lit | 2026-08-02T13:50:52.227555+00:00 | 15 |
| `mi_pariksha` | 3 | error, lit | 2026-08-21T02:36:53.655163+00:00 | 1670 |
| `mi_pramana` | 2 | error, lit | 2026-08-21T02:36:53.627032+00:00 | 63 |
| `mi_sambandha` | 2 | error, lit | 2026-08-21T02:36:53.726749+00:00 | 47 |
| `mi_sankalpa` | 1 | dormant | 2026-08-13T01:02:38.387443+00:00 | 0 |
| `mi_seva` | 2 | lit, stale | 2026-08-13T01:17:19.317030+00:00 | 0 |
| `mi_vistara` | 1 | lit | 2026-08-02T13:50:52.267777+00:00 | 0 |
| `ph_muhurta` | 2 | lit | 2026-08-13T01:16:03.105166+00:00 | 195 |
| `ph_nimitta` | 3 | error, lit | 2026-08-13T01:16:00.435155+00:00 | 195 |
| `ph_phaladesa` | 3 | error, lit, stale | 2026-08-13T01:16:27.343582+00:00 | 26 |
| `ph_pramana` | 2 | lit, stale | 2026-08-13T01:16:22.481143+00:00 | 195 |
| `ph_pratikara` | 2 | lit, stale | 2026-08-13T01:16:05.883214+00:00 | 1277 |
| `ph_rectification` | 2 | lit | 2026-08-13T01:16:06.163083+00:00 | 372 |
| `ph_sankrama` | 2 | lit | 2026-08-13T01:16:21.621682+00:00 | 2985 |
| `ph_sodhana` | 2 | lit | 2026-08-13T01:16:07.622477+00:00 | 138 |
| `ph_suddha_sodhana` | 2 | lit | 2026-08-13T01:16:09.082588+00:00 | 195 |

## 5 — `target_table` collisions (co-writer / multi-producer)

These are the tables where the `(table × generation × natural-key partition)` invariant has to be checked, because more than one registered asset declares the same `target_table`. This census reports the collision; it does not evaluate the invariant.

**5 tables claimed by more than one asset:**

| target_table | n | asset_ids | layers | with writer | active | catalog_statuses |
|---|--:|---|---|---|---|---|
| `bodha_msr_signals` | 7 | `bo_arudha`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` | L2 | `bo_arudha`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` | `bo_arudha`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` | CURRENT, DRAFT |
| `brahma_class_priors` | 2 | `bg_class_lifetime_counts`, `bg_class_priors` | L0 | `bg_class_lifetime_counts`, `bg_class_priors` | `bg_class_lifetime_counts`, `bg_class_priors` | CURRENT |
| `chart_facts` | 5 | `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive_degree` | L1 | `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive_degree` | `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive_degree` | CURRENT |
| `classical_text_chunks` | 2 | `bg_text_index`, `bg_texts` | L0 | `bg_text_index`, `bg_texts` | `bg_text_index`, `bg_texts` | CURRENT |
| `kala_gochara_windows` | 2 | `ka_gochara`, `ka_gochara_sweep` | L3 | `ka_gochara`, `ka_gochara_sweep` | `ka_gochara` | CURRENT, RETIRED |

### Writer modules that register more than one asset_id — 4

- `platform/python-sidecar/pipeline/orchestrator/writers/bg_medical_mappings.py` → `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_sign_medical`
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_phaladeepika_vedha.py` → `bg_phaladeepika_latta`, `bg_vedha_malefic_scale`
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py` → `bg_transit_engine`, `bg_transit_rules`
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py` → `bo_laksana`, `bo_laksana_rerank`

### Registry rows with no `target_table` — 14

`bg_ephemeris_engine`, `bg_panchanga`, `bg_prashna_rules`, `bo_cdlm_summary`, `bo_chart_gestalt`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`, `lel_events`

## 6 — Prefix conformance

`bg_`→L0 · `ga_`→L1 · `bo_`→L2 · `ka_`→L3 · `ph_`→L4 · `mi_`→L5 (CLAUDE.md §N.1).

- checked: **128** · fully conforming: **127**
- prefix distribution: `bg_` 40, `bo_` 22, `ga_` 19, `ka_` 23, `lel_` 1, `mi_` 14, `ph_` 9

Four non-conformance classes, kept apart on purpose — a wrong layer and a missing `layer_index` are different defects and must not be totalled together.

### unrecognised_prefix — 1

_asset_id prefix is not one of bg_/ga_/bo_/ka_/ph_/mi__

| asset_id | layer | layer_index | prefix |
|---|---|---|---|
| `lel_events` | mimamsa | NULL | lel |

### layer_contradiction — 0

_prefix says one layer, registry.layer or layer_index says a different one — the prefix is genuinely wrong or the layer column is_

_none_

### layer_index_format — 0

_layer names the right layer but layer_index is the bare digit ('1') where the convention is 'L1' — a format inconsistency, not a wrong layer_

_none_

### layer_index_null — 0

_layer_index is NULL, so the layer cannot be cross-checked from that column at all_

_none_

## 7 — `catalog_status` distribution, and which DRAFT assets are served

| catalog_status | count |
|---|--:|
| CURRENT | 80 |
| DRAFT | 47 |
| RETIRED | 1 |

### By layer

| layer | CURRENT | DRAFT | RETIRED | total |
|---|--:|--:|--:|--:|
| ? | 0 | 1 | 0 | 1 |
| L0 | 38 | 2 | 0 | 40 |
| L1 | 18 | 1 | 0 | 19 |
| L2 | 13 | 9 | 0 | 22 |
| L3 | 11 | 11 | 1 | 23 |
| L4 | 0 | 9 | 0 | 9 |
| L5 | 0 | 14 | 0 | 14 |

### DRAFT assets carrying a serving signal

A DRAFT asset is listed here if ANY of these observable signals is present: is_active=true, provides_apis non-empty, health_probe non-empty, at least one asset_throughput row, or a non-null last_invoked_at. This is an enumeration of observed signals, not a judgement that the asset is reachable by a caller.

**47 of 47 DRAFT assets carry at least one serving signal.**

Signal breakdown (an asset can carry more than one):

- `asset_throughput`: 46
- `is_active`: 47

| asset_id | layer | kind | signals |
|---|---|---|---|
| `bg_vidhi_floors` | L0 | data | is_active=true; asset_throughput rows=1 |
| `bg_vidhi_primitives` | L0 | data | is_active=true; asset_throughput rows=1 |
| `bo_arudha` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_cdlm_summary` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_chart_gestalt` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_laksana_rerank` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_nakshatra_semantic` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_special_lagna` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_sudarshana` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_vargottama_dhana` | L2 | data | is_active=true; asset_throughput rows=3 |
| `bo_yantra_mechanism` | L2 | data | is_active=true; asset_throughput rows=3 |
| `ga_vichara` | L1 | data | is_active=true; asset_throughput rows=3 |
| `ka_bhavishya_lekha` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_dasha_kala` | L3 | service | is_active=true; asset_throughput rows=3 |
| `ka_graha_sancara` | L3 | service | is_active=true; asset_throughput rows=1 |
| `ka_jivana_parva` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_kala_darshana` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_kalasutra` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_muhurta_seva` | L3 | service | is_active=true; asset_throughput rows=1 |
| `ka_sangam` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_tulana` | L3 | service | is_active=true; asset_throughput rows=3 |
| `ka_vighnakara` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `ka_yojaka` | L3 | artifact | is_active=true; asset_throughput rows=3 |
| `lel_events` | — | data | is_active=true |
| `mi_abhilekha` | L5 | service | is_active=true; asset_throughput rows=2 |
| `mi_adhilepa` | L5 | data | is_active=true; asset_throughput rows=3 |
| `mi_bhara` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_bhavisya` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_darshana` | L5 | data | is_active=true; asset_throughput rows=3 |
| `mi_gunanaka` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_jivanaghatana` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_kula` | L5 | data | is_active=true; asset_throughput rows=1 |
| `mi_pariksha` | L5 | data | is_active=true; asset_throughput rows=3 |
| `mi_pramana` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_sambandha` | L5 | data | is_active=true; asset_throughput rows=2 |
| `mi_sankalpa` | L5 | data | is_active=true; asset_throughput rows=1 |
| `mi_seva` | L5 | service | is_active=true; asset_throughput rows=2 |
| `mi_vistara` | L5 | data | is_active=true; asset_throughput rows=1 |
| `ph_muhurta` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_nimitta` | L4 | artifact | is_active=true; asset_throughput rows=3 |
| `ph_phaladesa` | L4 | artifact | is_active=true; asset_throughput rows=3 |
| `ph_pramana` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_pratikara` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_rectification` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_sankrama` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_sodhana` | L4 | artifact | is_active=true; asset_throughput rows=2 |
| `ph_suddha_sodhana` | L4 | artifact | is_active=true; asset_throughput rows=2 |

## 8 — What this census does NOT establish

- It does not verify that any asset's rows are correct, complete, or current.
- It does not check the `(table × generation × natural-key partition)` invariant — it only names the tables where that invariant is load-bearing (§5).
- It cannot see migrations that are not files in the working tree, nor asset ids a migration builds by string concatenation (§0 heuristics).
- It cannot distinguish "never built" from "built once and the throughput row was later removed" (§3).
- It certifies nothing. Verification of this artefact belongs to PARĪKṢAKA (I16).

