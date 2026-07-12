# Lane 8 shard trace — Saturn dossier, chart 1c826d5a (last4 f75a)

- dossier_id: Saturn_1c826d5a
- entity: Saturn
- chart_id: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
- facets_total: 75 (60 Appendix-B floor + 15 discovered F61–F75)
- resume_after_row_id: F01497 (shard fully graded)
- status: done

## Method
- Facet list from `ledgers/facets.jsonl` (entity=="Saturn", chart 1c826d5a), 75 rows.
- SHAPER #3: wire_reachable read from `CONCEPT_RETRIEVABILITY_MATRIX.jsonl` channel per backing table.
  `reachable-surgical` → wire_reachable=TRUE; `served-only-by-down-pipeline` / `truly-unreachable` → FALSE.
- held_in_db confirmed by read-only `mcp__postgres__query` spot-checks against chart_facts / chart_divisionals /
  chart_dashas / bodha_msr_signals for chart 1c826d5a.
- Rubric: Charter §7.1 (RATIFIED, gate v1.1) for usable_form.

## DB ground-truth (spot-checks)
- chart_facts holds Saturn's full battery, keyed by `fact_subject` (e.g. `SAT-HOUSE_n`) / `fact_key` / jsonb — 200+ fact_categories present incl. graha_position, graha_shadbala_* (sthana/dig/kala/cheshta/naisargika/drik/total), graha_dignity_per_varga, all 5 avastha sets, ashtakavarga_bindu/pinda_*, aspect_parashari/jaimini/tajik, dispositor_tree/graha_dispositor_chain, graha_kp_lords/kp_cuspal_significators, graha_gandanta, karaka_chara_position/karakamsa, yoga_label, dosha_label, sade_sati_* (9 categories) + 6 shani-period categories, esoteric_point_* (12), tajik_*, panchanga_* (30+), swamsa/midpoint/pranic/tri_deva, chart-level composites.
- chart_divisionals: graha='Saturn' present (varga placements + vargottama). channel reachable-surgical.
- chart_dashas systems present: vimshottari, vimshottari_kp, ashtottari, yogini, kalachakra, chara_karaka, mudda, naisargika — with lord_natal_house/dignity/shadbala context. channel reachable-surgical.
- bodha_msr_signals: 5226 Saturn-referencing signals. channel reachable-surgical.
- ABSENT categories (nonexistence): no mrityu_bhaga, no pushkar*, no neecha_* (as category), no transit/gochara natal category, no declination/kranti category. (esoteric_point_mrityu is mrityu-sphuta, NOT mrityu-bhaga.)

## Per-facet matrix

| row_id | # | facet_group | facet_text (abbr) | held | wire | usable | channel / backing |
|---|---|---|---|---|---|---|---|
| F00017 | 1 | B-I | Sign, dms, bhoga | T | T | T | surgical / chart_facts graha_position |
| F00037 | 2 | B-I | House WS + chalit | T | T | T | surgical / graha_position, cusp_kp_lords |
| F00057 | 3 | B-I | Bhava madhya / sandhi / cusp | T | T | T | surgical / near_*_boundary_flag, cusp_kp_lords |
| F00077 | 4 | B-I | Nakshatra/pada/lord; KP star/sub | T | T | T | surgical / graha_nakshatra_join, graha_pada_join, graha_kp_lords |
| F00097 | 5 | B-I | Navatara from Moon AND Lagna | T | T | T | surgical / graha_tara_bala, tara_bala |
| F00117 | 6 | B-I | Declination/latitude/rise-set/orient | F | F | F | NONEXISTENCE — no kranti/shara/udaya-asta category |
| F00137 | 7 | B-I | Speed/retro/stationary geometry | T | T | T | surgical / graha_position, graha_cheshta_bala |
| F00157 | 8 | B-I | Ayana / gola | F | F | F | NONEXISTENCE — graha ayana/gola not computed |
| F00177 | 9 | B-II | Exalt/debil deep-degree | T | T | T | surgical / graha_dignity_per_varga |
| F00197 | 10 | B-II | Mulatrikona/own/panchadha | T | T | T | surgical / graha_dignity_per_varga, graha_effective_dignity |
| F00217 | 11 | B-II | Neecha-bhanga enumeration | T | T | T | surgical / graha_effective_dignity_modified_by_aspects (enumeration-with-evidence partial) |
| F00237 | 12 | B-II | Vargottama; pushkara | T | T | T | surgical / vargottama_per_varga, graha_vargottama (pushkara sub-gap: not computed) |
| F00257 | 13 | B-II | Mrityu-bhaga; yogatara | F | F | F | NONEXISTENCE — R-47 anchor (computed nowhere per graha) |
| F00277 | 14 | B-II | Dagdha/tithi-shunya/mrityu-rashi | T | T | T | surgical / panchanga_tithi_shoonya_rashi, panchanga_nakshatra_shoonya_rashi |
| F00297 | 15 | B-II | Sign-type flavor | T | T | T | surgical / graha_sign_attributes |
| F00317 | 16 | B-III | Shadbala full tree | T | T | T | surgical / graha_shadbala_* (all 6 + total) |
| F00337 | 17 | B-III | Ishta/Kashta phala | T | T | T | surgical / graha_ishta_phala, graha_kashta_phala |
| F00357 | 18 | B-III | Vimsopaka ladder | T | T | T | surgical / graha_vimsopaka_* (shad/sapta/dasa/shodasa) |
| F00377 | 19 | B-III | Bhava bala owned/occupied | T | T | T | surgical / bhava_bala_*, house_bhava_bala_* |
| F00397 | 20 | B-III | Pancha/dwadash-vargiya | T | T | T | surgical / graha_saptavargaja_bala_component, vimsopaka |
| F00417 | 21 | B-III | Ashtakavarga full | T | T | T | surgical / ashtakavarga_bindu, ashtakavarga_pinda_* |
| F00437 | 22 | B-III | Sapta-vargaja dignity tally | T | T | T | surgical / graha_saptavargaja_bala_component, graha_dignity_per_varga |
| F00457 | 23 | B-IV | Combustion / graha-yuddha | T | T | T | surgical / combustion_relationship, graha_yuddha |
| F00477 | 24 | B-IV | Grahan yuti | T | T | T | surgical / eclipse_proximity_natal, combustion |
| F00497 | 25 | B-IV | Avastha all 5 sets | T | T | T | surgical / graha_avastha_* (baladi/jagrad/deepta/lajjitadi/sayanadi) |
| F00517 | 26 | B-IV | Gandanta proximity | T | T | T | surgical / graha_gandanta |
| F00537 | 27 | B-IV | Upagraha contact | T | T | T | surgical / upagraha_position, sensitive_point_gulika_mandi, sun_derived_upagraha |
| F00557 | 28 | B-IV | Saham contacts | T | T | T | surgical / saham_position |
| F00577 | 29 | B-V | Conjunctions/aspects sputa | T | T | T | surgical / conjunction_within_orb, aspect_parashari_*, virupa_drishti |
| F00597 | 30 | B-V | Rashi drishti (Jaimini) | T | T | T | surgical / aspect_jaimini |
| F00617 | 31 | B-V | Sambandha classification | T | T | T | surgical / sambandha_grade |
| F00637 | 32 | B-V | Dispositor web | T | T | T | surgical / graha_dispositor_chain, dispositor_tree, nakshatra_dispositor_chain |
| F00657 | 33 | B-V | Papa/shubha kartari | T | T | T | surgical / conjunction/aspect derived, yoga_label |
| F00677 | 34 | B-V | Argala | T | T | T | surgical / argala_natal_matrix, net_argala_per_varga, virodha_argala |
| F00697 | 35 | B-V | Vedha (SBC/nakshatra/latta) | F | F | F | NONEXISTENCE — Sarvatobhadra/latta natal vedha not computed (bg_transit_vedha is transit-only, truly-unreachable) |
| F00717 | 36 | B-V | Tara bala from Moon | T | T | T | surgical / graha_tara_bala, tara_bala |
| F00737 | 37 | B-VI | Lordships + functional class | T | T | T | surgical / graha_functional_class_per_ascendant |
| F00757 | 38 | B-VI | Kendradhipati/badhaka/maraka | T | T | T | surgical / graha_functional_class, bhava_significance_link |
| F00777 | 39 | B-VI | Karaka portfolio (naisargika+chara) | T | T | T | surgical / karaka_chara_position, karaka_web_per_varga, karakamsa_position |
| F00797 | 40 | B-VI | Arudha involvement | T | T | T | surgical / arudha_pada, bhava_arudha |
| F00817 | 41 | B-VI | Yoga participation all families | T | T | T | surgical / yoga_label + bodha_msr_signals (5226 Saturn signals) |
| F00837 | 42 | B-VI | Dosha participation | T | T | T | surgical / dosha_label + msr |
| F00857 | 43 | B-VI | 22nd drekkana / 64th navamsha | T | T | T | surgical / chart_divisionals (D3/D9 lords derivable ≤2 calls) |
| F00877 | 44 | B-VII | Vimshottari now + windows | T | T | T | surgical / chart_dashas (level_n, start/end, sandhi) |
| F00897 | 45 | B-VII | Dasha-quality context | T | T | T | surgical / chart_dashas (lord_natal_house/dignity/shadbala) |
| F00917 | 46 | B-VII | Other dasha systems | T | T | T | surgical / chart_dashas (yogini/ashtottari/kalachakra/chara/mudda/naisargika) |
| F00937 | 47 | B-VII | Transit now | T | F | F | HELD-NOT-RECEIVED — bg_transit_engine truly-unreachable (class 1) |
| F00957 | 48 | B-VII | Sade-sati / dhaiya | T | T | T | surgical / sade_sati_* (9 cat) + dhaiya_period + 6 shani-period cat |
| F00977 | 49 | B-VII | Double-transit (Sa+Ju) | T | F | F | HELD-NOT-RECEIVED — bg_transit_engine truly-unreachable (class 1) |
| F00997 | 50 | B-VII | Varshaphal / tajik | T | T | T | surgical / aspect_tajik, tajik_*, chart_dashas mudda/varsha |
| F01017 | 51 | B-VII | Eclipses/stations on natal deg | T | T | T | surgical / eclipse_proximity_natal (natal; future stations partial) |
| F01037 | 52 | B-VII | Structural×temporal convergence | T | F | F | HELD-NOT-RECEIVED — kala_convergence/kala_activation served-only-by-down-pipeline (R-45 anchor, class 1) |
| F01057 | 53 | B-VIII | KP significator ladder | T | T | T | surgical / kp_cuspal_significators, significator_path, kp_ruling_planets_natal |
| F01077 | 54 | B-VIII | Nadi roles / bhrigu-bindu | T | T | T | surgical / bhrigu_nadi_point, esoteric_point_bhrigu_bindu |
| F01097 | 55 | B-VIII | Deity web | T | F | F | HELD-NOT-RECEIVED — reference_nakshatra truly-unreachable (class 1) |
| F01117 | 56 | B-VIII | Remedial mapping + priority-vs-affliction | T | T | F | HELD-NOT-RECEIVED — generic via brahma_remedy_corpus (surgical) but chart-specific affliction-priority via bodha_rm_* served-only (class 1; usable_form fails Charter §7.1 referential-resolvability for the discriminating part) |
| F01137 | 57 | B-VIII | Medical (avayava/dhatu/dosha) | T | F | F | HELD-NOT-RECEIVED — bg_medical_mappings truly-unreachable / bg_nakshatra_medical served-only (class 1) |
| F01157 | 58 | B-VIII | Sambandha table (varna/guna/tattva…) | T | F | F | HELD-NOT-RECEIVED — reference_planets truly-unreachable (class 1) |
| F01177 | 59 | B-VIII | Nodal axis relations | T | T | T | surgical / nakshatra_dispositor, dispositor_tree (agency doctrine partial) |
| F01197 | 60 | B-VIII | Special-lagna relations | T | T | T | surgical / special_lagna |
| F01217 | 61 | DISC | Panchanga/muhurta catalog | T | T | T | surgical / panchanga_* (30+ categories) |
| F01237 | 62 | DISC | Lal Kitab special-point | T | T | T | surgical / lal_kitab_special_point |
| F01257 | 63 | DISC | Maharishi-specific point | T | T | T | surgical / maharsi_specific_point |
| F01277 | 64 | DISC | Chart-level analytics | T | T | T | surgical / chart_center_of_gravity, chart_cluster, graha_centrality, composite_* |
| F01297 | 65 | DISC | Contradiction/convergence meta | T | T | T | surgical / contradiction_pair, convergence_count |
| F01317 | 66 | DISC | Karaka-bhava concordance | T | T | T | surgical / karaka_bhava_concordance, karaka_house_lord_overlap_flag, karakatva_strength |
| F01337 | 67 | DISC | Midpoint (Western) | T | T | T | surgical / midpoint |
| F01357 | 68 | DISC | Nakshatra co-gravity/stats | T | T | T | surgical / nakshatra_cogravity, co_tenancy, cross_ayanamsha, statistics |
| F01377 | 69 | DISC | Swamsa position | T | T | T | surgical / swamsa_position |
| F01397 | 70 | DISC | Tajika hadda/triraashipathi/vargottama | T | T | T | surgical / tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific |
| F01417 | 71 | DISC | Esoteric sensitive-point web | T | T | T | surgical / esoteric_point_* (avayogi/brahma/mrityu/pranapada/shiva/… 12) |
| F01437 | 72 | DISC | Pranic strength system | T | T | T | surgical / pranic_strength_per_graha |
| F01457 | 73 | DISC | Tri-deva role strength (Jaimini) | T | T | T | surgical / graha_tri_deva_role_strength, jaimini_tri_deva_role_per_graha |
| F01477 | 74 | DISC | Shani special-period catalog | T | T | T | surgical / anumukha/ardha_ashtama/ashtama/janma/kantaka/vishakha_shani_period |
| F01497 | 75 | DISC | Saturn/Sun-derived special points | T | T | T | surgical / saturn_derived_point, sun_derived_upagraha |

## Dossier rollup
- facets_total: 75
- held_in_db: 71 (not held: F6, F8, F13, F35 — 4 nonexistence)
- wire_reachable: 65
- reachable_in_2_calls: 65
- usable_form: 64
- held_but_not_received (held T, wire F or usable F): 7 → F47, F49, F52, F55, F56, F57, F58
- dossier_completeness_pct: 64/75 = 85.3%
- dossier_verdict: **PARTIAL**

Rationale: the deterministic natal core of Saturn's dossier — position, full shadbala tree, all five avastha
sets, ashtakavarga, dignity/vargottama, dispositor web, argala, karaka portfolio, yoga/dosha membership (5226
MSR signals), all eight dasha systems with time-lord context, sade-sati + six shani-period sub-types, KP
significators, esoteric-point web, and the 15 discovered composite/tajika/shani families — is fully composable
surgically at acharya depth. But seven facets are held-but-not-received (the entire temporal-convergence /
R-45 ripeness layer, live transit + double-transit, chart-specific remedial-priority, medical, deity, and
graha sambandha attributes), and four classical facets (declination, ayana/gola, mrityu-bhaga [R-47], natal
Sarvatobhadra/latta vedha) are absent by nonexistence. Material gaps, not fatal → PARTIAL.

## Findings (all class 1 UNREACHABLE)

### Held-but-not-received (held in DB, not received over the wire)
- **F-Sat-01 (F01037, convergence, HIGH)** — Saturn's structural×temporal convergence / ripeness (which of
  its yogas/promises are temporally ripe, R-45 asset) is held in `kala_convergence` / `kala_activation` but
  channel = `served-only-by-down-pipeline`: a consuming LLM cannot surgically pull Saturn's convergence rows;
  they surface only inside a downstream pipeline product. Class 1. Rediscovers R-45 anchor. Suspected layer:
  MCP contract / serving-query.
- **F-Sat-02 (F00937, transit-now, MED)** — current gochara of/on Saturn (sign/house from natal Moon & Lagna,
  vedha, murthi) served only by `bg_transit_engine`, channel = `truly-unreachable`. Class 1. Suspected layer:
  MCP contract (no tool fronts the transit engine).
- **F-Sat-03 (F00977, double-transit, MED)** — Saturn+Jupiter double-transit participation on natal points:
  `bg_transit_engine` truly-unreachable. Class 1.
- **F-Sat-04 (F01117, remedial-priority, MED)** — generic Saturn remedies reachable via `brahma_remedy_corpus`,
  but the discriminating facet ("whether served remedial priority reflects its actual afflictions") lives in
  `bodha_rm_remedy_prescriptions` / `bodha_rm_dasha_windowed_prescriptions`, channel served-only /
  truly-unreachable → usable_form fails Charter §7.1 (referential resolvability of the chart-specific part).
  Class 1.
- **F-Sat-05 (F01137, medical, MED)** — Saturn's avayava/dhatu/dosha + disease significations from its
  afflictions held in `bg_medical_mappings` (truly-unreachable) / `bg_nakshatra_medical` (served-only). Class 1.
- **F-Sat-06 (F01097, deity-web, LOW)** — nakshatra deity / adhidevata / pratyadhidevata held in
  `reference_nakshatra`, channel truly-unreachable. Class 1.
- **F-Sat-07 (F01157, sambandha-attributes, LOW)** — Saturn's varna/guna/tattva/gender/direction/metal/grain
  table held in `reference_planets`, channel truly-unreachable. Class 1.

### Nonexistence (not held; UNREACHABLE-by-nonexistence)
- **F-Sat-08 (F00257, mrityu-bhaga, MED)** — mrityu-bhaga per-sign degree check + yogatara proximity computed
  nowhere per graha. Rediscovers R-47 anchor. Class 1 (data-plane gap).
- **F-Sat-09 (F00117, F00157, coordinate, LOW)** — declination/kranti, celestial latitude/shara, rise-set
  (udaya/asta) state, oriental/occidental, and ayana/gola of the graha not computed. Class 1 (data-plane gap).
- **F-Sat-10 (F00697, natal-vedha, LOW)** — Sarvatobhadra-chakra vedha / nakshatra-vedha pairs / latta on
  Saturn's nakshatra not computed as a natal facet (only transit vedha exists, itself truly-unreachable).
  Class 1 (data-plane gap).
