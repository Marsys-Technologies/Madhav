---
artifact: CONCEPT_COVERAGE_CENSUS_v1_0.md
canonical_id: CONCEPT_COVERAGE_CENSUS
version: 1.0
status: GENERATED — v1
generator: platform/scripts/census/generate_concept_reachability.ts
generated_at: 2026-07-19T21:18:10.803Z
---

# Concept Coverage Census v1.0 (W-21 — concept granularity, not table)

Per RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-21: "Census granularity = CONCEPT not table: enumerate chart_facts fact_categories... as first-class census rows — table-level coverage under-counts L1 by design." This census enumerates all **218** live `chart_facts.fact_category` values (the live-DB-verified set from L1b's E3 extractor, cross-referenced against E1's declared registry extraction for a serving capability path) — not the smaller hand-maintained lists.

**Headline finding, verified by direct source read (corrects L1b's stated impact claim):** `chart_facts_query`'s category filter (`register_d7_channel.ts`) does `fact_category = ANY($n::text[])` straight from the caller's string — **no enum validates it, from any of the four static category lists in the repo.** So all 218 live categories are technically SERVED (queryable) today, not just the 152 L1b's ledger loader counted as SERVED (which used coverage_matrix.ts membership as its SERVED/DARK signal). The real gap is **discoverability at the serving layer**: `chart_facts_query`'s own handler never consults `coverage_matrix.ts`'s 158-entry `CHART_FACTS_CATEGORIES` constant, so an LLM caller has no single documented, load-bearing list of the real category strings to draw from at query time. That constant is **not fully dead**, though — a real repo-wide import-site scan (this generator's own `scanImportSites()`, not a hand-typed claim) finds **1** import site(s): `platform/tests/retrieval/coverage_gate.test.ts:15`. It is imported by `platform/tests/retrieval/coverage_gate.test.ts` and used as a live CI coverage gate — one real consumer, just a test-time gate rather than a runtime-serving one.

- Live categories: **218**
- Documented in coverage_matrix.ts's list (158 entries, but unused by the query path): **152**
- SERVED-UNDOCUMENTED (queryable but absent from every static list): **66**
- Planner-known (referenced by name in a vidhi primitive/floor's fallback_face or definition): **0**

## Per-category coverage

| fact_category | live rows | served? | documented in coverage_matrix.ts? | planner-known? |
|---|---|---|---|---|
| `anumukha_shani_period` | 200 | yes | yes | no |
| `aprakasha_position` | 350 | yes | yes | no |
| `ardha_ashtama_shani_period` | 705 | yes | yes | no |
| `argala_natal_matrix` | 41760 | yes | yes | no |
| `arudha_pada` | 570 | yes | yes | no |
| `ashtakavarga_bindu` | 960 | yes | yes | no |
| `ashtakavarga_bindu_per_varga` | 13440 | yes | no | no |
| `ashtakavarga_bindu_sign` | 960 | yes | no | no |
| `ashtakavarga_ekadhipathya_shodhana` | 840 | yes | no | no |
| `ashtakavarga_kakshya_boundary` | 240 | yes | no | no |
| `ashtakavarga_pinda_bhinna` | 80 | yes | yes | no |
| `ashtakavarga_pinda_raasi` | 80 | yes | no | no |
| `ashtakavarga_pinda_sarva` | 80 | yes | yes | no |
| `ashtakavarga_pinda_sarva_per_varga` | 1120 | yes | no | no |
| `ashtakavarga_pinda_sodhita` | 80 | yes | yes | no |
| `ashtakavarga_trikona_shodhana` | 840 | yes | no | no |
| `ashtama_shani_period` | 480 | yes | yes | no |
| `aspect_jaimini` | 1080 | yes | yes | no |
| `aspect_jaimini_per_varga` | 31320 | yes | yes | no |
| `aspect_matrix_summary` | 120 | yes | yes | no |
| `aspect_parashari_given` | 190 | yes | yes | no |
| `aspect_parashari_per_varga` | 5510 | yes | yes | no |
| `aspect_parashari_received` | 190 | yes | yes | no |
| `aspect_received_by_special_point` | 899 | yes | no | no |
| `aspect_tajik` | 31 | yes | yes | no |
| `ayurdaya` | 260 | yes | no | no |
| `bhadra_flag` | 12 | yes | yes | no |
| `bhava_arudha` | 420 | yes | no | no |
| `bhava_bala_aspectual` | 120 | yes | yes | no |
| `bhava_bala_directional` | 120 | yes | yes | no |
| `bhava_bala_lord` | 120 | yes | yes | no |
| `bhava_bala_occupant` | 120 | yes | yes | no |
| `bhava_bala_positional` | 120 | yes | yes | no |
| `bhava_bala_temporal` | 120 | yes | yes | no |
| `bhava_bala_total_extended` | 120 | yes | yes | no |
| `bhava_cusps` | 360 | yes | no | no |
| `bhava_significance_link` | 10440 | yes | no | no |
| `bhrigu_nadi_point` | 560 | yes | yes | no |
| `chandra_bala_natal_baseline` | 120 | yes | yes | no |
| `chart_center_of_gravity` | 580 | yes | no | no |
| `chart_cluster` | 2610 | yes | no | no |
| `combustion_per_varga` | 1450 | yes | no | no |
| `combustion_relationship` | 5 | yes | no | no |
| `composite_dispositor_strength` | 90 | yes | yes | no |
| `conjunction_per_varga` | 1269 | yes | yes | no |
| `conjunction_special_point` | 357 | yes | no | no |
| `conjunction_within_orb` | 25 | yes | yes | no |
| `contradiction_pair` | 3480 | yes | no | no |
| `convergence_count` | 6090 | yes | no | no |
| `cusp_kp_lords` | 480 | yes | no | no |
| `dhaiya_period` | 1410 | yes | yes | no |
| `dispositor_chain_per_varga` | 2610 | yes | yes | no |
| `dispositor_tree` | 2900 | yes | no | no |
| `dosha_label` | 99 | yes | yes | no |
| `eclipse_proximity_natal` | 10 | yes | yes | no |
| `esoteric_point_avayogi` | 140 | yes | yes | no |
| `esoteric_point_bhrigu_bindu` | 70 | yes | yes | no |
| `esoteric_point_brahma` | 160 | yes | yes | no |
| `esoteric_point_mrityu` | 210 | yes | yes | no |
| `esoteric_point_pranapada_sphuta` | 70 | yes | yes | no |
| `esoteric_point_shiva` | 140 | yes | yes | no |
| `esoteric_point_sphuta_fertility` | 140 | yes | no | no |
| `esoteric_point_sri_yantra_position` | 30 | yes | yes | no |
| `esoteric_point_trikona_dasha_sphuta` | 10 | yes | yes | no |
| `esoteric_point_vishnu` | 140 | yes | yes | no |
| `esoteric_point_yogi` | 140 | yes | yes | no |
| `esoteric_point_yogi_system` | 50 | yes | no | no |
| `graha_avastha_baladi` | 90 | yes | yes | no |
| `graha_avastha_baladi_per_varga` | 2610 | yes | no | no |
| `graha_avastha_deepta` | 90 | yes | yes | no |
| `graha_avastha_deeptaadi_per_varga` | 2610 | yes | no | no |
| `graha_avastha_jagrad` | 90 | yes | yes | no |
| `graha_avastha_jagradadi_per_varga` | 90 | yes | no | no |
| `graha_avastha_lajjitadi` | 90 | yes | yes | no |
| `graha_avastha_lajjitadi_per_varga` | 90 | yes | no | no |
| `graha_avastha_lifetime_exposure_summary` | 90 | yes | yes | no |
| `graha_avastha_sayanadi` | 90 | yes | yes | no |
| `graha_avastha_sayanadi_per_varga` | 90 | yes | no | no |
| `graha_centrality` | 2610 | yes | no | no |
| `graha_cheshta_bala_per_varga` | 1470 | yes | no | no |
| `graha_composite_state_classification` | 90 | yes | yes | no |
| `graha_dignity_per_varga` | 2610 | yes | yes | no |
| `graha_dispositor_chain` | 90 | yes | yes | no |
| `graha_drik_bala_per_varga` | 1470 | yes | no | no |
| `graha_effective_dignity_modified_by_aspects` | 90 | yes | yes | no |
| `graha_functional_class_per_ascendant` | 140 | yes | yes | no |
| `graha_gandanta` | 103 | yes | no | no |
| `graha_in_house_composite_strength` | 3240 | yes | yes | no |
| `graha_ishta_phala` | 70 | yes | yes | no |
| `graha_kala_bala_per_varga` | 1470 | yes | no | no |
| `graha_kashta_phala` | 70 | yes | yes | no |
| `graha_kp_lords` | 400 | yes | no | no |
| `graha_nakshatra_join` | 1400 | yes | no | no |
| `graha_pada_join` | 400 | yes | no | no |
| `graha_position` | 860 | yes | yes | no |
| `graha_saptavargaja_bala_component` | 70 | yes | yes | no |
| `graha_shadbala_cheshta` | 90 | yes | yes | no |
| `graha_shadbala_dig` | 90 | yes | yes | no |
| `graha_shadbala_drik` | 90 | yes | yes | no |
| `graha_shadbala_kala` | 90 | yes | yes | no |
| `graha_shadbala_naisargika` | 18 | yes | yes | no |
| `graha_shadbala_sthana` | 90 | yes | yes | no |
| `graha_shadbala_total` | 174 | yes | yes | no |
| `graha_sign_attributes` | 200 | yes | yes | no |
| `graha_special_state_rollup` | 450 | yes | yes | no |
| `graha_sthana_bala_per_varga` | 1470 | yes | no | no |
| `graha_tara_bala` | 300 | yes | no | no |
| `graha_tri_deva_role_strength` | 90 | yes | yes | no |
| `graha_vargottama_amplification_factor` | 70 | yes | yes | no |
| `graha_vimsopaka_dasavarga` | 70 | yes | yes | no |
| `graha_vimsopaka_saptavarga` | 70 | yes | yes | no |
| `graha_vimsopaka_shadvarga` | 70 | yes | yes | no |
| `graha_vimsopaka_shodasavarga` | 70 | yes | yes | no |
| `graha_yoga_karaka_flag` | 70 | yes | yes | no |
| `graha_yuddha` | 15 | yes | no | no |
| `graha_yuddha_per_varga` | 93 | yes | no | no |
| `house_bhava_bala_ratio` | 120 | yes | no | no |
| `house_bhava_bala_subscore` | 360 | yes | yes | no |
| `house_bhava_bala_total` | 120 | yes | yes | no |
| `house_chalit` | 225 | yes | no | no |
| `house_strength_classification_rollup` | 120 | yes | yes | no |
| `jaimini_tri_deva_role_per_graha` | 90 | yes | yes | no |
| `janma_shani_period` | 200 | yes | yes | no |
| `kala_sarpa_per_varga` | 290 | yes | yes | no |
| `kantaka_shani_period` | 460 | yes | yes | no |
| `karaka_bhava_concordance` | 8700 | yes | no | no |
| `karaka_chara_position` | 1050 | yes | yes | no |
| `karaka_house_lord_overlap_flag` | 120 | yes | yes | no |
| `karakamsa_position` | 30 | yes | yes | no |
| `karakatva_strength_per_significance` | 600 | yes | yes | no |
| `karaka_web_per_varga` | 2156 | yes | no | no |
| `kendradhipati_dosha` | 20 | yes | no | no |
| `kp_cuspal_significators` | 600 | yes | yes | no |
| `kp_ruling_planets_natal` | 100 | yes | yes | no |
| `lal_kitab_special_point` | 200 | yes | yes | no |
| `lord_aspects_lord_per_varga` | 1788 | yes | yes | no |
| `lord_in_house_per_varga` | 3480 | yes | yes | no |
| `maharsi_specific_point` | 140 | yes | yes | no |
| `midpoint` | 2160 | yes | yes | no |
| `nakshatra_cogravity` | 20 | yes | no | no |
| `nakshatra_conjunction` | 7 | yes | no | no |
| `nakshatra_co_tenancy` | 7 | yes | no | no |
| `nakshatra_cross_ayanamsha` | 36 | yes | no | no |
| `nakshatra_dispositor` | 400 | yes | no | no |
| `nakshatra_dispositor_chain` | 100 | yes | no | no |
| `nakshatra_lord_relationship` | 90 | yes | no | no |
| `nakshatra_pada_sensitive` | 160 | yes | yes | no |
| `nakshatra_statistics` | 69 | yes | no | no |
| `net_argala_per_varga` | 3480 | yes | no | no |
| `nway_config_per_varga` | 168 | yes | no | no |
| `panchadha_maitri` | 210 | yes | no | no |
| `panchaka_flag` | 15 | yes | yes | no |
| `panchanga_abhijit_muhurta` | 6 | yes | yes | no |
| `panchanga_agni_vasa` | 6 | yes | yes | no |
| `panchanga_brahma_muhurta` | 6 | yes | yes | no |
| `panchanga_calendrical` | 18 | yes | yes | no |
| `panchanga_choghadiya_birth` | 2 | yes | yes | no |
| `panchanga_disha_shul` | 4 | yes | yes | no |
| `panchanga_durmuhurta` | 6 | yes | yes | no |
| `panchanga_godhuli_muhurta` | 6 | yes | yes | no |
| `panchanga_gulika_kalam` | 6 | yes | yes | no |
| `panchanga_hora_birth` | 2 | yes | yes | no |
| `panchanga_karana` | 10 | yes | yes | no |
| `panchanga_krakaca` | 6 | yes | yes | no |
| `panchanga_madhyahna_sandhya` | 6 | yes | yes | no |
| `panchanga_nakshatra_moon` | 50 | yes | yes | no |
| `panchanga_nakshatra_shoonya_rashi` | 4 | yes | yes | no |
| `panchanga_nishita_kala` | 6 | yes | yes | no |
| `panchanga_panchaka_classification` | 160 | yes | yes | no |
| `panchanga_pratah_sandhya` | 6 | yes | yes | no |
| `panchanga_rahu_kalam` | 6 | yes | yes | no |
| `panchanga_sashtighati` | 6 | yes | yes | no |
| `panchanga_sayam_sandhya` | 6 | yes | yes | no |
| `panchanga_solar_context` | 6 | yes | yes | no |
| `panchanga_special_yoga_combinations` | 15 | yes | yes | no |
| `panchanga_sun_moon_dynamics` | 14 | yes | yes | no |
| `panchanga_tithi` | 14 | yes | yes | no |
| `panchanga_tithi_shoonya_rashi` | 4 | yes | yes | no |
| `panchanga_vara` | 8 | yes | yes | no |
| `panchanga_varjyam` | 6 | yes | yes | no |
| `panchanga_vijaya_muhurta` | 6 | yes | yes | no |
| `panchanga_visha_ghati` | 6 | yes | yes | no |
| `panchanga_yamaganda_kalam` | 6 | yes | yes | no |
| `panchanga_yamakantaka` | 6 | yes | yes | no |
| `panchanga_yoga` | 8 | yes | yes | no |
| `parivartana_per_varga` | 408 | yes | yes | no |
| `pranic_strength_per_graha` | 90 | yes | yes | no |
| `sade_sati_cancellation_check` | 80 | yes | yes | no |
| `sade_sati_concurrent_dasha_overlay` | 280 | yes | yes | no |
| `sade_sati_cycle` | 320 | yes | yes | no |
| `sade_sati_downstream_cross_reference` | 120 | yes | yes | no |
| `sade_sati_modifier_overlay` | 600 | yes | yes | no |
| `sade_sati_phase` | 3040 | yes | yes | no |
| `sade_sati_phase_quarter` | 3360 | yes | yes | no |
| `sade_sati_saturn_retrograde_subset` | 1112 | yes | yes | no |
| `saham_position` | 5600 | yes | yes | no |
| `sambandha_grade` | 10440 | yes | no | no |
| `sandhi_flag` | 90 | yes | no | no |
| `saturn_derived_point` | 290 | yes | yes | no |
| `sensitive_degree_check` | 550 | yes | no | no |
| `sensitive_point_gulika_mandi` | 140 | yes | no | no |
| `significator_path` | 720 | yes | no | no |
| `special_lagna` | 490 | yes | no | no |
| `sun_derived_upagraha` | 280 | yes | no | no |
| `swamsa_position` | 240 | yes | yes | no |
| `tajik_hadda_lord` | 2400 | yes | yes | no |
| `tajik_triraashipathi` | 20 | yes | yes | no |
| `tajik_vargottama_specific` | 30 | yes | yes | no |
| `tara_bala` | 88 | yes | no | no |
| `tara_bala_natal_baseline` | 270 | yes | yes | no |
| `upagraha_position` | 420 | yes | yes | no |
| `upapada_lagna` | 10 | yes | no | no |
| `vargottama_per_varga` | 2520 | yes | yes | no |
| `vimsopaka_bala_per_graha` | 70 | yes | yes | no |
| `virodha_argala_natal_matrix` | 41760 | yes | yes | no |
| `virupa_drishti` | 5510 | yes | no | no |
| `vishakha_shani_period` | 200 | yes | yes | no |
| `yoga_label` | 75 | yes | yes | no |

---

*End of CONCEPT_COVERAGE_CENSUS v1.0 — Lane L1d, W1. Full JSON at `platform/src/generated/census/concept_reachability_v1.json`. See `REACHABILITY_MATRIX_v1.md` for the full three-way SERVED/NAVIGABLE/PLANNER-KNOWN matrix across all concept kinds (fact_category + dark table + signal_class).*
