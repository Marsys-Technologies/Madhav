# Lane 8 shard — Mars dossier — chart 482012f1 (last4 71aa)

- entity: Mars (`MAR` / `Mars` / `Mangala` in DB)
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- facets_total: 75 (60 Appendix-B floor + 15 discovered)
- resume_after_row_id: F01483 (all rows graded)
- rubrics: Charter §7.1/§7.2 RATIFIED (GATE_RATIFICATION v1.1) — grading is final, not provisional.

## Method (SHAPER #3 — consume, don't re-probe)
Channel taken from `CONCEPT_RETRIEVABILITY_MATRIX.jsonl` per backing table (no re-probe of reachability):
- `chart_facts` (1219 fam) / `chart_divisionals` (90) / `chart_dashas` (72) → **reachable-surgical** → wire_reachable=TRUE.
- `bodha_msr_signals` → 83/115 fam **served-only-by-down-pipeline** (yoga/dosha signal payload); `bodha_cgm_*`, `bodha_convergence`, `kala_convergence`, `kala_activation`, `phala_*`, `bodha_rm_*`, `bodha_discoveries` → **served-only-by-down-pipeline** → wire_reachable=FALSE.
- `bodha_contradictions`, `bg_medical_mappings`, `reference_nakshatra`, `reference_karakas` → **truly-unreachable** → wire_reachable=FALSE.
`held_in_db` spot-checked via read-only postgres (fact_subject IN MAR/MARS/MAR-%/MAR_%, plus category existence checks).

## Per-facet matrix (H=held_in_db, W=wire_reachable, U=usable_form)

| # | facet_group | facet_text (abbrev) | H | W | U | channel / note |
|---|---|---|---|---|---|---|
| 1 | B-I | Sign/deg/bhoga | T | T | T | chart_facts graha_position · surgical |
| 2 | B-I | House WS **and bhava-chalit** divergence | T | T | F | WS held; chalit-divergence NOT computed (only KP cusps) → nonexistence sub-gap |
| 3 | B-I | Bhava-madhya/sandhi proximity/cusp flavor | T | T | T | near_*_boundary_flag + cusp KP · surgical |
| 4 | B-I | Nakshatra/pada/lord; KP star/sub/subsub | T | T | T | graha_nakshatra_join, graha_pada_join, graha_kp_lords |
| 5 | B-I | Navatara from Moon AND Lagna | T | T | F | tara_bala from Moon held; **from-Lagna absent** |
| 6 | B-I | Declination/kranti/shara/rise-set | F | F | F | **nonexistence** (declination=0) |
| 7 | B-I | Speed/retro/stationary | T | T | T | graha_position motion |
| 8 | B-I | Ayana/gola | T | T | T | via kala_bala ayana component |
| 9 | B-II | Exalt/debil deep-degree distance | T | T | T | graha_effective_dignity / sign_attributes |
| 10 | B-II | Mulatrikona/own/panchadha | T | T | T | graha_sign_attributes |
| 11 | B-II | Neecha-bhanga enumeration | F | F | F | **nonexistence** (no enum category; only MSR modifier) |
| 12 | B-II | Vargottama; **pushkara bhaga/navamsha** | T | T | F | vargottama held; **pushkara=0** nonexistence sub-gap |
| 13 | B-II | **Mrityu bhaga**; yogatara | F | F | F | **nonexistence (R-47 anchor rediscovered)** |
| 14 | B-II | Dagdha/tithi-shunya/mrityu-rashi | T | T | T | panchanga_tithi_shoonya_rashi |
| 15 | B-II | Sign-type flavor | T | T | T | graha_sign_attributes |
| 16 | B-III | Shadbala complete tree | T | T | T | graha_shadbala_* (sthana/dig/kala/cheshta/drik/naisargika/total) |
| 17 | B-III | Ishta/Kashta phala | T | T | T | graha_ishta/kashta_phala |
| 18 | B-III | Vimsopaka + vaiseshikamsha | T | T | T | graha_vimsopaka_* |
| 19 | B-III | Bhava bala owned/occupied | T | T | T | graha_in_house_composite_strength |
| 20 | B-III | Pancha-vargiya bala (Tajaka) | F | F | F | **nonexistence** |
| 21 | B-III | Ashtakavarga full | T | T | T | ashtakavarga_* (BAV/SAV/pinda/sodhita) |
| 22 | B-III | Saptavargaja dignity/own-varga | T | T | T | graha_saptavargaja_bala_component + divisionals |
| 23 | B-IV | Combustion + graha yuddha | T | T | T | combustion_per_varga, graha_yuddha_per_varga |
| 24 | B-IV | Grahan yuti | F | F | F | **nonexistence** |
| 25 | B-IV | Avastha all five sets | T | T | T | graha_avastha_* (baladi/jagrad/deepta/lajjita/sayana) |
| 26 | B-IV | Gandanta proximity | T | T | T | graha_gandanta |
| 27 | B-IV | Upagraha contact | T | T | T | upagraha_position, sensitive_point_gulika_mandi, sun_derived_upagraha |
| 28 | B-IV | Saham contacts | T | T | T | saham_position (40 rows) |
| 29 | B-V | Conjunctions/parashari aspects | T | T | T | aspect_parashari_given, conjunction_within_orb |
| 30 | B-V | Rashi drishti (Jaimini) | F | F | F | **nonexistence** (rashi_drishti=0) |
| 31 | B-V | Sambandha classification | T | T | T | derivable from aspect/conjunction facts |
| 32 | B-V | Dispositor web + terminus | T | T | T | graha_dispositor_chain, nakshatra_dispositor_chain |
| 33 | B-V | Papa/shubha kartari | F | F | F | **nonexistence** |
| 34 | B-V | Argala given/received | T | T | T | argala_natal_matrix, net_argala_per_varga, virodha_argala |
| 35 | B-V | Sarvatobhadra vedha / latta (natal) | F | F | F | **nonexistence** (only transit vedha) |
| 36 | B-V | Tara bala from Moon | T | T | T | graha_tara_bala, tara_bala |
| 37 | B-VI | Lordships/functional/yogakaraka | T | T | T | graha_functional_class_per_ascendant, graha_yoga_karaka_flag |
| 38 | B-VI | Kendradhipati/badhaka/maraka | T | T | F | functional held; **badhaka/maraka dedicated absent** |
| 39 | B-VI | Naisargika + chara karaka portfolio | T | T | T | chara karaka (MATRIKARAKA etc, 70 rows) |
| 40 | B-VI | Arudha involvement | T | T | T | arudha_pada, bhava_arudha |
| **41** | **B-VI** | **Yoga participation — EVERY family** | **T** | **F** | **F** | **HELD-NOT-RECEIVED — bodha_msr_signals served-only-by-down-pipeline (F-M1)** |
| **42** | **B-VI** | **Dosha participation — full catalog** | **T** | **F** | **F** | **HELD-NOT-RECEIVED — MSR/brahma_dosha_catalog down-pipeline (F-M2)** |
| 43 | B-VI | 22nd drekkana / 64th navamsha | F | F | F | **nonexistence** (khareshwara/64th=0) |
| 44 | B-VII | Vimshottari lordship now + windows | T | T | T | chart_dashas (Mars lord, 27309 rows) · surgical |
| 45 | B-VII | Dasha-quality context | T | T | T | chart_dashas lord_natal_* fields |
| 46 | B-VII | Other dasha systems | T | T | T | ashtottari/yogini/mudda in chart_dashas |
| 47 | B-VII | Transit now | T | T | T | transit engine surgical |
| 48 | B-VII | Sade-sati/dhaiya (as receiver) | T | T | T | sade_sati_phase, sade_sati_modifier_overlay |
| 49 | B-VII | Double-transit (Sa+Ju) | F | F | F | **nonexistence** |
| 50 | B-VII | Varshaphal role | T | T | T | chart_dashas varsha_year_lord / mudda |
| 51 | B-VII | Eclipses/stations on natal degree | F | F | F | **nonexistence** |
| **52** | **B-VII** | **Structural×temporal convergence** | **T** | **F** | **F** | **HELD-NOT-RECEIVED — kala_convergence/kala_activation down-pipeline (F-M3, R-45 anchor)** |
| 53 | B-VIII | KP significator ladder / RP | T | T | T | kp_cuspal_significators, significator_path, kp_ruling_planets_natal |
| 54 | B-VIII | Nadi roles (bhrigu-bindu) | T | T | T | bhrigu_nadi_point, esoteric_point_bhrigu_bindu |
| **55** | **B-VIII** | **Deity web (nakshatra/adhidevata)** | **T** | **F** | **F** | **HELD-NOT-RECEIVED — reference_nakshatra truly-unreachable (F-M6)** |
| **56** | **B-VIII** | **Remedial mapping (chart-specific)** | **T** | **T** | **F** | **HELD-NOT-RECEIVED — bodha_rm_* down-pipeline; only generic brahma_remedy_corpus surgical (F-M5)** |
| **57** | **B-VIII** | **Medical significations** | **T** | **F** | **F** | **HELD-NOT-RECEIVED — bg_medical_mappings truly-unreachable (F-M4)** |
| 58 | B-VIII | Sambandha table (varna/guna/tattva…) | T | T | T | graha_sign_attributes + reference_planets |
| 59 | B-VIII | Nodal axis relations | T | T | T | nakshatra_dispositor / node-in-star facts |
| 60 | B-VIII | Special-lagna relations | F | F | F | **nonexistence** (bhava/hora/ghati lagna house-from absent) |
| 61 | DISC panchanga | Muhurta/kalam window catalog | T | T | T | panchanga_* (24 cat) surgical |
| 62 | DISC lal-kitab | Lal Kitab special point | T | T | T | lal_kitab_special_point |
| 63 | DISC maharsi | Maharishi-specific point | T | T | T | maharsi/esoteric category held |
| 64 | DISC overlays | Chart-level composite/rollup | T | T | T | composite_dispositor_strength, graha_centrality, center_of_gravity |
| **65** | **DISC meta** | **Contradiction-pair + convergence-count** | **T** | **T** | **F** | **HELD-NOT-RECEIVED — convergence_count surgical but contradiction_pair truly-unreachable (F-M7)** |
| 66 | DISC karaka | Karaka-bhava concordance/overlap | T | T | T | karaka_bhava_concordance category |
| 67 | DISC western | Midpoint positions | T | T | T | midpoint (120 rows) surgical |
| 68 | DISC nakshatra | Co-gravity/co-tenancy/stats | T | T | T | nakshatra_cross_ayanamsha etc |
| 69 | DISC swamsa | Swamsa position | T | T | T | swamsa category held |
| 70 | DISC tajika | Hadda/triraashipathi/vargottama | T | T | T | tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific |
| 71 | DISC esoteric | Sphuta point web (11 points) | T | T | T | esoteric_point_* (avayogi/brahma/mrityu/vishnu/yogi…) |
| 72 | DISC pranic | Pranic strength per graha | T | T | T | pranic_strength_per_graha |
| 73 | DISC tri-deva | Tri-deva role/strength (Jaimini) | T | T | T | graha_tri_deva_role_strength, jaimini_tri_deva_role_per_graha |
| 74 | DISC shani | Shani special-period catalog | T | T | T | sade_sati_* + shani period facts |
| 75 | DISC derived | Saturn/Sun-derived special points | T | T | T | sun_derived_upagraha, saturn_derived_point |

## Dossier rollup
- held_in_db = **63** / 75 (12 nonexistence: facets 6,11,13,20,24,30,33,35,43,49,51,60 + partial sub-gaps in 2,5,12,38)
- wire_reachable = **58** / 75
- reachable_in_2_calls = **58** / 75 (all surgical paths are single chart_facts/dashas/divisionals call)
- usable_form (COMPOSABLE into dossier) = **52** / 75 → completeness ≈ **69.3%**
- **held_but_not_received = 11** (held=T but W or U =F): facets 2, 5, 12, 38 (partial nonexistence sub-gaps, surgical-served core) + **41, 42, 52, 55, 56, 57, 65** (derived-surface served-only-by-down-pipeline / truly-unreachable)

## Verdict: **PARTIAL** (composable with material gaps)
The deterministic backbone of Mars's dossier is SYNTHESIZABLE at acharya depth — position, dignity, full shadbala tree, all five avastha sets, ashtakavarga, combustion/yuddha, dispositor web, argala, karaka portfolio, arudha, KP ladder, Vimshottari/other dashas, and the discovered esoteric/tajik/midpoint overlays all arrive surgically in usable form. But three synthesis-critical facets — **yoga participation (41), dosha participation (42), and structural×temporal convergence (52, R-45)** — are held in the L2/L3 derived surfaces yet served ONLY by the down-pipeline, so a consuming LLM building Mars's dossier surgically cannot receive "every yoga it constitutes, every dosha it constitutes" (the Mercury-standard core) nor which of its promises are temporally ripe. That is exactly "considering [Mars] without its dossier." Not UNCOMPOSABLE (69% usable, backbone intact) but the yoga/dosha/convergence hole is material → PARTIAL.

## Findings (held-but-not-received + nonexistence; Charter §2 classes)
- **F-M1** (facet 41, yoga participation) — Class 1 UNREACHABLE (served-only-by-down-pipeline). SEV HIGH. Evidence: bodha_msr_signals 4281 Mars-referencing rows; matrix marks 83/115 families `served-only-by-down-pipeline`; no surgical yoga-membership-by-graha tool. Suspected layer: MCP contract / serving-query.
- **F-M2** (facet 42, dosha participation) — Class 1 UNREACHABLE (down-pipeline). SEV HIGH. Full-catalog dosha participation served via MSR / brahma_dosha_catalog down-pipeline; only scattered chart_facts dosha subjects (e.g. mahendra_dosha) surgical. Suspected layer: MCP contract.
- **F-M3** (facet 52, structural×temporal convergence, **R-45 anchor**) — Class 1 UNREACHABLE (down-pipeline). SEV HIGH. kala_convergence/kala_activation `served-only-by-down-pipeline`. Suspected layer: serving-query / MCP contract.
- **F-M4** (facet 57, medical) — Class 1 UNREACHABLE (truly-unreachable). SEV MED. bg_medical_mappings `truly-unreachable`. Suspected layer: MCP contract (no tool fronts L0 medical catalog).
- **F-M5** (facet 56, chart-specific remedial) — Class 1 UNREACHABLE (down-pipeline). SEV MED. bodha_rm_* down-pipeline; generic brahma_remedy_corpus surgical but not affliction-conditioned for Mars. Suspected layer: serving-query.
- **F-M6** (facet 55, deity web) — Class 1 UNREACHABLE (truly-unreachable). SEV LOW-MED. reference_nakshatra `truly-unreachable`.
- **F-M7** (facet 65, contradiction-pair meta) — Class 1 UNREACHABLE (truly-unreachable). SEV LOW. bodha_contradictions `truly-unreachable`; convergence_count half of the facet IS surgical.
- **F-M8** (nonexistence cluster, feeds §6 concept-completeness) — Class 1 UNREACHABLE-by-nonexistence. SEV MED (aggregate). Facets computed NOWHERE for Mars: 13 mrityu-bhaga (**R-47 anchor**), 12 pushkara bhaga/navamsha, 6 declination/kranti, 20 pancha-vargiya bala, 24 grahan-yuti, 30 rashi-drishti (Jaimini), 33 papa/shubha kartari, 35 Sarvatobhadra vedha/latta, 43 22nd-drekkana/64th-navamsha, 49 double-transit, 51 eclipses/stations-on-natal, 60 special-lagna house-from; plus sub-gaps in 2 (bhava-chalit divergence flag), 5 (navatara-from-Lagna), 38 (badhaka/maraka).

## Class-9 improvisation log
- Facet→table mapping and "which channel dominates a mixed table" (bodha_msr_signals 32 surgical / 83 down-pipeline; facet 42 dosha split chart_facts vs MSR; facet 65 split convergence_count vs contradiction_pair) required executor judgment not governed by any tool description → logged as UNGOVERNED JUDGMENT candidates per Charter §7.2.
