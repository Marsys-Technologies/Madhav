# Lane 8 shard trace — Jupiter dossier — chart 482012f1 (71aa)

- dossier_id: Jupiter_482012f1
- entity: Jupiter (fact_subject code `JUP`)
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- facets_total: 75 (60 Appendix-B floor + 15 discovered)
- resume_after_row_id: F01485 (all rows graded)
- status: done

## Method (SHAPER #3 — consume the matrix, don't re-probe)
- `wire_reachable := (channel == 'reachable-surgical')` read from CONCEPT_RETRIEVABILITY_MATRIX.jsonl.
- Backing-channel per table (from matrix): `chart_facts` / `chart_divisionals` / `chart_dashas` = **reachable-surgical**; `kala_*`, `bodha_*` (except 32 msr families), `phala_*`, `mimamsa_*` = **served-only-by-down-pipeline**; `reference_*`, `bg_*`, `yoga_*` = **truly-unreachable**.
- `held_in_db` confirmed via read-only DB spot-checks: `JUP` holds rows across ~80 chart_facts categories; kala_convergence=6484, bodha_rm_remedy_prescriptions=135, chart_dashas=483060, chart_divisionals=21992, yoga_label+dosha_label=144.

## Per-facet matrix

| # | facet_group | facet_text (abbr) | backing table / fact_category | held | wire | ≤2 | usable | channel |
|---|---|---|---|---|---|---|---|---|
|1|B-I|Sign, DMS, bhoga|chart_facts graha_position|T|T|T|T|reachable-surgical|
|2|B-I|House WS + bhava-chalit|chart_facts graha_position/cusp|T|T|T|T|reachable-surgical|
|3|B-I|Bhava-madhya, sandhi, cusp flavor|chart_facts (boundary flags)|T|T|T|T|reachable-surgical|
|4|B-I|Nakshatra/pada/lord, KP star-sub|chart_facts graha_nakshatra_join/kp_lords|T|T|T|T|reachable-surgical|
|5|B-I|Navatara from Moon+Lagna|chart_facts graha_tara_bala/tara_bala|T|T|T|T|reachable-surgical|
|6|B-I|Declination/latitude/rise-set/orient|**not computed**|F|F|F|F|— (nonexistence)|
|7|B-I|Speed/retro geometry|chart_facts graha_position/combustion_per_varga|T|T|T|T|reachable-surgical|
|8|B-I|Ayana/gola|chart_facts graha_shadbala_kala (ayana bala)|T|T|T|T|reachable-surgical|
|9|B-II|Exalt/debil deep-degree|chart_facts graha_dignity_per_varga|T|T|T|T|reachable-surgical|
|10|B-II|Mulatrikona/own/panchadha|chart_facts graha_dignity_per_varga/sambandha_grade|T|T|T|T|reachable-surgical|
|11|B-II|Neecha-bhanga enumeration|**not computed (JUP not debilitated → N/A)**|F|F|F|F|— (nonexistence)|
|12|B-II|Vargottama/pushkara|chart_facts vargottama_per_varga|T|T|T|T|reachable-surgical|
|13|B-II|**Mrityu-bhaga**/yogatara (R-47)|**not computed per graha**|F|F|F|F|— (nonexistence, R-47 anchor)|
|14|B-II|Dagdha/tithi-shunya/mrityu-rashi|chart_facts panchanga_*_shoonya_rashi|T|T|T|T|reachable-surgical|
|15|B-II|Sign-type flavor|chart_facts graha_sign_attributes|T|T|T|T|reachable-surgical|
|16|B-III|Shadbala full tree|chart_facts graha_shadbala_*|T|T|T|T|reachable-surgical|
|17|B-III|Ishta/Kashta|chart_facts graha_ishta/kashta_phala|T|T|T|T|reachable-surgical|
|18|B-III|Vimsopaka + vaiseshikamsha|chart_facts graha_vimsopaka_*|T|T|T|T|reachable-surgical|
|19|B-III|Bhava bala owned/occupied|chart_facts bhava_bala_*|T|T|T|T|reachable-surgical|
|20|B-III|Pancha/dwadash-vargiya|chart_facts graha_saptavargaja_bala_component|T|T|T|T|reachable-surgical|
|21|B-III|Ashtakavarga full|chart_facts ashtakavarga_*|T|T|T|T|reachable-surgical|
|22|B-III|Sapta-vargaja dignity tally|chart_facts graha_saptavargaja/vargottama|T|T|T|T|reachable-surgical|
|23|B-IV|Combustion + graha-yuddha|chart_facts combustion_per_varga/graha_yuddha_per_varga|T|T|T|T|reachable-surgical|
|24|B-IV|Grahan yuti|chart_facts eclipse_proximity_natal|T|T|T|T|reachable-surgical|
|25|B-IV|Avastha all five|chart_facts graha_avastha_*|T|T|T|T|reachable-surgical|
|26|B-IV|Gandanta|chart_facts graha_gandanta|T|T|T|T|reachable-surgical|
|27|B-IV|Upagraha contact|chart_facts upagraha_position/sensitive_point_gulika_mandi|T|T|T|T|reachable-surgical|
|28|B-IV|Saham contacts|chart_facts saham_position|T|T|T|T|reachable-surgical|
|29|B-V|Conjunctions/parashari aspects|chart_facts conjunction_within_orb/aspect_parashari_*/virupa_drishti|T|T|T|T|reachable-surgical|
|30|B-V|Rashi drishti (Jaimini)|chart_facts aspect_jaimini|T|T|T|T|reachable-surgical|
|31|B-V|Sambandha classification|chart_facts sambandha_grade|T|T|T|T|reachable-surgical|
|32|B-V|Dispositor web|chart_facts dispositor_tree/graha_dispositor_chain|T|T|T|T|reachable-surgical|
|33|B-V|Papa/shubha kartari|**not computed as category**|F|F|F|F|— (nonexistence)|
|34|B-V|Argala|chart_facts argala_natal_matrix/net_argala_per_varga|T|T|T|T|reachable-surgical|
|35|B-V|Vedha (SBC/nakshatra/latta)|**not computed natally per graha**|F|F|F|F|— (nonexistence)|
|36|B-V|Tara bala from Moon|chart_facts graha_tara_bala|T|T|T|T|reachable-surgical|
|37|B-VI|Lordships/functional/yogakaraka|chart_facts graha_functional_class_per_ascendant/yoga_karaka_flag|T|T|T|T|reachable-surgical|
|38|B-VI|Kendradhipati/badhaka/maraka|chart_facts functional_class/dosha_label|T|T|T|T|reachable-surgical|
|39|B-VI|Karaka portfolio + karakamsha|chart_facts karaka_web_per_varga/karaka_chara/karakamsa|T|T|T|T|reachable-surgical|
|40|B-VI|Arudha involvement|chart_facts bhava_arudha/arudha_pada|T|T|T|T|reachable-surgical|
|41|B-VI|Yoga participation (every family)|chart_facts yoga_label (+bodha_msr_signals surgical subset)|T|T|T|T|reachable-surgical|
|42|B-VI|Dosha participation (L0 catalog)|chart_facts dosha_label|T|T|T|T|reachable-surgical|
|43|B-VI|22nd drekkana/64th navamsha|chart_divisionals + chart_facts|T|T|T|T|reachable-surgical|
|44|B-VII|Vimshottari lordship+windows|chart_dashas|T|T|T|T|reachable-surgical|
|45|B-VII|Dasha-quality FROM graha|chart_dashas + chart_facts (compose)|T|T|T|T|reachable-surgical|
|46|B-VII|Other dasha systems|chart_dashas (multi-system)|T|T|T|T|reachable-surgical|
|47|B-VII|Transit now / gochara|**transit-now not stored (bg_transit_* rules only)**|F|F|F|F|— (nonexistence/retrieval)|
|48|B-VII|Sade-sati/dhaiya overlay|chart_facts sade_sati_* (JUP overlay present)|T|T|T|T|reachable-surgical|
|49|B-VII|Double-transit (Sa+Ju)|**not stored**|F|F|F|F|— (nonexistence)|
|50|B-VII|Varshaphal role|chart_facts aspect_tajik/tajik_*|T|T|T|T|reachable-surgical|
|51|B-VII|Eclipses/stations on natal deg|chart_facts eclipse_proximity_natal|T|T|T|T|reachable-surgical|
|52|B-VII|**Structural×temporal convergence (R-45)**|kala_convergence (6484 rows)|T|**F**|F|**F**|**served-only-by-down-pipeline**|
|53|B-VIII|KP significator ladder|chart_facts kp_cuspal_significators/kp_ruling_planets/significator_path|T|T|T|T|reachable-surgical|
|54|B-VIII|Nadi/bhrigu-bindu|chart_facts bhrigu_nadi_point/esoteric_point_bhrigu_bindu|T|T|T|T|reachable-surgical|
|55|B-VIII|Deity web|**not materialized per-graha (generic reference only)**|F|F|F|F|— (nonexistence)|
|56|B-VIII|**Remedial priority vs afflictions**|bodha_rm_remedy_prescriptions (135 rows)|T|**F**|F|**F**|**served-only-by-down-pipeline**|
|57|B-VIII|**Medical significations**|bg_medical_mappings / bg_nakshatra_medical|T|**F**|F|**F**|**truly-unreachable / down-pipeline**|
|58|B-VIII|Sambandha table (varna/guna/tattva)|chart_facts graha_sign_attributes|T|T|T|T|reachable-surgical|
|59|B-VIII|Nodal axis relations|chart_facts dispositor_tree (nodes)|T|T|T|T|reachable-surgical|
|60|B-VIII|Special-lagna relations|chart_facts special_lagna|T|T|T|T|reachable-surgical|
|61|DISC|Panchanga/muhurta window catalog|chart_facts panchanga_* (24 cat)|T|T|T|T|reachable-surgical|
|62|DISC|Lal Kitab special point|chart_facts lal_kitab_special_point (JUP=10)|T|T|T|T|reachable-surgical|
|63|DISC|Maharishi-specific point|chart_facts maharsi_specific_point|T|T|T|T|reachable-surgical|
|64|DISC|Chart-level composite rollups|chart_facts chart_center_of_gravity/graha_centrality/composite_*|T|T|T|T|reachable-surgical|
|65|DISC|Contradiction/convergence meta|chart_facts contradiction_pair/convergence_count (JUP=145)|T|T|T|T|reachable-surgical|
|66|DISC|Karaka-bhava concordance|chart_facts karaka_bhava_concordance/karakatva_strength|T|T|T|T|reachable-surgical|
|67|DISC|Midpoint (Western)|chart_facts midpoint (JUP=200)|T|T|T|T|reachable-surgical|
|68|DISC|Nakshatra co-gravity/stats|chart_facts nakshatra_cogravity/co_tenancy/statistics|T|T|T|T|reachable-surgical|
|69|DISC|Swamsa position|chart_facts swamsa_position|T|T|T|T|reachable-surgical|
|70|DISC|Tajika hadda/triraashipathi|chart_facts tajik_hadda_lord/triraashipathi/vargottama_specific|T|T|T|T|reachable-surgical|
|71|DISC|Esoteric sensitive-point web|chart_facts esoteric_point_*|T|T|T|T|reachable-surgical|
|72|DISC|Pranic strength|chart_facts pranic_strength_per_graha (JUP=5)|T|T|T|T|reachable-surgical|
|73|DISC|Tri-deva role strength|chart_facts graha_tri_deva_role_strength/jaimini_tri_deva|T|T|T|T|reachable-surgical|
|74|DISC|Shani special-period catalog|**Saturn-specific; N/A for Jupiter**|F|F|F|F|— (nonexistence/N-A)|
|75|DISC|Saturn/Sun-derived points|**no Jupiter analog; N/A**|F|F|F|F|— (nonexistence/N-A)|

## Dossier rollup
- held_in_db (T): **65 / 75** (held F=10: facets 6,11,13,33,35,47,49,55,74,75 — data-plane nonexistence / N-A)
- wire_reachable (T): **62 / 75**
- reachable_in_2_calls (T): **62 / 75**
- usable_form (T): **62 / 75**
- **held_but_not_received: 3** (facets 52, 56, 57 — held in DB but channel is not reachable-surgical)
- dossier_completeness_pct: 62/75 = **82.7%**
- **dossier_verdict: PARTIAL** — the acharya core (position, dignity, full strength battery, state, relational web, functional roles, dasha, ashtakavarga, karaka, yoga/dosha membership, esoteric points) is fully composable over surgical `chart_facts`/`chart_divisionals`/`chart_dashas`. Material gaps: structural×temporal convergence (the temporal-ripeness read an acharya needs), chart-specific remedial priority, and medical significations are all HELD but marooned behind down-pipeline/unreachable channels; plus 7 data-plane nonexistence gaps (mrityu-bhaga R-47, transit-now, double-transit, kartari, vedha, deity-web, declination). Composable with material gaps → PARTIAL.

## Findings (held-but-not-received — root-caused to Charter §2 class 1)
1. **F01025 / facet 52 — structural×temporal convergence UNREACHABLE (R-45 anchor).** kala_convergence holds 6484 rows for the chart but the matrix marks the whole `kala_convergence` family `served-only-by-down-pipeline` — no surgical MCP tool fronts it. Class 1 UNREACHABLE (served-only-by-down-pipeline sub-type). Severity HIGH — this is the exact facet doctrine names as required ("which of its yogas/promises are temporally ripe"). Suspected layer: MCP contract / serving-query. Dedupe: rediscovers R-45.
2. **F01105 / facet 56 — remedial priority-vs-afflictions UNREACHABLE.** bodha_rm_remedy_prescriptions holds 135 rows; channel `served-only-by-down-pipeline`. Generic remedial reference (brahma_remedy_corpus) is reachable-surgical, but the chart-specific "does served priority reflect actual afflictions" layer is not. Class 1 UNREACHABLE. Severity MEDIUM. Suspected layer: MCP contract.
3. **F01125 / facet 57 — medical significations UNREACHABLE.** bg_medical_mappings = `truly-unreachable`; bg_nakshatra_medical = `served-only-by-down-pipeline`. Jupiter's afflictions→body-part/dhatu/disease mapping is held only in reference/down-pipeline channels no consuming LLM can call. Class 1 UNREACHABLE (truly-unreachable sub-type). Severity MEDIUM. Suspected layer: data-plane reference exposure / MCP contract.

### Secondary (data-plane nonexistence — class 1, UNREACHABLE-by-nonexistence; not held-but-not-received)
- **facet 13 mrityu-bhaga (R-47 anchor):** not computed per graha anywhere — rediscovers R-47. Also facets 6 (declination), 33 (papa/shubha kartari), 35 (vedha/SBC/latta), 47 (transit-now gochara), 49 (double-transit), 55 (deity web) — classical canon calls for them, system never computed them. Feed the Section-6 concept-completeness register, not the held-but-not-received count.
