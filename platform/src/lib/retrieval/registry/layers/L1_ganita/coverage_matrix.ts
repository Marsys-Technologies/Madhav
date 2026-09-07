/**
 * L1 Gaṇita Retrieval Coverage Matrix
 * =====================================
 * Machine-readable map: fact_category → tool URI(s).
 * Used by the R3 CI gate to enforce coverage completeness.
 *
 * Phase R1 finding: 0 of 158 fact_categories were covered before this wave.
 * Phase R2 target: every category maps to ≥1 tool.
 *
 * Authored: Wave 3 Phase R1/R2 (2026-06-16)
 *
 * F-B32 (NIRMĀṆA campaign, 2026-09-07): this list was found stale against the live canonical
 * chart's fact_category universe (169 hand-maintained vs. 219 live — see
 * L1_W6_CLOSE_REPORT_v1_0.md §2/§5 for the full audit). Being closed incrementally, one verified
 * cluster at a time, rather than in one unverified bulk pass — each addition here must be
 * confirmed against the real serving tool's actual query logic, not inferred from naming alone.
 * `graha_avastha_*_per_varga` (5 categories) closed 2026-09-07 slice 1; `graha_{cheshta,drik,
 * kala,sthana}_bala_per_varga` (4 categories) closed 2026-09-07 slice 2; the get_nakshatra.ts
 * cluster (12 categories) closed 2026-09-07 slice 3; special_lagna/upapada_lagna/
 * sensitive_point_gulika_mandi (get_sensitive_points.ts) + sensitive_degree_check/
 * sensitive_point_yogi (get_sensitive_degrees.ts) closed 2026-09-07 slice 4 (5 categories);
 * `ayurdaya` (get_ayurdaya.ts, unconditionally served) closed 2026-09-07 slice 5; `bhava_cusps`
 * (get_kp_cusps.ts, unconditional) + `house_bhava_bala_ratio`/`house_chalit` (get_bhava_bala.ts,
 * opt-in) closed 2026-09-07 slice 6 (3 categories); `dispositor_tree` (get_dispositors.ts,
 * opt-in) closed 2026-09-07 slice 7.
 *
 * `graha_yuddha_per_varga` (17 live rows) was investigated and found genuinely UNREACHABLE by
 * any tool — get_graha_yuddha.ts hardcodes `fact_category = 'graha_yuddha'` (a bare, zero-row-
 * for-this-chart category) with no override mechanism, so the per-varga variant cannot be
 * opted into like every other per_varga category in this file. This is a deeper defect than a
 * stale list entry (a real computed category with no path to any tool at all).
 *
 * Slice 7's sweep (cycle 156) checked every remaining category by name against every
 * L1_ganita/*.ts file: of ~26 remaining after slice 7, `dispositor_tree` was the ONLY one
 * confirmed with a real serving tool at the time — **that sweep's own claim about
 * `karaka_web_per_varga` ("real but not yet built for this chart, a separate concern") was
 * itself wrong, corrected here (2026-09-07, slice 8): it was already covered above via
 * get_karakas.ts, a pre-existing W2 structural-close SC-5 entry the sweep missed.** The
 * remaining ~25 — `aspect_received_by_special_point`, `bhava_significance_link`,
 * `chart_center_of_gravity`, `chart_cluster`, `conjunction_special_point`, `contradiction_pair`,
 * `esoteric_point_sphuta_fertility`, `esoteric_point_yogi_system`, `graha_centrality`,
 * `kendradhipati_dosha`, `nakshatra_co_tenancy`, `nakshatra_dispositor_chain`,
 * `nakshatra_lord_relationship`, `net_argala_per_varga`, `nway_config_per_varga`,
 * `panchadha_maitri`, `sambandha_grade`, `sandhi_flag`, `significator_path`,
 * `sun_derived_upagraha`, `tara_bala` (bare, distinct from the already-covered
 * `graha_tara_bala`), `virupa_drishti`, plus `graha_yuddha_per_varga` above — genuinely had
 * ZERO hits anywhere in `L1_ganita/*.ts` (verified by grep, not assumed from naming). This
 * reframed what remains: F-B32 is no longer mostly "a stale list needs new entries" — it is
 * mostly "these categories have no serving tool at all," the same defect class as
 * `graha_yuddha_per_varga` and, at the asset level, F-B18/F-B19's original `ga_nakshatra`
 * finding.
 *
 * **Slice 8 (2026-09-07): `get_structural_signals.ts` closes 15 of these 25** — every category
 * confirmed single-writer-owned by `ga_structural_writer.py` alone (no competing L0/L1/L3
 * writer for the same category).
 *
 * **`esoteric_point_sphuta_fertility`/`esoteric_point_yogi_system` closed here (2026-09-07,
 * cycle 182) via `get_sensitive_points.ts`** — these two were mischaracterized during the
 * cycle-156 sweep above as needing new-endpoint work same as the rest; re-checked, both are
 * cleanly single-writer-owned by `ga_sensitive_writer.py` alone (70 and 25 live rows) and were
 * simply never added to `get_sensitive_points.ts`'s existing `esoteric_point_*` category
 * family — not genuinely unreachable. Added there directly (same flat SELECT shape as every
 * other sibling in that family, no new tool needed).
 *
 * **Cycle 183: 3 more of the "remaining ~10" closed via the SAME tool** —
 * `bhava_significance_link`/`net_argala_per_varga`/`panchadha_maitri` were originally filed as
 * "ambiguous multi-writer ownership" alongside `sandhi_flag`, but re-checking each occurrence
 * individually (not trusting a grouped grep hit count) found every non-`ga_structural_writer.py`
 * mention is a READ, a route descriptor, or a same-named helper feeding a DIFFERENT category —
 * never a second genuine `chart_facts` row construction. All three are single-writer,
 * `ga_structural_writer.py` alone, and added to `get_structural_signals.ts` directly.
 * `esoteric_point_sphuta_fertility`/`esoteric_point_yogi_system` (real `ga_sensitive_writer.py`-
 * owned categories, not `ga_structural`'s) belong with `get_sensitive_points.ts` instead — a
 * separate PR handles those, not assumed merged here since PR ordering is not guaranteed.
 * `sandhi_flag`'s apparent second "writer" turned out to be an unrelated same-named COLUMN on
 * the `chart_dashas` TABLE (`ga_dashas_writer.py`/`_vimshottari_independent_verifier.py`'s own
 * per-period bulk-load schema) — not a `chart_facts.fact_category` mention at all. The real
 * (sole) `chart_facts` writer is `ga_positions_writer.py`, already correctly declared in that
 * asset's `natural_key_partition` (migration 876) but still lacking a serving-layer fix —
 * deliberately deferred to its own pass on `get_positions.ts` (frame-rebasing math, CR-50
 * discipline — a materially higher-blast-radius file than this one) rather than rushed in here.
 *
 * **`sun_derived_upagraha`/`sandhi_flag` closed here (cycle 184) via `get_positions.ts`**:
 * both are genuinely single-writer. `sun_derived_upagraha` (`ga_sensitive_writer.py`, 4
 * Sun-derived shadow points, 20 rows/ayanamsha, carries `house_d1`) joins the
 * `include_upagrahas` opt-in bundle since it IS an upagraha and the `frame` facet applies to it
 * exactly like `upagraha_position`. `sandhi_flag` (`ga_positions_writer.py`'s own
 * `_build_chalit_rows`, already correctly declared in this asset's `natural_key_partition`
 * since migration 876, but never served) is categories-only opt-in — it has no `house_d1` (a
 * flag/reasons pair, not a position) and is not an upagraha, so it does NOT join that bundle.
 * Both were deliberately deferred across cycles 181-183 pending a careful pass on this
 * specific, higher-blast-radius file (frame-rebasing math, CR-50 discipline) rather than a
 * rushed addition riding along with an unrelated tool's fix. Bare `tara_bala`
 * (`ga_structural_writer.py`) remains the last open F-B32 category as of this PR — a separate
 * PR (not assumed merged here) closes it via `get_structural_signals.ts`. See
 * `L1_W6_CLOSE_REPORT_v1_0.md` §3.5/§5 for the full, current account of every category's
 * disposition.
 */

/** Every chart_facts.fact_category that exists for chart_id=native */
export const CHART_FACTS_CATEGORIES = [
  'anumukha_shani_period',
  'aprakasha_position',
  'ardha_ashtama_shani_period',
  'argala_natal_matrix',
  'arudha_pada',
  'ashtakavarga_anubindu',
  'ashtakavarga_bindu',
  'ashtakavarga_bindu_per_varga',
  'ashtakavarga_bindu_sign',
  'ashtakavarga_ekadhipathya_shodhana',
  'ashtakavarga_kakshya_boundary',
  'ashtakavarga_pinda_bhinna',
  'ashtakavarga_pinda_raasi',
  'ashtakavarga_pinda_sarva',
  'ashtakavarga_pinda_sarva_per_varga',
  'ashtakavarga_pinda_sodhita',
  'ashtakavarga_trikona_shodhana',
  'ashtama_shani_period',
  'aspect_jaimini',
  'aspect_jaimini_per_varga',
  'aspect_matrix_summary',
  'aspect_parashari_given',
  'aspect_parashari_per_varga',
  'aspect_parashari_received',
  'aspect_received_by_special_point',
  'aspect_tajik',
  'ayurdaya',
  'bhadra_flag',
  'bhava_arudha',
  'bhava_bala_aspectual',
  'bhava_bala_directional',
  'bhava_bala_lord',
  'bhava_bala_occupant',
  'bhava_bala_positional',
  'bhava_bala_temporal',
  'bhava_bala_total_extended',
  'bhava_cusps',
  'bhava_significance_link',
  'bhrigu_nadi_point',
  'chandra_bala_natal_baseline',
  'chart_center_of_gravity',
  'chart_cluster',
  'composite_dispositor_strength',
  'conjunction_per_varga',
  'conjunction_special_point',
  'conjunction_within_orb',
  'contradiction_pair',
  'cusp_kp_lords',
  'dhaiya_period',
  'dispositor_chain_per_varga',
  'dispositor_tree',
  'dosha_fires',
  'dosha_label',
  'eclipse_proximity_natal',
  'esoteric_point_avayogi',
  'esoteric_point_bhrigu_bindu',
  'esoteric_point_brahma',
  'esoteric_point_chatushphuta',
  'esoteric_point_mrityu',
  'esoteric_point_panchasphuta',
  'esoteric_point_pranapada_sphuta',
  'esoteric_point_shiva',
  'esoteric_point_sphuta_fertility',
  'esoteric_point_sri_yantra_position',
  'esoteric_point_trikona_dasha_sphuta',
  'esoteric_point_trisphuta',
  'esoteric_point_vishnu',
  'esoteric_point_yogi',
  'esoteric_point_yogi_system',
  'graha_avastha_baladi',
  'graha_avastha_baladi_per_varga',
  'graha_avastha_deepta',
  'graha_avastha_deeptaadi_per_varga',
  'graha_avastha_jagrad',
  'graha_avastha_jagradadi_per_varga',
  'graha_avastha_lajjitadi',
  'graha_avastha_lajjitadi_per_varga',
  'graha_avastha_lifetime_exposure_summary',
  'graha_avastha_sayanadi',
  'graha_avastha_sayanadi_per_varga',
  'graha_centrality',
  'graha_cheshta_bala_per_varga',
  'graha_composite_state_classification',
  'graha_degree_flags',
  'graha_dignity_per_varga',
  'graha_dispositor_chain',
  'graha_drik_bala_per_varga',
  'graha_effective_dignity_modified_by_aspects',
  'graha_functional_class_per_ascendant',
  'graha_gandanta',
  'graha_in_house_composite_strength',
  'graha_ishta_phala',
  'graha_kala_bala_per_varga',
  'graha_kashta_phala',
  'graha_kp_lords',
  'graha_nakshatra_join',
  'graha_pada_join',
  'graha_position',
  'graha_saptavargaja_bala_component',
  'graha_shadbala_cheshta',
  'graha_shadbala_dig',
  'graha_shadbala_drik',
  'graha_shadbala_kala',
  'graha_shadbala_naisargika',
  'graha_shadbala_sthana',
  'graha_shadbala_total',
  'graha_sign_attributes',
  'graha_special_state_rollup',
  'graha_sthana_bala_per_varga',
  'graha_tara_bala',
  'graha_tri_deva_role_strength',
  'graha_vargottama_amplification_factor',
  'graha_vimsopaka_dasavarga',
  'graha_vimsopaka_saptavarga',
  'graha_vimsopaka_shadvarga',
  'graha_vimsopaka_shodasavarga',
  'graha_yoga_karaka_flag',
  'graha_yuddha_per_varga',
  'house_bhava_bala_ratio',
  'house_bhava_bala_subscore',
  'house_bhava_bala_total',
  'house_chalit',
  'house_strength_classification_rollup',
  'jaimini_tri_deva_role_per_graha',
  'janma_shani_period',
  'kala_sarpa_per_varga',
  'kantaka_shani_period',
  'karaka_bhava_concordance',
  'karaka_chara_position',
  'karaka_house_lord_overlap_flag',
  'karaka_web_per_varga',
  'karakamsa_position',
  'karakatva_strength_per_significance',
  'kendradhipati_dosha',
  'kp_cuspal_significators',
  'kp_house_significators',
  'kp_planet_significations',
  'kp_ruling_planets_natal',
  'lal_kitab_special_point',
  'lord_aspects_lord_per_varga',
  'lord_in_house_per_varga',
  'maharsi_specific_point',
  'midpoint',
  'nakshatra_co_tenancy',
  'nakshatra_cogravity',
  'nakshatra_conjunction',
  'nakshatra_cross_ayanamsha',
  'nakshatra_dispositor',
  'nakshatra_dispositor_chain',
  'nakshatra_exchange',
  'nakshatra_lord_relationship',
  'nakshatra_pada_sensitive',
  'nakshatra_statistics',
  'net_argala_per_varga',
  'nway_config_per_varga',
  'panchadha_maitri',
  'panchaka_flag',
  'panchanga_abhijit_muhurta',
  'panchanga_agni_vasa',
  'panchanga_brahma_muhurta',
  'panchanga_calendrical',
  'panchanga_choghadiya_birth',
  'panchanga_disha_shul',
  'panchanga_durmuhurta',
  'panchanga_godhuli_muhurta',
  'panchanga_gulika_kalam',
  'panchanga_hora_birth',
  'panchanga_karana',
  'panchanga_krakaca',
  'panchanga_madhyahna_sandhya',
  'panchanga_nakshatra_moon',
  'panchanga_nakshatra_shoonya_rashi',
  'panchanga_nishita_kala',
  'panchanga_panchaka_classification',
  'panchanga_pratah_sandhya',
  'panchanga_rahu_kalam',
  'panchanga_sashtighati',
  'panchanga_sayam_sandhya',
  'panchanga_solar_context',
  'panchanga_special_yoga_combinations',
  'panchanga_sun_moon_dynamics',
  'panchanga_tithi',
  'panchanga_tithi_shoonya_rashi',
  'panchanga_vara',
  'panchanga_varjyam',
  'panchanga_vijaya_muhurta',
  'panchanga_visha_ghati',
  'panchanga_yamaganda_kalam',
  'panchanga_yamakantaka',
  'panchanga_yoga',
  'parivartana_per_varga',
  'pranic_strength_per_graha',
  'sade_sati_cancellation_check',
  'sade_sati_concurrent_dasha_overlay',
  'sade_sati_cycle',
  'sade_sati_downstream_cross_reference',
  'sade_sati_modifier_overlay',
  'sade_sati_phase',
  'sade_sati_phase_quarter',
  'sade_sati_saturn_retrograde_subset',
  'saham_position',
  'sambandha_grade',
  'sandhi_flag',
  'saturn_derived_point',
  'sensitive_degree_check',
  'sensitive_point_gulika_mandi',
  'sensitive_point_yogi',
  'significator_path',
  'special_lagna',
  'sun_derived_upagraha',
  'swamsa_position',
  'tajik_hadda_lord',
  'tajik_triraashipathi',
  'tajik_vargottama_specific',
  'tara_bala_natal_baseline',
  'upagraha_position',
  'upapada_lagna',
  'vargottama_per_varga',
  'vimsopaka_bala_per_graha',
  'virodha_argala_natal_matrix',
  'virupa_drishti',
  'vishakha_shani_period',
  'yoga_fires',
  'yoga_label',
] as const

export type ChartFactsCategory = (typeof CHART_FACTS_CATEGORIES)[number]

/** Coverage map: category → covering tool URI(s) */
export const CATEGORY_TOOL_COVERAGE: Record<ChartFactsCategory, string[]> = {
  // ── Positions ──────────────────────────────────────────────────────────────
  graha_position:                       ['marsys://tool/L1/get_positions'],
  upagraha_position:                    ['marsys://tool/L1/get_positions'],
  aprakasha_position:                   ['marsys://tool/L1/get_positions'],
  karaka_chara_position:                ['marsys://tool/L1/get_karakas'],
  // W2 structural-close SC-5 (serving-side only, no writer change): real, computed,
  // previously-unserved category; opt-in via categories:["nakshatra_cross_ayanamsha"] on
  // get_positions (not on the default page — see get_positions.ts header comment).
  nakshatra_cross_ayanamsha:            ['marsys://tool/L1/get_positions'],
  // F-B32 (cycle 184): sun_derived_upagraha joins the include_upagrahas bundle (has house_d1,
  // frame facet applies); sandhi_flag is categories-only opt-in (no house_d1, not an upagraha)
  // — see get_positions.ts header comment for the full disambiguation account.
  sun_derived_upagraha:                 ['marsys://tool/L1/get_positions'],
  sandhi_flag:                          ['marsys://tool/L1/get_positions'],

  // ── Strength / Shadbala ───────────────────────────────────────────────────
  graha_shadbala_cheshta:               ['marsys://tool/L1/get_strength'],
  graha_shadbala_dig:                   ['marsys://tool/L1/get_strength'],
  graha_shadbala_drik:                  ['marsys://tool/L1/get_strength'],
  graha_shadbala_kala:                  ['marsys://tool/L1/get_strength'],
  graha_shadbala_naisargika:            ['marsys://tool/L1/get_strength'],
  graha_shadbala_sthana:                ['marsys://tool/L1/get_strength'],
  graha_shadbala_total:                 ['marsys://tool/L1/get_strength'],
  // F-B32 (2026-09-07, slice 2/N): opt-in only, same doctrine as the avastha per-varga slice
  // above — get_strength.ts's query is `fact_category = ANY($2)` over the caller's `categories`
  // param, `STRENGTH_CATEGORIES` being only the default 21. Real per-varga breakdown of the
  // cheshta/drik/kala/sthana shadbala components above; 735/735/735/735 live rows (canonical
  // chart) confirm populated, not stray.
  graha_cheshta_bala_per_varga:         ['marsys://tool/L1/get_strength'],
  graha_drik_bala_per_varga:            ['marsys://tool/L1/get_strength'],
  graha_kala_bala_per_varga:            ['marsys://tool/L1/get_strength'],
  graha_sthana_bala_per_varga:          ['marsys://tool/L1/get_strength'],
  graha_vimsopaka_dasavarga:            ['marsys://tool/L1/get_strength'],
  graha_vimsopaka_saptavarga:           ['marsys://tool/L1/get_strength'],
  graha_vimsopaka_shadvarga:            ['marsys://tool/L1/get_strength'],
  graha_vimsopaka_shodasavarga:         ['marsys://tool/L1/get_strength'],
  vimsopaka_bala_per_graha:             ['marsys://tool/L1/get_strength'],
  graha_saptavargaja_bala_component:    ['marsys://tool/L1/get_strength'],
  graha_ishta_phala:                    ['marsys://tool/L1/get_strength'],
  graha_kashta_phala:                   ['marsys://tool/L1/get_strength'],
  pranic_strength_per_graha:            ['marsys://tool/L1/get_strength'],
  graha_in_house_composite_strength:    ['marsys://tool/L1/get_strength'],
  graha_composite_state_classification: ['marsys://tool/L1/get_strength'],
  graha_special_state_rollup:           ['marsys://tool/L1/get_strength'],
  graha_yoga_karaka_flag:               ['marsys://tool/L1/get_strength'],
  graha_tri_deva_role_strength:         ['marsys://tool/L1/get_strength'],
  karakatva_strength_per_significance:  ['marsys://tool/L1/get_karakas'],

  // ── Dignity / Sign state ──────────────────────────────────────────────────
  graha_dignity_per_varga:                    ['marsys://tool/L1/get_dignity'],
  graha_effective_dignity_modified_by_aspects:['marsys://tool/L1/get_dignity'],
  graha_sign_attributes:                      ['marsys://tool/L1/get_dignity'],
  graha_vargottama_amplification_factor:      ['marsys://tool/L1/get_dignity'],
  vargottama_per_varga:                       ['marsys://tool/L1/get_dignity'],
  graha_functional_class_per_ascendant:       ['marsys://tool/L1/get_dignity'],

  // ── Ashtakavarga ─────────────────────────────────────────────────────────
  ashtakavarga_bindu:                 ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_anubindu:              ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_pinda_bhinna:          ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_pinda_sarva:           ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_pinda_sodhita:         ['marsys://tool/L1/get_ashtakavarga'],
  // W2 structural-close SC-4 (serving-side only, no writer change — see get_ashtakavarga.ts
  // header comment): these are real, computed, previously-unserved refinement categories.
  ashtakavarga_bindu_sign:            ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_pinda_raasi:           ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_trikona_shodhana:      ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_ekadhipathya_shodhana: ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_kakshya_boundary:      ['marsys://tool/L1/get_ashtakavarga'],
  // opt-in only (not on the default page — large per-varga row sets), reachable via an
  // explicit `categories` request; still genuinely served, per the coverage doctrine (§5.2).
  ashtakavarga_bindu_per_varga:       ['marsys://tool/L1/get_ashtakavarga'],
  ashtakavarga_pinda_sarva_per_varga: ['marsys://tool/L1/get_ashtakavarga'],

  // ── Bhava Bala / House Strength ───────────────────────────────────────────
  bhava_bala_aspectual:             ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_directional:           ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_lord:                  ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_occupant:              ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_positional:            ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_temporal:              ['marsys://tool/L1/get_bhava_bala'],
  bhava_bala_total_extended:        ['marsys://tool/L1/get_bhava_bala'],
  house_bhava_bala_subscore:        ['marsys://tool/L1/get_bhava_bala'],
  house_bhava_bala_total:           ['marsys://tool/L1/get_bhava_bala'],
  house_strength_classification_rollup: ['marsys://tool/L1/get_bhava_bala'],
  // F-B32 (2026-09-07, slice 6/N): opt-in only, same "fact_category = ANY($2)" doctrine as
  // every prior opt-in slice (get_bhava_bala.ts:57) — neither is in the tool's own default
  // BB_CATEGORIES, but the query is fully data-driven. Live rows (canonical chart):
  // house_bhava_bala_ratio=60, house_chalit=225.
  house_bhava_bala_ratio:           ['marsys://tool/L1/get_bhava_bala'],
  house_chalit:                     ['marsys://tool/L1/get_bhava_bala'],

  // ── Aspects ───────────────────────────────────────────────────────────────
  aspect_parashari_given:    ['marsys://tool/L1/get_aspects'],
  aspect_parashari_received: ['marsys://tool/L1/get_aspects'],
  aspect_parashari_per_varga:['marsys://tool/L1/get_aspects'],
  aspect_jaimini:            ['marsys://tool/L1/get_aspects'],
  aspect_jaimini_per_varga:  ['marsys://tool/L1/get_aspects'],
  aspect_matrix_summary:     ['marsys://tool/L1/get_aspects'],
  aspect_tajik:              ['marsys://tool/L1/get_aspects'],
  conjunction_within_orb:    ['marsys://tool/L1/get_aspects'],
  conjunction_per_varga:     ['marsys://tool/L1/get_aspects'],
  lord_aspects_lord_per_varga:['marsys://tool/L1/get_aspects'],
  lord_in_house_per_varga:   ['marsys://tool/L1/get_aspects'],

  // ── Yoga / Dosha ─────────────────────────────────────────────────────────
  yoga_fires:    ['marsys://tool/L1/get_yoga_dosha'],
  yoga_label:    ['marsys://tool/L1/get_yoga_dosha'],
  dosha_fires:   ['marsys://tool/L1/get_yoga_dosha'],
  dosha_label:   ['marsys://tool/L1/get_yoga_dosha'],
  bhadra_flag:   ['marsys://tool/L1/get_yoga_dosha'],
  panchaka_flag: ['marsys://tool/L1/get_yoga_dosha'],

  // ── Argala ────────────────────────────────────────────────────────────────
  argala_natal_matrix:         ['marsys://tool/L1/get_argala'],
  virodha_argala_natal_matrix: ['marsys://tool/L1/get_argala'],

  // ── Dispositors / Parivartana ─────────────────────────────────────────────
  graha_dispositor_chain:     ['marsys://tool/L1/get_dispositors'],
  dispositor_chain_per_varga: ['marsys://tool/L1/get_dispositors'],
  composite_dispositor_strength:['marsys://tool/L1/get_dispositors'],
  parivartana_per_varga:      ['marsys://tool/L1/get_dispositors'],
  kala_sarpa_per_varga:       ['marsys://tool/L1/get_dispositors'],
  // F-B32 (2026-09-07, slice 7/N): opt-in only, same "fact_category = ANY($2)" doctrine as
  // every prior opt-in slice (get_dispositors.ts:66) — not in the tool's own default
  // DISP_CATEGORIES, but the query is fully data-driven. 1450 live rows (canonical chart).
  dispositor_tree:            ['marsys://tool/L1/get_dispositors'],

  // ── Sade Sati + Shani periods ─────────────────────────────────────────────
  sade_sati_cycle:                  ['marsys://tool/L1/get_sade_sati'],
  sade_sati_phase:                  ['marsys://tool/L1/get_sade_sati'],
  sade_sati_phase_quarter:          ['marsys://tool/L1/get_sade_sati'],
  sade_sati_modifier_overlay:       ['marsys://tool/L1/get_sade_sati'],
  sade_sati_cancellation_check:     ['marsys://tool/L1/get_sade_sati'],
  sade_sati_concurrent_dasha_overlay:['marsys://tool/L1/get_sade_sati'],
  sade_sati_downstream_cross_reference:['marsys://tool/L1/get_sade_sati'],
  sade_sati_saturn_retrograde_subset:['marsys://tool/L1/get_sade_sati'],
  janma_shani_period:               ['marsys://tool/L1/get_sade_sati'],
  anumukha_shani_period:            ['marsys://tool/L1/get_sade_sati'],
  ardha_ashtama_shani_period:       ['marsys://tool/L1/get_sade_sati'],
  ashtama_shani_period:             ['marsys://tool/L1/get_sade_sati'],
  dhaiya_period:                    ['marsys://tool/L1/get_sade_sati'],
  vishakha_shani_period:            ['marsys://tool/L1/get_sade_sati'],
  kantaka_shani_period:             ['marsys://tool/L1/get_sade_sati'],

  // ── Āyurdāya ──────────────────────────────────────────────────────────────
  // F-B32 (2026-09-07, slice 5/N): get_ayurdaya.ts unconditionally serves this category via a
  // hardcoded `fact_category = 'ayurdaya'` filter (get_ayurdaya.ts:71) — no opt-in ambiguity,
  // the whole tool exists for exactly this one category. 130 live rows (canonical chart),
  // matching the tool's own docstring count exactly.
  ayurdaya:                          ['marsys://tool/L1/get_ayurdaya'],

  // ── Panchanga ─────────────────────────────────────────────────────────────
  panchanga_abhijit_muhurta:         ['marsys://tool/L1/get_panchanga'],
  panchanga_agni_vasa:               ['marsys://tool/L1/get_panchanga'],
  panchanga_brahma_muhurta:          ['marsys://tool/L1/get_panchanga'],
  panchanga_calendrical:             ['marsys://tool/L1/get_panchanga'],
  panchanga_choghadiya_birth:        ['marsys://tool/L1/get_panchanga'],
  panchanga_disha_shul:              ['marsys://tool/L1/get_panchanga'],
  panchanga_durmuhurta:              ['marsys://tool/L1/get_panchanga'],
  panchanga_godhuli_muhurta:         ['marsys://tool/L1/get_panchanga'],
  panchanga_gulika_kalam:            ['marsys://tool/L1/get_panchanga'],
  panchanga_hora_birth:              ['marsys://tool/L1/get_panchanga'],
  panchanga_karana:                  ['marsys://tool/L1/get_panchanga'],
  panchanga_krakaca:                 ['marsys://tool/L1/get_panchanga'],
  panchanga_madhyahna_sandhya:       ['marsys://tool/L1/get_panchanga'],
  panchanga_nakshatra_moon:          ['marsys://tool/L1/get_panchanga'],
  panchanga_nakshatra_shoonya_rashi: ['marsys://tool/L1/get_panchanga'],
  panchanga_nishita_kala:            ['marsys://tool/L1/get_panchanga'],
  panchanga_panchaka_classification: ['marsys://tool/L1/get_panchanga'],
  panchanga_pratah_sandhya:          ['marsys://tool/L1/get_panchanga'],
  panchanga_rahu_kalam:              ['marsys://tool/L1/get_panchanga'],
  panchanga_sashtighati:             ['marsys://tool/L1/get_panchanga'],
  panchanga_sayam_sandhya:           ['marsys://tool/L1/get_panchanga'],
  panchanga_solar_context:           ['marsys://tool/L1/get_panchanga'],
  panchanga_special_yoga_combinations:['marsys://tool/L1/get_panchanga'],
  panchanga_sun_moon_dynamics:       ['marsys://tool/L1/get_panchanga'],
  panchanga_tithi:                   ['marsys://tool/L1/get_panchanga'],
  panchanga_tithi_shoonya_rashi:     ['marsys://tool/L1/get_panchanga'],
  panchanga_vara:                    ['marsys://tool/L1/get_panchanga'],
  panchanga_varjyam:                 ['marsys://tool/L1/get_panchanga'],
  panchanga_vijaya_muhurta:          ['marsys://tool/L1/get_panchanga'],
  panchanga_visha_ghati:             ['marsys://tool/L1/get_panchanga'],
  panchanga_yamaganda_kalam:         ['marsys://tool/L1/get_panchanga'],
  panchanga_yamakantaka:             ['marsys://tool/L1/get_panchanga'],
  panchanga_yoga:                    ['marsys://tool/L1/get_panchanga'],

  // ── Sensitive / Esoteric Points ───────────────────────────────────────────
  esoteric_point_avayogi:            ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_bhrigu_bindu:       ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_brahma:             ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_chatushphuta:       ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_mrityu:             ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_panchasphuta:       ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_pranapada_sphuta:   ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_shiva:              ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_sphuta_fertility:   ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_sri_yantra_position:['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_trikona_dasha_sphuta:['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_trisphuta:          ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_vishnu:             ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_yogi:               ['marsys://tool/L1/get_sensitive_points'],
  esoteric_point_yogi_system:        ['marsys://tool/L1/get_sensitive_points'],
  bhrigu_nadi_point:                 ['marsys://tool/L1/get_sensitive_points'],
  lal_kitab_special_point:           ['marsys://tool/L1/get_sensitive_points'],
  maharsi_specific_point:            ['marsys://tool/L1/get_sensitive_points'],
  midpoint:                          ['marsys://tool/L1/get_sensitive_points'],
  saham_position:                    ['marsys://tool/L1/get_sensitive_points'],
  saturn_derived_point:              ['marsys://tool/L1/get_sensitive_points'],
  nakshatra_pada_sensitive:          ['marsys://tool/L1/get_sensitive_points'],
  // F-B32 (2026-09-07, slice 4/N): opt-in only, same "fact_category = ANY($2)" doctrine as
  // every prior slice (get_sensitive_points.ts:78) — none of these three are in the tool's own
  // default SP_CATEGORIES, but tool_name_bridge.ts:87 explicitly maps the retired
  // `query_special_lagnas` tool name onto this URI, confirming special_lagna's data now lives
  // here rather than in a since-removed dedicated tool. Live rows (canonical chart):
  // special_lagna=245, upapada_lagna=10, sensitive_point_gulika_mandi=70.
  special_lagna:                     ['marsys://tool/L1/get_sensitive_points'],
  upapada_lagna:                     ['marsys://tool/L1/get_sensitive_points'],
  sensitive_point_gulika_mandi:      ['marsys://tool/L1/get_sensitive_points'],

  // ── Sensitive Degrees (Yogi/Avayogi + classical degree checks) ────────────
  // F-B32 (2026-09-07, slice 4/N): get_sensitive_degrees.ts unconditionally serves BOTH
  // categories on its default page via SERVED_FACT_CATEGORIES (not opt-in — no caller override
  // exists, unlike every other tool in this file). F-B14's own fix. Live rows (canonical chart):
  // sensitive_degree_check=275, sensitive_point_yogi=60.
  sensitive_degree_check:            ['marsys://tool/L1/get_sensitive_degrees'],
  sensitive_point_yogi:              ['marsys://tool/L1/get_sensitive_degrees'],

  // ── Karakas / KP / Jaimini ───────────────────────────────────────────────
  arudha_pada:                   ['marsys://tool/L1/get_karakas'],
  // W2 structural-close S-3 (serving-side only, no writer change — see get_karakas.ts header
  // comment): computed by ga_sensitive_writer.py, previously zero serving route.
  bhava_arudha:                  ['marsys://tool/L1/get_karakas'],
  karakamsa_position:            ['marsys://tool/L1/get_karakas'],
  swamsa_position:               ['marsys://tool/L1/get_karakas'],
  karaka_house_lord_overlap_flag:['marsys://tool/L1/get_karakas'],
  // W2 structural-close SC-5 — opt-in only (large per-varga/per-house-pair row sets), reachable
  // via an explicit `categories` request; still genuinely served, per the coverage doctrine (§5.2).
  karaka_web_per_varga:          ['marsys://tool/L1/get_karakas'],
  karaka_bhava_concordance:      ['marsys://tool/L1/get_karakas'],
  kp_cuspal_significators:       ['marsys://tool/L1/get_karakas'],
  kp_ruling_planets_natal:       ['marsys://tool/L1/get_karakas'],
  jaimini_tri_deva_role_per_graha:['marsys://tool/L1/get_karakas'],

  // ── KP Cusps (dedicated) ───────────────────────────────────────────────────
  // F-B32 (2026-09-07, slice 6/N): get_kp_cusps.ts (CR-30's dedicated KP-cusp face) spreads its
  // fixed KP_CATEGORIES unconditionally on every call (get_kp_cusps.ts:130) — no opt-in needed.
  // `cusp_kp_lords`/`kp_ruling_planets_natal` are already covered above via get_karakas;
  // `bhava_cusps` is the one category from that same const that had no entry anywhere in this
  // file. 360 live rows (canonical chart).
  bhava_cusps:                    ['marsys://tool/L1/get_kp_cusps'],

  // ── Avasthas ─────────────────────────────────────────────────────────────
  graha_avastha_baladi:                   ['marsys://tool/L1/get_avasthas'],
  graha_avastha_deepta:                   ['marsys://tool/L1/get_avasthas'],
  graha_avastha_jagrad:                   ['marsys://tool/L1/get_avasthas'],
  graha_avastha_lajjitadi:                ['marsys://tool/L1/get_avasthas'],
  graha_avastha_lifetime_exposure_summary:['marsys://tool/L1/get_avasthas'],
  // F-B32 (2026-09-07): opt-in only (not on the default page — the query is
  // `fact_category = ANY($2)` over the caller's `categories` param, `AVASTHA_CATEGORIES`
  // being only the default subset — get_avasthas.ts:11); real, computed, previously-uncatalogued
  // per-varga refinement categories, same "opt-in still counts as served" doctrine as
  // ashtakavarga_bindu_per_varga above. 1305/1305/45/45/45 live rows respectively (canonical
  // chart) confirm these are populated, not stray.
  graha_avastha_baladi_per_varga:         ['marsys://tool/L1/get_avasthas'],
  graha_avastha_deeptaadi_per_varga:      ['marsys://tool/L1/get_avasthas'],
  graha_avastha_jagradadi_per_varga:      ['marsys://tool/L1/get_avasthas'],
  graha_avastha_lajjitadi_per_varga:      ['marsys://tool/L1/get_avasthas'],
  graha_avastha_sayanadi_per_varga:       ['marsys://tool/L1/get_avasthas'],
  graha_avastha_sayanadi:                 ['marsys://tool/L1/get_avasthas'],

  // ── Nakshatra Semantic Layer ──────────────────────────────────────────────
  // F-B32 (2026-09-07, slice 3/N): get_nakshatra.ts (F-B18/F-B19's fix — this asset previously
  // had NO dedicated serving tool at all) had zero entries in this file despite covering 16
  // fact_categories by its own header comment and NAKSHATRA_CATEGORIES const. These 12 are the
  // ones directly named in that const with confirmed non-trivial live rows (canonical chart):
  // graha_nakshatra_join=700, graha_pada_join=200, graha_kp_lords=200, cusp_kp_lords=240,
  // graha_gandanta=50, nakshatra_dispositor=200, nakshatra_conjunction=1, nakshatra_cogravity=10,
  // graha_tara_bala=150, nakshatra_statistics=34, kp_house_significators=540,
  // kp_planet_significations=505.
  // CORRECTED (migration 878, slice 3 follow-up): this comment previously claimed all three of
  // nakshatra_lord_placement/graha_degree_flags/nakshatra_exchange were docstring overclaims
  // with zero live rows — wrong for two of the three. Grepped the actual writer source
  // (ga_writers/ga_nakshatra_emitters.py) directly: graha_degree_flags/nakshatra_exchange ARE
  // genuinely emitted (real, currently-active code, confirmed by migration 872's own earlier
  // investigation) — their zero-live-rows measurement was the same build-lag artifact cycle
  // 157 already corrected for 6 other categories on this exact writer, not a docstring overclaim.
  // Added below. Only nakshatra_lord_placement is a genuine overclaim (zero writer emission
  // anywhere, not just zero rows) — removed from get_nakshatra.ts itself (migration 878), so it
  // is correctly absent from this file too, not "deliberately excluded despite being claimed".
  // nakshatra_cross_ayanamsha (also in the tool's const) is already covered above via
  // get_positions (W2 SC-5, a separate, earlier, already-correct entry) — not duplicated here.
  // Three more from the F-B32 diff that look nakshatra-adjacent by name (nakshatra_co_tenancy,
  // nakshatra_dispositor_chain, nakshatra_lord_relationship) do NOT appear in get_nakshatra.ts's
  // own category list at all and are NOT added here either — they need their own tool-ownership
  // verification, not an assumed match by naming similarity.
  graha_nakshatra_join:        ['marsys://tool/L1/get_nakshatra'],
  graha_pada_join:             ['marsys://tool/L1/get_nakshatra'],
  graha_kp_lords:              ['marsys://tool/L1/get_nakshatra'],
  cusp_kp_lords:               ['marsys://tool/L1/get_nakshatra'],
  graha_gandanta:              ['marsys://tool/L1/get_nakshatra'],
  graha_degree_flags:          ['marsys://tool/L1/get_nakshatra'],
  nakshatra_dispositor:        ['marsys://tool/L1/get_nakshatra'],
  nakshatra_exchange:          ['marsys://tool/L1/get_nakshatra'],
  nakshatra_conjunction:       ['marsys://tool/L1/get_nakshatra'],
  nakshatra_cogravity:         ['marsys://tool/L1/get_nakshatra'],
  graha_tara_bala:             ['marsys://tool/L1/get_nakshatra'],
  nakshatra_statistics:        ['marsys://tool/L1/get_nakshatra'],
  kp_house_significators:      ['marsys://tool/L1/get_nakshatra'],
  kp_planet_significations:    ['marsys://tool/L1/get_nakshatra'],

  // ── Tajik ─────────────────────────────────────────────────────────────────
  tajik_hadda_lord:          ['marsys://tool/L1/get_tajik'],
  tajik_triraashipathi:      ['marsys://tool/L1/get_tajik'],
  tajik_vargottama_specific: ['marsys://tool/L1/get_tajik'],

  // ── Tara / Chandra Bala ───────────────────────────────────────────────────
  chandra_bala_natal_baseline: ['marsys://tool/L1/get_tara_chandra_bala'],
  tara_bala_natal_baseline:    ['marsys://tool/L1/get_tara_chandra_bala'],

  // ── Eclipse / Misc flags ──────────────────────────────────────────────────
  eclipse_proximity_natal: ['marsys://tool/L1/get_eclipse_flags'],

  // F-B32 (2026-09-07, slice 8/N): get_structural_signals.ts closes ga_structural's residual
  // 15-category gap the cycle-156 sweep found genuinely unreachable by any tool (see the file
  // header comment above). All 15 confirmed single-writer-owned by ga_structural_writer.py with
  // non-trivial live rows for the canonical chart (1 to 5,220 rows each).
  sambandha_grade:                   ['marsys://tool/L1/get_structural'],
  virupa_drishti:                    ['marsys://tool/L1/get_structural'],
  contradiction_pair:                ['marsys://tool/L1/get_structural'],
  conjunction_special_point:         ['marsys://tool/L1/get_structural'],
  nakshatra_dispositor_chain:        ['marsys://tool/L1/get_structural'],
  nakshatra_lord_relationship:       ['marsys://tool/L1/get_structural'],
  nakshatra_co_tenancy:              ['marsys://tool/L1/get_structural'],
  graha_centrality:                  ['marsys://tool/L1/get_structural'],
  chart_cluster:                     ['marsys://tool/L1/get_structural'],
  chart_center_of_gravity:           ['marsys://tool/L1/get_structural'],
  significator_path:                 ['marsys://tool/L1/get_structural'],
  aspect_received_by_special_point:  ['marsys://tool/L1/get_structural'],
  nway_config_per_varga:             ['marsys://tool/L1/get_structural'],
  graha_yuddha_per_varga:            ['marsys://tool/L1/get_structural'],
  kendradhipati_dosha:               ['marsys://tool/L1/get_structural'],
  bhava_significance_link:           ['marsys://tool/L1/get_structural'],
  net_argala_per_varga:              ['marsys://tool/L1/get_structural'],
  panchadha_maitri:                  ['marsys://tool/L1/get_structural'],
} as const

/** Additional non-chart_facts tables that need retrieval coverage */
export const NON_CHART_FACTS_COVERAGE: Record<string, string[]> = {
  // L1 separate tables
  chart_dashas:               ['marsys://tool/L1/get_dashas'],
  chart_divisionals:          ['marsys://tool/L1/get_divisionals'],
  l1_tajik_varsha_year_lords: ['marsys://tool/L1/get_tajik'],

  // L0 corpus tables
  brahma_yoga_catalog:     ['marsys://tool/L0/query_yoga_catalog'],
  brahma_dosha_catalog:    ['marsys://tool/L0/query_dosha_catalog'],
  brahma_remedy_corpus:    ['marsys://tool/L0/query_remedy_corpus'],
  // Drift fix (W2b Batch 2, TABLE_CONCEPT_DISPOSITIONS_v2_0.md): this previously pointed at
  // query_classical_texts, which queries classical_text_chunks — a DIFFERENT table. Corrected
  // to the new dedicated capability wired for brahma_compendium_index itself.
  brahma_compendium_index: ['marsys://tool/L0/query_compendium_index'],

  // L2 bodha tables (populated after Wave 4)
  bodha_signals:            ['marsys://tool/L2/get_msr_signals'],
  bodha_graph:              ['marsys://tool/L2/get_cgm_nodes'],
  bodha_graph_edges:        ['marsys://tool/L2/get_cgm_edges'],
  bodha_domain_links:       ['marsys://tool/L2/get_cdlm_cells'],
  bodha_remediation:        ['marsys://tool/L2/get_remediation'],
  bodha_resonance:          ['marsys://tool/L2/get_resonance'],
  bodha_signal_embeddings:  ['marsys://tool/L2/get_signal_embeddings'],
  synthesis_quality_scorecard: ['marsys://tool/L2/get_scorecard'],
}
