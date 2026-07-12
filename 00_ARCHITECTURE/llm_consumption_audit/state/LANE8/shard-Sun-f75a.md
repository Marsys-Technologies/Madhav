# Lane 8 shard — Sun dossier · chart 1c826d5a (last4 f75a)

dossier_id: Sun_1c826d5a
resume_after_row_id: F01491
rows_total: 75 (60 floor + 15 discovered)
rows_done: 75
findings_count: 6

Method (SHAPER #3 — consume, don't re-probe): `wire_reachable` derived from
CONCEPT_RETRIEVABILITY_MATRIX channel of each facet's primary backing table
(`reachable-surgical` ⇒ true; `served-only-by-down-pipeline` / `truly-unreachable` ⇒ false).
`held_in_db` confirmed by read-only SELECTs on chart_facts / chart_dashas fact_category +
Sun-subject counts for chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a. `usable_form` per Charter §7.1
(referential resolvability / narration integrity / budget / signal-to-trivia) — DRAFT rubric,
grading provisional pending Cowork ratification.

Reachable-surgical tables (matrix): chart_facts · chart_divisionals · chart_dashas ·
bodha_msr_signals (partial) · brahma_ontology · brahma_remedy_corpus · classical_text_chunks.

## Per-facet matrix

| row_id | # | facet_group | facet (abbrev) | backing table / fact_category | channel | held | wire | usable |
|---|---|---|---|---|---|---|---|---|
| F00011 | 1 | B-I | Sign/deg/bhoga | chart_facts graha_position | reachable-surgical | Y | Y | Y |
| F00031 | 2 | B-I | House WS + bhava-chalit divergence | chart_facts graha_position/cusp_kp_lords | reachable-surgical | Y | Y | Y |
| F00051 | 3 | B-I | Bhava-madhya dist / sandhi / cusp | chart_facts graha_position + near_boundary flags | reachable-surgical | Y | Y | Y |
| F00071 | 4 | B-I | Nakshatra/pada/lord + KP star/sub | chart_facts graha_nakshatra_join/pada_join/kp_lords | reachable-surgical | Y | Y | Y |
| F00091 | 5 | B-I | Navatara from Moon & Lagna | chart_facts graha_tara_bala/tara_bala | reachable-surgical | Y | Y | Y |
| F00111 | 6 | B-I | Declination/latitude/rise-set/oriental | — (no category) | n/a | N | N | N |
| F00131 | 7 | B-I | Speed / retro phase | chart_facts graha_position | reachable-surgical | Y | Y | Y |
| F00151 | 8 | B-I | Ayana / gola | chart_facts panchanga_solar_context/graha_position | reachable-surgical | Y | Y | Y |
| F00171 | 9 | B-II | Exalt/debil deep-degree | chart_facts graha_dignity_per_varga/effective_dignity | reachable-surgical | Y | Y | Y |
| F00191 | 10 | B-II | Mulatrikona/own/panchadha | chart_facts graha_dignity_per_varga/saptavargaja | reachable-surgical | Y | Y | Y |
| F00211 | 11 | B-II | Neecha-bhanga enumeration | — (no category) | n/a | N | N | N |
| F00231 | 12 | B-II | Vargottama + pushkara | chart_facts vargottama_per_varga (pushkara absent) | reachable-surgical | Y | Y | Y |
| F00251 | 13 | B-II | Mrityu bhaga | — (R-47: computed nowhere) | n/a | N | N | N |
| F00271 | 14 | B-II | Dagdha/tithi-shunya/mrityu rashi | chart_facts panchanga_*_shoonya_rashi | reachable-surgical | Y | Y | Y |
| F00291 | 15 | B-II | Sign-type flavor | chart_facts graha_sign_attributes | reachable-surgical | Y | Y | Y |
| F00311 | 16 | B-III | Shadbala complete tree | chart_facts graha_shadbala_* | reachable-surgical | Y | Y | Y |
| F00331 | 17 | B-III | Ishta/Kashta | chart_facts graha_ishta_phala/kashta_phala | reachable-surgical | Y | Y | Y |
| F00351 | 18 | B-III | Vimsopaka + vaiseshikamsha | chart_facts graha_vimsopaka_* | reachable-surgical | Y | Y | Y |
| F00371 | 19 | B-III | Bhava bala owned+occupied | chart_facts bhava_bala_*/house_bhava_bala_total | reachable-surgical | Y | Y | Y |
| F00391 | 20 | B-III | Pancha-vargiya bala (Tajaka) | — (no category) | n/a | N | N | N |
| F00411 | 21 | B-III | Ashtakavarga BAV/SAV/sodhya | chart_facts ashtakavarga_* | reachable-surgical | Y | Y | Y |
| F00431 | 22 | B-III | Saptavargaja tally / own-varga | chart_facts graha_saptavargaja/dignity_per_varga | reachable-surgical | Y | Y | Y |
| F00451 | 23 | B-IV | Combustion + graha yuddha | chart_facts combustion_relationship/graha_yuddha | reachable-surgical | Y | Y | Y |
| F00471 | 24 | B-IV | Grahan yuti (eclipse) | chart_facts eclipse_proximity_natal | reachable-surgical | Y | Y | Y |
| F00491 | 25 | B-IV | Avastha all five | chart_facts graha_avastha_* (all 5) | reachable-surgical | Y | Y | Y |
| F00511 | 26 | B-IV | Gandanta | chart_facts graha_gandanta | reachable-surgical | Y | Y | Y |
| F00531 | 27 | B-IV | Upagraha contact | chart_facts upagraha_position/gulika_mandi/sun_derived | reachable-surgical | Y | Y | Y |
| F00551 | 28 | B-IV | Saham | chart_facts saham_position | reachable-surgical | Y | Y | Y |
| F00571 | 29 | B-V | Conjunctions + parashari drishti | chart_facts aspect_parashari_*/virupa_drishti | reachable-surgical | Y | Y | Y |
| F00591 | 30 | B-V | Rashi drishti (Jaimini) | chart_facts aspect_jaimini | reachable-surgical | Y | Y | Y |
| F00611 | 31 | B-V | Sambandha classification | chart_facts sambandha_grade | reachable-surgical | Y | Y | Y |
| F00631 | 32 | B-V | Dispositor web | chart_facts dispositor_tree/graha_dispositor_chain | reachable-surgical | Y | Y | Y |
| F00651 | 33 | B-V | Papa/shubha kartari | — (no category; derivable only) | n/a | N | N | N |
| F00671 | 34 | B-V | Argala given/received | chart_facts argala_natal_matrix/net_argala | reachable-surgical | Y | Y | Y |
| F00691 | 35 | B-V | Vedha SBC / latta | — (no sarvatobhadra category) | n/a | N | N | N |
| F00711 | 36 | B-V | Tara bala from Moon | chart_facts graha_tara_bala/tara_bala_natal_baseline | reachable-surgical | Y | Y | Y |
| F00731 | 37 | B-VI | Lordships + functional + yogakaraka | chart_facts graha_functional_class/yoga_karaka_flag | reachable-surgical | Y | Y | Y |
| F00751 | 38 | B-VI | Kendradhipati/badhaka/maraka | chart_facts graha_functional_class_per_ascendant | reachable-surgical | Y | Y | Y |
| F00771 | 39 | B-VI | Naisargika/sthira/chara karaka | chart_facts karaka_chara_position/karakamsa/karaka_web | reachable-surgical | Y | Y | Y |
| F00791 | 40 | B-VI | Arudha involvement | chart_facts arudha_pada/bhava_arudha | reachable-surgical | Y | Y | Y |
| F00811 | 41 | B-VI | Yoga participation (all families) | chart_facts yoga_label (+bodha_msr_signals partial) | reachable-surgical | Y | Y | Y |
| F00831 | 42 | B-VI | Dosha participation | chart_facts dosha_label | reachable-surgical | Y | Y | Y |
| F00851 | 43 | B-VI | 22nd drekkana / 64th navamsha lord | — (no category) | n/a | N | N | N |
| F00871 | 44 | B-VII | Vimshottari lordship + windows | chart_dashas | reachable-surgical | Y | Y | Y |
| F00891 | 45 | B-VII | Dasha-quality (dignity/house of lord) | chart_dashas lord_natal_house/dignity/shadbala | reachable-surgical | Y | Y | Y |
| F00911 | 46 | B-VII | Other dasha systems (yogini/chara/…) | chart_dashas system_id (multi-system) | reachable-surgical | Y | Y | Y |
| F00931 | 47 | B-VII | Transit now (gochara) | bg_transit_engine/rules/moorti/vedha (dynamic, not stored) | truly-unreachable | N | N | N |
| F00951 | 48 | B-VII | Sade-sati / dhaiya | chart_facts sade_sati_*/dhaiya_period | reachable-surgical | Y | Y | Y |
| F00971 | 49 | B-VII | Double-transit (Sa+Ju) | — (transit-based, not stored) | n/a | N | N | N |
| F00991 | 50 | B-VII | Varshaphal role | chart_dashas varsha_year_lord + chart_facts aspect_tajik | reachable-surgical | Y | Y | Y |
| F01011 | 51 | B-VII | Recent/upcoming eclipses on natal deg | chart_facts eclipse_proximity_natal | reachable-surgical | Y | Y | Y |
| F01031 | 52 | B-VII | **Structural×temporal convergence (R-45)** | kala_convergence/kala_taranga | **served-only-by-down-pipeline** | Y | **N** | **N** |
| F01051 | 53 | B-VIII | KP significator ladder | chart_facts kp_cuspal_significators/significator_path/ruling | reachable-surgical | Y | Y | Y |
| F01071 | 54 | B-VIII | Nadi roles / bhrigu-bindu | chart_facts bhrigu_nadi_point/esoteric_point_bhrigu_bindu | reachable-surgical | Y | Y | Y |
| F01091 | 55 | B-VIII | **Deity web (nakshatra deity/adhidevata)** | reference_nakshatra | **truly-unreachable** | Y | **N** | **N** |
| F01111 | 56 | B-VIII | **Remedial chart-priority vs afflictions** | bodha_rm_remedy_prescriptions | **served-only-by-down-pipeline** | Y | **N** | **N** |
| F01131 | 57 | B-VIII | **Medical (body-part/dhatu/dosha)** | bg_medical_mappings | **truly-unreachable** | Y | **N** | **N** |
| F01151 | 58 | B-VIII | **Graha-intrinsic sambandha table** | reference_planets | **truly-unreachable** | Y | **N** | **N** |
| F01171 | 59 | B-VIII | Nodal axis relations | chart_facts dispositor_tree/sambandha_grade/nakshatra_join | reachable-surgical | Y | Y | Y |
| F01191 | 60 | B-VIII | Special-lagna relations | chart_facts special_lagna | reachable-surgical | Y | Y | Y |
| F01211 | 61 | DISC panchanga | Muhurta/kalam window catalog | chart_facts panchanga_* (24 cats) | reachable-surgical | Y | Y | Y |
| F01231 | 62 | DISC lal-kitab | Lal Kitab special point | chart_facts lal_kitab_special_point | reachable-surgical | Y | Y | Y |
| F01251 | 63 | DISC maharishi | Maharishi-specific point | chart_facts maharsi_specific_point | reachable-surgical | Y | Y | Y |
| F01271 | 64 | DISC composite | Chart-level composite/rollup analytics | chart_facts chart_center_of_gravity/cluster/centrality/… | reachable-surgical | Y | Y | Y |
| F01291 | 65 | DISC meta | Contradiction/convergence tallies | chart_facts contradiction_pair/convergence_count | reachable-surgical | Y | Y | Y |
| F01311 | 66 | DISC karaka | Karaka-bhava concordance/overlap | chart_facts karaka_bhava_concordance/overlap_flag | reachable-surgical | Y | Y | Y |
| F01331 | 67 | DISC western | Midpoints | chart_facts midpoint | reachable-surgical | Y | Y | Y |
| F01351 | 68 | DISC nakshatra | Co-gravity/co-tenancy/stats | chart_facts nakshatra_cogravity/co_tenancy/statistics | reachable-surgical | Y | Y | Y |
| F01371 | 69 | DISC swamsa | Swamsa position | chart_facts swamsa_position | reachable-surgical | Y | Y | Y |
| F01391 | 70 | DISC tajik | Hadda/triraashipathi/vargottama | chart_facts tajik_hadda_lord/triraashipathi/vargottama | reachable-surgical | Y | Y | Y |
| F01411 | 71 | DISC esoteric | Sphuta point web (10+ points) | chart_facts esoteric_point_* | reachable-surgical | Y | Y | Y |
| F01431 | 72 | DISC pranic | Pranic strength per graha | chart_facts pranic_strength_per_graha | reachable-surgical | Y | Y | Y |
| F01451 | 73 | DISC tri-deva | Tri-deva role strength (Jaimini) | chart_facts graha_tri_deva_role/jaimini_tri_deva | reachable-surgical | Y | Y | Y |
| F01471 | 74 | DISC shani | Shani special-period catalog (6 types) | chart_facts *_shani_period | reachable-surgical | Y | Y | Y |
| F01491 | 75 | DISC derived-pts | Saturn/Sun-derived special points | chart_facts saturn_derived_point/sun_derived_upagraha | reachable-surgical | Y | Y | Y |

## Dossier rollup

- facets_total: **75**
- held_in_db=true: **66** (9 absent-by-nonexistence)
- wire_reachable=true: **61**
- reachable_in_2_calls=true: **61** (all reachable facets resolve in a single chart_facts / chart_dashas SELECT)
- usable_form=true: **61**
- **held-but-not-received: 5** (held=true, wire_reachable=false) — F01031, F01091, F01111, F01131, F01151
- absent-by-nonexistence (held=false → UNREACHABLE by non-existence): 9 — F00111, F00211, F00251, F00391, F00651, F00691, F00851, F00931, F00971
- dossier_completeness_pct = 61/75 = **81.3%**
- **dossier_verdict: PARTIAL** — the acharya-grade synthesis spine (position, dignity, full
  shadbala tree, ashtakavarga, all five avastha sets, relational web, dispositor chain,
  karaka portfolio, dasha lordship + dasha-quality, yogas, doshas, KP ladder, and the 15
  discovered composite/esoteric layers) is entirely reachable-surgical and composes cleanly.
  It is downgraded from SYNTHESIZABLE by 5 held-but-not-received facets — most materially the
  R-45 structural×temporal convergence (which of Sun's promises are temporally ripe: the core
  of time-indexed prediction) and the chart-specific remedial priority — plus 9 non-existent
  classical facets (mrityu-bhaga R-47, neecha-bhanga enumeration, pancha-vargiya bala, SBC
  vedha, 22nd-drekkana/64th-navamsha lords, live transit/double-transit).

## Findings (root-caused; Charter §2)

**FN-1 · F01031 · class 1 UNREACHABLE (served-only-by-down-pipeline) · HIGH.** Sun's
structural×temporal convergence (R-45 asset — which of its yogas/promises are temporally ripe,
recent-past/near-future) is HELD (kala_convergence / kala_taranga populated) but the matrix
marks kala_convergence `served-only-by-down-pipeline`: no MCP tool surfaces it to a consuming
LLM. The dossier cannot answer "is Sun's promise active now" — the exact time-indexed-prediction
question. Dedup: cognate to anchor R-45 (convergence empty/unreached family).

**FN-2 · F01111 · class 1 UNREACHABLE (served-only-by-down-pipeline) · MED.** Sun's
chart-specific remedial prescription (whether served remedy priority reflects Sun's actual
afflictions) sits in bodha_rm_remedy_prescriptions, `served-only-by-down-pipeline`. Generic
graha→remedy corpus (brahma_remedy_corpus) is reachable, but the chart-tuned priority is not.

**FN-3 · F01131 · class 1 UNREACHABLE (truly-unreachable) · MED.** Sun's medical significations
(avayava/dhatu/vata-pitta-kapha/disease from its afflictions) live in bg_medical_mappings,
`truly-unreachable`. No wire path; medical dossier facet cannot be composed.

**FN-4 · F01091 · class 1 UNREACHABLE (truly-unreachable) · MED.** Nakshatra deity /
adhidevata / pratyadhidevata (deity web) for Sun's nakshatra is held in reference_nakshatra,
`truly-unreachable`. Ishta-devata karakamsa-path IS reachable (karakamsa_position), so the
facet is partially composable, but the deity attributions themselves do not arrive.

**FN-5 · F01151 · class 1 UNREACHABLE (truly-unreachable) · LOW-MED.** Sun's intrinsic
sambandha table (varna/guna/tattva/gender/direction/season/taste/metal/grain/color) is in
reference_planets, `truly-unreachable`. Sign-derived attributes (graha_sign_attributes) reach,
but graha-intrinsic static attributes do not.

**FN-6 · F00251 · class 1 UNREACHABLE-by-nonexistence · MED (anchor R-47).** Mrityu-bhaga is
computed nowhere per graha — no fact_category exists for Sun on this chart. Confirmed absent
(no `mrityu_bhaga` category in chart_facts inventory). Dedup: this is anchor R-47; report as
confirming evidence, not a new register row.

Absent-by-nonexistence rollup (class 1, non-existence subtype; feed §6 concept-completeness
register, dedupe before append): F00111 declination/oriental-occidental; F00211 neecha-bhanga
enumeration; F00391 pancha-vargiya bala; F00651 papa/shubha kartari; F00691 Sarvatobhadra vedha
/ latta; F00851 22nd-drekkana (khareshwara) & 64th-navamsha lord; F00931 live transit-now;
F00971 double-transit (Sa+Ju). These are system-absent facets, not held-but-not-received.

## Rubric caveat
usable_form graded under Charter §7.1 DRAFT rubric (Cowork ratification pending). Grading is
provisional per brief §5; no usable_form value here should be treated as final until ratified.
