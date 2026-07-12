# Lane 8 shard — Lagna dossier — chart 482012f1 (…71aa)

entity: Lagna · chart_id: 482012f1-710e-4a25-994a-93821f5871aa · facets_total: 75 (60 floor + 15 discovered)
resume_after_row_id: F01490 (shard complete)
status: done

## Method
- Facet list from `ledgers/facets.jsonl` (entity==Lagna, chart 482012f1) — 75 rows.
- SHAPER #3 consumed: `wire_reachable = (matrix channel == 'reachable-surgical')`. NOT re-probed.
  - chart_facts / chart_divisionals / chart_dashas / brahma_ontology / brahma_remedy_corpus / classical_text_chunks / bodha_msr_signals(yoga family) → `reachable-surgical` → wire_reachable=TRUE
  - kala_* / bodha_convergence / bodha_cgm / bodha_rm_* / phala_* / mimamsa_* / bg_nakshatra_medical → `served-only-by-down-pipeline` → FALSE
  - reference_* / bg_medical_mappings / bg_transit_* / yoga_families → `truly-unreachable` → FALSE
- held_in_db spot-checked via read-only mcp__postgres__query against chart_facts (fact_subject IN LAGNA/HOUSE_1/special-lagnas), chart_dashas (system_id), bodha_msr_signals.

## Key DB confirmations (Lagna entity, chart 482012f1)
- LAGNA subject held: graha_position(25), graha_sign_attributes(10), graha_nakshatra_join(70), graha_pada_join(20), graha_kp_lords(20), nakshatra_dispositor(20)+chain(5), nakshatra_pada_sensitive(20), graha_gandanta(5), graha_tara_bala(15), nakshatra_cross_ayanamsha(1)
- special_lagna: **245 rows** (BHAVA/HORA/GHATI/VARNADA/SREE/INDU/VIGHATI + pranapada) — B-VIII.60 fully held
- HOUSE_1 (lagna-bhava): bhava_bala_* (7 subscores), house_bhava_bala_total/subscore, house_strength_classification_rollup, aspect_parashari_received(15), aspect_matrix_summary
- midpoint ASC-* (180), esoteric_point_sri_yantra=SRI_YANTRA_LAGNA, bhava_arudha(210 incl AL/A1), yoga_label(34), dosha_label(110), saham_position(2800), eclipse_proximity_natal, kp_cuspal_significators, kp_ruling_planets_natal
- chart_dashas systems: vimshottari, vimshottari_kp, ashtottari, yogini, kalachakra, chara_karaka(155135 — Jaimini/rashi, seeded from lagna), naisargika, mudda(tajaka annual) — all reachable-surgical
- bodha_msr_signals referencing lagna/ascendant: 258 (of 66,836)

## Per-facet retrievability matrix

| # | facet_group | held | wire | usable | channel / note |
|---|---|---|---|---|---|
| 1 | B-I Positional | T | T | T | chart_facts graha_position(LAGNA) reachable-surgical |
| 2 | B-I Positional | T | T | T | lagna≡H1 cusp; chalit via cusp_kp_lords/bhava-madhya |
| 3 | B-I Positional | T | T | T | near_sign_boundary_flag + bhava madhya; cusp dual-flavor |
| 4 | B-I Positional | T | T | T | graha_nakshatra_join/pada_join/graha_kp_lords(LAGNA) |
| 5 | B-I Positional | T | T | T | graha_tara_bala(LAGNA) = navatara from Moon & Lagna |
| 6 | B-I Positional | F | – | F | N/A — ascendant point: no declination/rise-set/oriental facet stored |
| 7 | B-I Positional | F | – | F | N/A — lagna has no speed/retrograde geometry |
| 8 | B-I Positional | F | – | F | N/A — no ayana/gola for the ascendant point |
| 9 | B-II Dignity | F | – | F | N/A — lagna point has no exalt/debil dignity |
| 10 | B-II Dignity | F | – | F | N/A — mulatrikona/panchadha is a graha property |
| 11 | B-II Dignity | F | – | F | N/A — neecha-bhanga is graha-only |
| 12 | B-II Dignity | T | T | T | vargottama_per_varga + vargottama_flag_at_point |
| 13 | B-II Dignity | F | – | F | mrityu-bhaga computed nowhere per point (R-47 nonexistence) |
| 14 | B-II Dignity | T | T | T | panchanga_tithi_shoonya_rashi (sign-level, lagna sign) |
| 15 | B-II Dignity | T | T | T | graha_sign_attributes(LAGNA) sign-type flavor |
| 16 | B-III Strength | F | – | F | N/A — no shadbala for ascendant point |
| 17 | B-III Strength | F | – | F | N/A — ishta/kashta is graha-only |
| 18 | B-III Strength | F | – | F | N/A — vimsopaka is graha-only |
| 19 | B-III Strength | T | T | T | house_bhava_bala_total/subscore(HOUSE_1) = lagna-bhava bala |
| 20 | B-III Strength | F | – | F | N/A — pancha-vargiya bala graha-only |
| 21 | B-III Strength | T | T | T | ashtakavarga_pinda_sarva of lagna sign (occupied-sign SAV) |
| 22 | B-III Strength | F | – | F | N/A — saptavargaja dignity tally graha-only |
| 23 | B-IV State | F | – | F | N/A — lagna no combustion/graha-yuddha |
| 24 | B-IV State | F | – | F | N/A — grahan yuti graha-only |
| 25 | B-IV State | F | – | F | N/A — avastha sets are graha-only |
| 26 | B-IV State | T | T | T | graha_gandanta(LAGNA) |
| 27 | B-IV State | F | – | F | no lagna-upagraha contact facet computed |
| 28 | B-IV State | T | T | T | saham_position (sahams reckoned from lagna) |
| 29 | B-V Relational | T | T | T | aspect_parashari_received(HOUSE_1); lagna casts none |
| 30 | B-V Relational | T | T | T | aspect_jaimini rashi drishti of lagna sign |
| 31 | B-V Relational | F | – | F | N/A — sambandha is graha-pair classification |
| 32 | B-V Relational | T | T | T | nakshatra_dispositor(_chain)(LAGNA) + sign dispositor=lagnesha |
| 33 | B-V Relational | F | – | F | no explicit papa/shubha-kartari facet on H1 |
| 34 | B-V Relational | T | T | T | argala_natal_matrix (HOUSE_1 rows) |
| 35 | B-V Relational | F | – | F | SBC/nakshatra-vedha/latta = transit engine (not stored natal) |
| 36 | B-V Relational | T | T | T | graha_tara_bala(LAGNA) |
| 37 | B-VI Functional | T | T | T | graha_functional_class_per_ascendant + yoga_karaka_flag |
| 38 | B-VI Functional | T | T | T | badhaka/maraka derivable from functional class + dosha_label |
| 39 | B-VI Functional | F | – | F | N/A — karaka roles are graha-only (lagna not a karaka) |
| 40 | B-VI Functional | T | T | T | bhava_arudha (Arudha Lagna A1) |
| 41 | B-VI Functional | T | T | T | yoga_label + bodha_msr_signals(yoga, reachable-surgical) |
| 42 | B-VI Functional | T | T | T | dosha_label |
| 43 | B-VI Functional | F | – | F | 22nd-drekkana/64th-navamsa lord not itemized as a facet |
| 44 | B-VII Temporal | F | – | F | N/A — lagna is not a vimshottari dasha lord |
| 45 | B-VII Temporal | F | – | F | N/A — dasha-quality "from this graha" undefined for lagna |
| 46 | B-VII Temporal | T | T | T | chart_dashas chara_karaka/kalachakra/ashtottari/yogini (rashi dashas from lagna) reachable-surgical |
| 47 | B-VII Temporal | F | – | F | transit-now is dynamic, not a stored natal Lagna fact |
| 48 | B-VII Temporal | F | – | F | N/A — sade-sati is Saturn/Moon, not a Lagna facet |
| 49 | B-VII Temporal | F | – | F | double-transit = transit engine (not stored) |
| 50 | B-VII Temporal | T | T | T | tajik_hadda_lord/triraashipathi + mudda dasha (varshaphal) |
| 51 | B-VII Temporal | T | T | T | eclipse_proximity_natal on lagna degree |
| 52 | B-VII Temporal | **T** | **F** | **F** | **HELD-BUT-NOT-RECEIVED** — R-45 convergence asset: kala_convergence/bodha_convergence = served-only-by-down-pipeline |
| 53 | B-VIII Esoteric | T | T | T | kp_cuspal_significators + kp_ruling_planets_natal |
| 54 | B-VIII Esoteric | T | T | T | bhrigu_nadi_point / esoteric_point_bhrigu_bindu |
| 55 | B-VIII Esoteric | T | T | T | nakshatra reachable → deity derivable at canon level |
| 56 | B-VIII Esoteric | **T** | **F** | **F** | **HELD-BUT-NOT-RECEIVED** — chart-specific remedial priority: bodha_rm_remedy_prescriptions served-only / rm_chart_summary+rm_dasha_windowed truly-unreachable |
| 57 | B-VIII Esoteric | **T** | **F** | **F** | **HELD-BUT-NOT-RECEIVED** — medical: bg_medical_mappings truly-unreachable, bg_nakshatra_medical served-only |
| 58 | B-VIII Esoteric | T | T | T | graha_sign_attributes(LAGNA) varna/guna/tattva/etc |
| 59 | B-VIII Esoteric | F | – | F | N/A — nodal agency rules are graha-only |
| 60 | B-VIII Esoteric | T | T | T | special_lagna (245 rows) — bhava/hora/ghati/varnada/sree/indu + pranapada |
| 61 | DISC panchanga | T | T | T | panchanga_* (24 categories) chart_facts reachable-surgical |
| 62 | DISC lal-kitab | T | T | T | lal_kitab_special_point |
| 63 | DISC maharishi | T | T | T | maharsi_specific_point |
| 64 | DISC composite | T | T | T | chart_center_of_gravity/cluster/graha_centrality/composite_* rollups |
| 65 | DISC contradiction/conv | T | T | T | contradiction_pair + convergence_count IN chart_facts (reachable — cf. 52) |
| 66 | DISC karaka-concordance | T | T | T | karaka_bhava_concordance/overlap/karakatva_strength |
| 67 | DISC midpoint | T | T | T | midpoint (ASC-* 180 rows) |
| 68 | DISC nakshatra-stats | T | T | T | nakshatra_cogravity/co_tenancy/cross_ayanamsha/statistics |
| 69 | DISC swamsa | T | T | T | swamsa_position |
| 70 | DISC tajik-sublords | T | T | T | tajik_hadda_lord/triraashipathi/vargottama_specific |
| 71 | DISC esoteric web | T | T | T | esoteric_point_* (avayogi/brahma/mrityu/pranapada/shiva/…/sri_yantra_lagna) |
| 72 | DISC pranic | T | T | T | pranic_strength_per_graha (chart-level) |
| 73 | DISC tri-deva | T | T | T | graha_tri_deva_role_strength + jaimini_tri_deva_role |
| 74 | DISC shani-periods | T | T | T | anumukha/ardha_ashtama/ashtama/janma/kantaka/vishakha shani periods |
| 75 | DISC saturn/sun-points | T | T | T | saturn_derived_point + sun_derived_upagraha |

## Rollup
- facets_total: **75**
- held_in_db: **48** (27 held=FALSE are graha-battery facets inapplicable to the ascendant point — nonexistence-by-design, not defects: strength/avastha/combustion/dignity/karaka/dasha-lordship of a non-graha point; incl. mrityu-bhaga R-47 nonexistence)
- wire_reachable (channel==reachable-surgical): **45**
- reachable_in_2_calls: **45** (all reachable facets resolve in a single chart_facts / chart_dashas / bodha_msr_signals surgical query)
- usable_form (held ∧ reachable ∧ §7.1 pass): **45**
- held_but_not_received: **3** (facets 52, 56, 57)
- dossier_completeness_pct (usable/total): 45/75 = **60.0%**  ·  applicable-adjusted (usable / held-applicable 48): **93.8%**
- dossier_verdict: **PARTIAL** — the Lagna core (positional, nakshatra/KP, functional-class, arudha, yoga/dosha, special-lagna×245, bhava-bala, esoteric web, dashas-from-lagna) is fully composable at acharya depth; three material supplementary layers are held-but-not-received.

## Findings (held-but-not-received → §4 class 1 UNREACHABLE, per matrix channel)

**L8-Lagna-F1 — Structural×temporal convergence (R-45 asset) unreachable.**
Facet F01030 (#52). held_in_db=TRUE (kala_convergence / bodha_convergence populated; kala_activation ripeness). wire_reachable=FALSE. Class 1 UNREACHABLE, subclass **served-only-by-down-pipeline**. Suspected layer: MCP contract / serving-query. Evidence: CONCEPT_RETRIEVABILITY_MATRIX — every kala_convergence & bodha_convergence family_key = "served-only-by-down-pipeline"; raw convergence_count IS reachable via chart_facts (facet #65) but the temporally-ripe "which of the lagna's promises are ripe, recent-past/near-future" asset is not exposed. Dedupe: **matches anchor R-45** (kala_activation first-contact failure) — re-confirmed independently via Lane 8 depth pass, not a new register row.

**L8-Lagna-F2 — Chart-specific remedial prioritization unreachable.**
Facet F01110 (#56). held_in_db=TRUE (bodha_rm_remedy_prescriptions / rm_dosha_remedy_bundles / rm_dasha_windowed_prescriptions). wire_reachable=FALSE. Class 1 UNREACHABLE (rm_remedy_prescriptions=served-only-by-down-pipeline; rm_chart_summary & rm_dasha_windowed_prescriptions=truly-unreachable). Suspected layer: serving-query / MCP contract. Evidence: matrix bodha_rm_* channels. The generic brahma_remedy_corpus IS reachable-surgical, so an LLM gets textbook remedies but NOT the chart-specific "does served remedial priority reflect the lagna/lagnesha's actual afflictions" (the facet's own test) — the afflicton-weighted prioritization is down-pipeline-only.

**L8-Lagna-F3 — Medical significations (avayava/dhatu/dosha) unreachable.**
Facet F01130 (#57). held_in_db=TRUE (bg_medical_mappings, bg_nakshatra_medical L0 catalogs). wire_reachable=FALSE. Class 1 UNREACHABLE (bg_medical_mappings=truly-unreachable; bg_nakshatra_medical=served-only-by-down-pipeline). Suspected layer: MCP contract (no tool fronts the L0 medical catalogs). Evidence: matrix bg_medical_mappings/bg_nakshatra_medical channels.

## Class-9 (UNGOVERNED JUDGMENT) note
The applicability partition (which of the graha-oriented Appendix-B floor rows are inapplicable to the ascendant point vs. genuine gaps) was an executor judgment the system does not govern — the facet floor is graha-shaped and provides no per-entity applicability map for the Lagna dossier. Logged as a class-9 candidate (taxonomy→entity-shape translation). Non-blocking; the 27 inapplicable rows are marked held=FALSE by-design-nonexistence, not counted as held-but-not-received.

## Secondary observation (INCONSISTENT surface, class 3 candidate — not a primary finding)
Convergence is split across a reachable raw counter (chart_facts.convergence_count, facet #65 — reachable-surgical) and an unreachable rich asset (kala/bodha_convergence, facet #52 — served-only). A consuming LLM receives the tally but not the substance; the two surfaces describe the same quantity at incompatible fidelity. Noted for Lane 6/Lane 1a cross-reference; primary defect logged as F1 (class 1).
