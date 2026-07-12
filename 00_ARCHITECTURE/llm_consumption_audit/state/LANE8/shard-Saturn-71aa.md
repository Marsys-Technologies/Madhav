# Lane 8 shard trace — Saturn dossier (chart 482012f1 / last4 71aa)

- dossier_id: Saturn_482012f1
- entity: Saturn — Libra (exalt sign), Vishakha nakshatra (lord Jupiter), pada n/a-null, retrograde=direct, combustion=none
- facets_total (this chart): **75** (60 Appendix-B floor + 15 discovered)
- resume_after_row_id: F01487 (all rows graded)
- grading basis: SHAPER #3 — wire_reachable consumed from `CONCEPT_RETRIEVABILITY_MATRIX.jsonl` (not re-probed). held_in_db spot-checked via read-only postgres against chart_facts / chart_dashas / chart_divisionals on this chart.
- rubric note: usable_form graded per Charter §7.1 (DRAFT-pending-ratification) — grading provisional per Lane 8 brief §5.

## Channel legend
- **rs** = reachable-surgical (chart_facts / chart_dashas / chart_divisionals; MSR reachable slice) → wire_reachable=true
- **sod** = served-only-by-down-pipeline (kala_* / phala_* / bodha_* / mimamsa_*) → wire_reachable=false
- **tu** = truly-unreachable (reference_* / bg_* / yoga_* L0 catalogs) → wire_reachable=false
- **none** = not held anywhere in DB (nonexistence)

## Per-facet retrievability matrix (75 rows)

| row_id | # | facet_group | facet_text (abbrev) | held_db | wire | ≤2call | usable | channel | backing |
|---|---|---|---|---|---|---|---|---|---|
| F00007 | 1 | B-I | Sign, d-m-s; bhoga | Y | Y | Y | Y | rs | chart_facts.graha_position |
| F00027 | 2 | B-I | House whole-sign + bhava-chalit | Y | Y | Y | Y | rs | graha_position.house_d1 + cusp_kp_lords |
| F00047 | 3 | B-I | Bhava madhya / sandhi proximity | Y | Y | Y | Y | rs | chart_facts near_*_boundary_flag |
| F00067 | 4 | B-I | Nakshatra/pada/lord; KP star/sub | Y | Y | Y | Y | rs | graha_nakshatra_join, graha_pada_join, graha_kp_lords |
| F00087 | 5 | B-I | Navatara from Moon AND Lagna | Y | Y | Y | Y | rs | graha_tara_bala, tara_bala |
| F00107 | 6 | B-I | Declination/latitude; udaya-asta; oriental | **N** | N | N | N | none | not computed (graha_position lacks kranti/shara/rise-set) |
| F00127 | 7 | B-I | Speed/ratio/stationary; retro geometry | Y* | Y | Y | Y | rs | retrograde_flag + graha_cheshta_bala (speed value absent) |
| F00147 | 8 | B-I | Ayana (uttara/dakshina); gola | **N** | N | N | N | none | declination-derived; not stored |
| F00167 | 9 | B-II | Exalt/debil deep-degree distance | Y | Y | Y | Y | rs | graha_dignity_per_varga, graha_effective_dignity |
| F00187 | 10 | B-II | Mulatrikona/own/panchadha relation | Y | Y | Y | Y | rs | graha_dignity_per_varga, graha_sign_attributes |
| F00207 | 11 | B-II | Neecha-bhanga enumeration | **N** | N | N | N | none | no category (vacuous — Saturn exalted-sign) |
| F00227 | 12 | B-II | Vargottama; pushkara bhaga/navamsha | Y* | Y | Y | Y | rs | vargottama_per_varga (pushkara absent) |
| F00247 | 13 | B-II | Mrityu bhaga; yogatara proximity | **N** | N | N | N | none | no mrityu_bhaga category (R-47) |
| F00267 | 14 | B-II | Dagdha/tithi-shunya/mrityu rashi | Y* | Y | Y | Y | rs | panchanga_tithi/nakshatra_shoonya_rashi (dagdha partial) |
| F00287 | 15 | B-II | Sign-type flavor chara/sthira | Y | Y | Y | Y | rs | graha_sign_attributes |
| F00307 | 16 | B-III | Shadbala complete tree + norm band | Y | Y | Y | Y | rs | graha_shadbala_* (all six + total) |
| F00327 | 17 | B-III | Ishta/Kashta phala | Y | Y | Y | Y | rs | graha_ishta_phala, graha_kashta_phala |
| F00347 | 18 | B-III | Vimsopaka + vaiseshikamsha ladder | Y* | Y | Y | Y | rs | graha_vimsopaka_* (ladder partial) |
| F00367 | 19 | B-III | Bhava bala owned/occupied | Y | Y | Y | Y | rs | house_bhava_bala_*, bhava_bala_* |
| F00387 | 20 | B-III | Pancha-vargiya / dwadash-vargiya bala | **N** | N | N | N | none | only saptavargaja present |
| F00407 | 21 | B-III | Ashtakavarga BAV/SAV/sodhya + transit filter | Y | Y | Y | Y | rs | ashtakavarga_* (transit-AV-filter part excepted) |
| F00427 | 22 | B-III | Sapta-vargaja dignity tally | Y | Y | Y | Y | rs | graha_saptavargaja_bala_component |
| F00447 | 23 | B-IV | Combustion + graha yuddha | Y | Y | Y | Y | rs | combustion_per_varga, graha_yuddha_per_varga |
| F00467 | 24 | B-IV | Grahan yuti (eclipse assoc) | Y | Y | Y | Y | rs | eclipse_proximity_natal |
| F00487 | 25 | B-IV | Avastha ALL FIVE | Y | Y | Y | Y | rs | graha_avastha_baladi/jagrad/deepta/lajjita/sayana |
| F00507 | 26 | B-IV | Gandanta proximity | Y | Y | Y | Y | rs | graha_gandanta |
| F00527 | 27 | B-IV | Upagraha contact (gulika/mandi/…) | Y | Y | Y | Y | rs | upagraha_position, sensitive_point_gulika_mandi |
| F00547 | 28 | B-IV | Saham contacts | Y | Y | Y | Y | rs | saham_position |
| F00567 | 29 | B-V | Conjunctions; parashari sputa-drishti; special | Y | Y | Y | Y | rs | conjunction_within_orb, aspect_parashari_given, virupa_drishti |
| F00587 | 30 | B-V | Rashi drishti (Jaimini) | Y | Y | Y | Y | rs | aspect_jaimini |
| F00607 | 31 | B-V | Sambandha classification | Y | Y | Y | Y | rs | sambandha_grade |
| F00627 | 32 | B-V | Dispositor web + terminus | Y | Y | Y | Y | rs | dispositor_tree, graha_dispositor_chain, nakshatra_dispositor_chain |
| F00647 | 33 | B-V | Papa/shubha kartari on position | **N** | N | N | N | none | no kartari category |
| F00667 | 34 | B-V | Argala given/received | Y | Y | Y | Y | rs | argala_natal_matrix, net_argala_per_varga, virodha_argala |
| F00687 | 35 | B-V | Vedha: SBC / nakshatra vedha / latta | **N** | N | N | N | none | no natal vedha (bg_transit_vedha=tu, transit-only) |
| F00707 | 36 | B-V | Tara bala from Moon | Y | Y | Y | Y | rs | graha_tara_bala, tara_bala |
| F00727 | 37 | B-VI | Lordships; functional class; yogakaraka | Y | Y | Y | Y | rs | graha_functional_class_per_ascendant, graha_yoga_karaka_flag |
| F00747 | 38 | B-VI | Kendradhipati/badhaka/maraka | Y* | Y | Y | Y | rs | graha_functional_class (badhaka/maraka partial) |
| F00767 | 39 | B-VI | Naisargika/sthira/chara karaka; karakamsha | Y | Y | Y | Y | rs | karaka_web_per_varga, karaka_chara_position, karakamsa_position |
| F00787 | 40 | B-VI | Arudha involvement | Y | Y | Y | Y | rs | arudha_pada, bhava_arudha |
| F00807 | 41 | B-VI | Yoga participation — every family | Y* | Y | Y | Y | rs | yoga_label (full-catalog completeness partial; bodha=sod) |
| F00827 | 42 | B-VI | Dosha participation — full L0 catalog | Y* | Y | Y | Y | rs | dosha_label (brahma_dosha_catalog=sod) |
| F00847 | 43 | B-VI | 22nd drekkana / 64th navamsha; sarpa drekkana | **N** | N | N | N | none | no category |
| F00867 | 44 | B-VII | Vimshottari now + next windows; sandhi | Y | Y | Y | Y | rs | chart_dashas (vimshottari) |
| F00887 | 45 | B-VII | Dasha-quality: lord dignity/house from graha | Y | Y | Y | Y | rs | chart_dashas.lord_natal_house_d1/dignity_d1 |
| F00907 | 46 | B-VII | Other dasha systems (yogini/chara/ashtottari/kalachakra) | Y | Y | Y | Y | rs | chart_dashas.system_id (8 systems) |
| F00927 | 47 | B-VII | Transit now: gochara/vedha/murthi/AV filter | **N** | N | N | N | none | no chart-scoped natal transit (bg_transit_engine=tu, runtime) |
| F00947 | 48 | B-VII | Sade-sati / dhaiya involvement | Y | Y | Y | Y | rs | sade_sati_* (8 categories), dhaiya_period |
| F00967 | 49 | B-VII | Double-transit (Sa+Ju) on natal points | **N** | N | N | N | none | transit-based, not stored |
| F00987 | 50 | B-VII | Varshaphal: year-lord/muntha/tajaka set | Y* | Y | Y | Y | rs | chart_dashas.varsha_year_lord + mudda + aspect_tajik (muntha partial) |
| F01007 | 51 | B-VII | Eclipses/stations on natal degree | Y* | Y | Y | Y | rs | eclipse_proximity_natal (stations partial) |
| F01027 | 52 | B-VII | **Structural×temporal convergence (R-45)** | **Y** | **N** | **N** | **N** | **sod** | kala_convergence / bodha_convergence — HELD-BUT-NOT-RECEIVED |
| F01047 | 53 | B-VIII | KP significator ladder; ruling planet | Y | Y | Y | Y | rs | kp_cuspal_significators, kp_ruling_planets_natal, significator_path |
| F01067 | 54 | B-VIII | Nadi jeeva/karma; bhrigu-bindu | Y | Y | Y | Y | rs | bhrigu_nadi_point, esoteric_point_bhrigu_bindu |
| F01087 | 55 | B-VIII | **Deity web: nakshatra deity/adhidevata** | **Y** | **N** | **N** | **N** | **tu** | reference_nakshatra — HELD-BUT-NOT-RECEIVED (karakamsa path=rs) |
| F01107 | 56 | B-VIII | Remedial mapping (gem/mantra/…) + priority | Y* | Y | Y | Y | rs | brahma_remedy_corpus=rs (chart-specific priority in bodha_rm=sod) |
| F01127 | 57 | B-VIII | **Medical: body-part/dhatu/dosha/disease** | **Y** | **N** | **N** | **N** | **tu** | bg_medical_mappings=tu / bg_nakshatra_medical=sod — HELD-BUT-NOT-RECEIVED |
| F01147 | 58 | B-VIII | **Sambandha table: varna/guna/tattva/…** | **Y** | **N** | **N** | **N** | **tu** | reference_planets — HELD-BUT-NOT-RECEIVED |
| F01167 | 59 | B-VIII | Nodal axis relations | Y* | Y | Y | Y | rs | dispositor_tree, nakshatra_dispositor (agency rules partial) |
| F01187 | 60 | B-VIII | Special-lagna relations | Y | Y | Y | Y | rs | special_lagna |
| F01207 | 61 | DISC | Panchanga/muhurta window catalog | Y | Y | Y | Y | rs | panchanga_* (24 cats) + bhadra/panchaka_flag |
| F01227 | 62 | DISC | Lal Kitab special-point | Y | Y | Y | Y | rs | lal_kitab_special_point |
| F01247 | 63 | DISC | Maharishi-specific point | Y | Y | Y | Y | rs | maharsi_specific_point |
| F01267 | 64 | DISC | Chart-level composite/rollup analytics | Y | Y | Y | Y | rs | chart_center_of_gravity, graha_centrality, composite_* rollups |
| F01287 | 65 | DISC | Contradiction/convergence meta | Y | Y | Y | Y | rs | contradiction_pair, convergence_count (bodha_contradictions=tu excepted) |
| F01307 | 66 | DISC | Karaka-bhava concordance/overlap | Y | Y | Y | Y | rs | karaka_bhava_concordance, karaka_house_lord_overlap_flag |
| F01327 | 67 | DISC | Western midpoints | Y | Y | Y | Y | rs | midpoint |
| F01347 | 68 | DISC | Nakshatra co-gravity/co-tenancy/stats | Y | Y | Y | Y | rs | nakshatra_cogravity/co_tenancy/cross_ayanamsha/statistics |
| F01367 | 69 | DISC | Swamsa position | Y | Y | Y | Y | rs | swamsa_position |
| F01387 | 70 | DISC | Tajika hadda/triraashipathi/vargottama | Y | Y | Y | Y | rs | tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific |
| F01407 | 71 | DISC | Esoteric sphuta-point web | Y | Y | Y | Y | rs | esoteric_point_* (11 categories) |
| F01427 | 72 | DISC | Pranic strength per graha | Y | Y | Y | Y | rs | pranic_strength_per_graha |
| F01447 | 73 | DISC | Tri-deva role strength (Jaimini) | Y | Y | Y | Y | rs | graha_tri_deva_role_strength, jaimini_tri_deva_role_per_graha |
| F01467 | 74 | DISC | Shani special-period catalog (6 types) | Y | Y | Y | Y | rs | anumukha/ardha_ashtama/ashtama/janma/kantaka/vishakha_shani_period |
| F01487 | 75 | DISC | Saturn/Sun-derived special points | Y | Y | Y | Y | rs | saturn_derived_point, sun_derived_upagraha |

`*` = held & reachable but PARTIAL (a named sub-component of the facet is absent/down-pipeline; core is served).

## Dossier rollup

| metric | count | of 75 |
|---|---|---|
| held_in_db | 65 | 86.7% |
| wire_reachable | 61 | 81.3% |
| reachable_in_2_calls | 61 | 81.3% |
| usable_form | 61 | 81.3% |
| **held-but-not-received** (held=T, wire=F) | **4** | 5.3% |
| absent / nonexistence (held=F) | 10 | 13.3% |

**dossier_completeness_pct = usable_form / 75 = 81.3%.**
(Note: the ledger holds 150 Saturn rows = 75 facets × 2 charts; this shard is chart 71aa only → denominator 75. Against the task's literal /150 that is 40.7%, but the single-chart dossier denominator is 75.)

**dossier_verdict: PARTIAL.** The acharya-grade core (positions, dignity, full shadbala tree, ishta/kashta, vimsopaka, ashtakavarga, all five avastha sets, combustion/yuddha, gandanta, upagraha, saham, all aspects + sputa-drishti, sambandha, dispositor web, argala, karaka portfolio, arudha, yoga_label, dosha_label, all 8 dasha systems, dasha-quality context, sade-sati battery, KP ladder, nadi/bhrigu-bindu, special-lagna, plus 15 discovered families incl. tri-deva, pranic, tajika, esoteric-sphuta web, Shani-period catalog) is fully held AND wire-reachable-surgical. But 14 facets cannot be composed as a consuming LLM needs them: 4 held-but-not-received (convergence R-45, deity web, medical, graha-sambandha attribute table) and 10 absent (secondary astronomy, mrityu-bhaga, kartari, vedha, 22DK/64N, transit-now, double-transit, pancha-vargiya bala, neecha-bhanga enum). Material gaps → not SYNTHESIZABLE; core is overwhelmingly intact → not UNCOMPOSABLE.

## Findings (root-caused; Charter §2 taxonomy — all class 1 UNREACHABLE)

**F-SAT-1 (class 1, HIGH) — R-45 structural×temporal convergence held but not wire-reachable.**
Facet 52 (F01027). `kala_convergence` / `bodha_convergence` hold Saturn's temporal-ripeness convergence windows, but matrix channel = `served-only-by-down-pipeline` → a consuming LLM cannot retrieve them over the wire. Evidence: matrix `{"table_name":"kala_convergence","channel":"served-only-by-down-pipeline"}` (33 families) + `bodha_convergence` (29, sod); DB holds kala_convergence rows for this chart. This is the flagship time-lord asset for a Saturn dossier (sade-sati adjacency) invisible to synthesis. Dedupe: relates to anchor R-45. Suspected layer: L3 Kāla serving surface.

**F-SAT-2 (class 1, MEDIUM) — Nakshatra deity / adhidevata web served only from truly-unreachable L0.**
Facet 55 (F01087). Nakshatra deity, adhidevata/pratyadhidevata live in `reference_nakshatra`, matrix channel `truly-unreachable`. Ishta-devata path (karakamsa_position) is rs, but the deity mapping itself is un-fetchable. Evidence: matrix `reference_nakshatra` = truly-unreachable. Suspected layer: L0 reference exposure.

**F-SAT-3 (class 1, MEDIUM) — Medical significations of Saturn's afflictions unreachable.**
Facet 57 (F01127). `bg_medical_mappings` (truly-unreachable) + `bg_nakshatra_medical` (served-only) hold body-part/dhatu/dosha/disease mappings; no chart_facts medical category exists → LLM cannot receive Saturn's medical/disease profile. Evidence: matrix `bg_medical_mappings`=truly-unreachable, `bg_nakshatra_medical`=served-only-by-down-pipeline.

**F-SAT-4 (class 1, MEDIUM) — Graha-sambandha attribute table (varna/guna/tattva/direction/…) unreachable.**
Facet 58 (F01147). These karaka attributes live only in `reference_planets`/`reference_signs` (truly-unreachable); no chart-scoped category. Evidence: matrix `reference_planets`=truly-unreachable. Blocks the classical significator layer of the dossier.

**F-SAT-5 (class 1, MEDIUM) — Secondary astronomical coordinates not computed.**
Facets 6 & 8 (F00107, F00147). No declination/kranti, celestial latitude/shara, rise-set (udaya/asta), oriental/occidental, ayana (uttarayana/dakshinayana), or gola facts in `graha_position` or anywhere. Evidence: `graha_position` D1_SAT keys = {sign, sign_lord, nakshatra, nakshatra_lord, pada, longitude_sidereal, house_d1, retrograde_flag, combustion_state} only. Nonexistence → concept-completeness register.

**F-SAT-6 (class 1, MEDIUM-HIGH) — Classical sensitive-degree & natal-vedha facets absent (echoes R-47).**
Facets 13, 35, 43, 33 (F00247, F00687, F00847, F00647). Mrityu-bhaga, yogatara proximity, Sarvatobhadra/nakshatra vedha + latta, 22nd-drekkana (khareshwara), 64th-navamsha lord, and papa/shubha kartari have no backing category. Evidence: absent from the chart's full fact_category enumeration. Dedupe: R-47 (mrityu-bhaga computed nowhere). Nonexistence.

**F-SAT-7 (class 1, MEDIUM) — Transit-now and double-transit not chart-scoped.**
Facets 47 & 49 (F00927, F00967). Gochara-now, transit vedha, murthi, transit-AV filter, and Saturn+Jupiter double-transit are runtime/ephemeris computations; `bg_transit_engine`/`bg_transit_rules`/`bg_transit_vedha` are truly-unreachable L0 and no precomputed chart-scoped transit facts exist. Evidence: matrix bg_transit_* = truly-unreachable; no transit fact_category on chart. Nonexistence for natal store.

**F-SAT-8 (class 1, LOW) — Pancha-vargiya bala & neecha-bhanga enumeration absent.**
Facets 20 & 11 (F00387, F00207). Only saptavargaja bala present (no pancha-vargiya/dwadash-vargiya Tajaka bala); no neecha-bhanga enumeration category (vacuous here — Saturn in own-friend Libra/exalt-sign, not debilitated). Nonexistence.
