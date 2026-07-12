# Lane 8 shard — Mercury dossier, chart 482012f1 (last4 71aa)

- dossier_id: `Mercury_482012f1`
- entity: Mercury · chart_id: `482012f1-710e-4a25-994a-93821f5871aa`
- facets graded: 75 (60 Appendix-B floor + 15 discovered) — ledger rows F00004..F01484
- resume_after_row_id: F01484 (shard complete)
- rubric basis: Charter §7.1 (RATIFIED v1.1, GATE_RATIFICATION_v1_0.md) — no provisional flag needed
- SHAPER #3: channels consumed from CONCEPT_RETRIEVABILITY_MATRIX.jsonl (not re-probed).
  Established channels: chart_facts / chart_divisionals / chart_dashas = **reachable-surgical**;
  bodha_cgm_* / bodha_convergence / kala_* / kala_convergence / bodha_discoveries / phala_* /
  mimamsa_* / bodha_msr_signals(83/115) = **served-only-by-down-pipeline**;
  bg_medical_mappings / reference_* / reference_planets = **truly-unreachable**.

## Grading key
- held_in_db T = DB confirmed holds this facet for Mercury on 71aa (spot-checked chart_facts by
  fact_subject IN (MER/MERCURY/MER-*), plus chart_divisionals/chart_dashas/bodha_* counts).
- wire_reachable = (backing channel == reachable-surgical).
- usable_form = held AND wire_reachable AND composable in-context (Charter §7.1). Down-pipeline &
  truly-unreachable held facets → held-but-not-received (usable F).
- held F where the facet is computed **nowhere** for Mercury = UNREACHABLE-by-nonexistence
  (data-plane gap, §2.1) — NOT counted in held_but_not_received, but is a class-1 finding.
- N/A = facet scoped by its own text to another entity (Saturn/Moon) — UNANSWERABLE-BY-DESIGN, no finding.

## Per-facet matrix

| # | group | facet (abbrev) | held | wire | ≤2c | usable | channel / backing |
|---|---|---|---|---|---|---|---|
| 1 | B-I | Sign/dms/bhoga | T | T | T | T | chart_facts graha_position (surgical) |
| 2 | B-I | House WS + bhava-chalit divergence | T | T | T | T | chart_facts house_d1 (chalit not computed — note) |
| 3 | B-I | Bhava madhya/sandhi/cusp | T | T | T | T | chart_facts near_sign/nak_boundary_flag |
| 4 | B-I | Nakshatra/pada/lord/KP | T | T | T | T | graha_nakshatra_join, graha_pada_join, graha_kp_lords |
| 5 | B-I | Navatara from Moon+Lagna | T | T | T | T | graha_tara_bala / tara_bala |
| 6 | B-I | Declination/latitude/rise-set/oriental | F | F | F | F | NONEXISTENCE — not in graha_position |
| 7 | B-I | Speed/stationary/retro geometry | T | T | T | T | retrograde_flag + graha_cheshta_bala (speed-value gap note) |
| 8 | B-I | Ayana/gola per-graha | F | F | F | F | NONEXISTENCE — chart-level only, not per-graha |
| 9 | B-II | Exalt/debil + deep-degree | T | T | T | T | graha_effective_dignity_modified_by_aspects |
| 10 | B-II | Mulatrikona/own/panchadha | T | T | T | T | chart_facts dignity families |
| 11 | B-II | Neecha-bhanga enumeration | F | F | F | F | NONEXISTENCE — no neecha_bhanga category |
| 12 | B-II | Vargottama/pushkara | T | T | T | T | vargottama_per_varga (pushkara absent — note) |
| 13 | B-II | **Mrityu bhaga** (per-sign degree) | F | F | F | F | NONEXISTENCE — **R-47 anchor** (computed nowhere per graha) |
| 14 | B-II | Dagdha/tithi-shunya/mrityu rashi | F | F | F | F | NONEXISTENCE |
| 15 | B-II | Sign-type flavor (chara/tattva) | T | T | T | T | graha_sign_attributes |
| 16 | B-III | Shadbala full tree | T | T | T | T | graha_shadbala_* (all 6 + total) |
| 17 | B-III | Ishta/Kashta phala | T | T | T | T | graha_ishta_phala, graha_kashta_phala |
| 18 | B-III | Vimsopaka + vaiseshikamsha | T | T | T | T | graha_vimsopaka_* (4 tiers) |
| 19 | B-III | Bhava bala owned/occupied | T | T | T | T | bhava_bala_lord, graha_in_house_composite_strength |
| 20 | B-III | Pancha-vargiya bala (Tajaka) | F | F | F | F | NONEXISTENCE — saptavargaja held, panchavargiya not |
| 21 | B-III | Ashtakavarga full | T | T | T | T | ashtakavarga_bindu/_per_varga/_pinda_* |
| 22 | B-III | Sapta-vargaja dignity tally | T | T | T | T | graha_saptavargaja_bala_component |
| 23 | B-IV | Combustion + graha yuddha | T | T | T | T | graha_position combustion_state (yuddha partial) |
| 24 | B-IV | Grahan yuti (eclipse assoc) | F | F | F | F | NONEXISTENCE |
| 25 | B-IV | Avastha ALL FIVE | T | T | T | T | baladi/jagradadi/deeptaadi/lajjitadi/sayanadi all held |
| 26 | B-IV | Gandanta proximity | T | T | T | T | graha_gandanta |
| 27 | B-IV | Upagraha contact | T | T | T | T | upagraha_position (contact derivable in-context) |
| 28 | B-IV | Saham contacts (Tajaka) | F | F | F | F | NONEXISTENCE |
| 29 | B-V | Conjunctions + parashari aspects | T | T | T | T | aspect_parashari_given/received |
| 30 | B-V | Rashi drishti (Jaimini) | F | F | F | F | NONEXISTENCE — no rashi_drishti category |
| 31 | B-V | Sambandha classification | F | F | F | F | NONEXISTENCE — derivable, not stored |
| 32 | B-V | Dispositor web + terminus | T | T | T | T | graha_dispositor_chain, nakshatra_dispositor_chain |
| 33 | B-V | Papa/shubha kartari | F | F | F | F | NONEXISTENCE |
| 34 | B-V | Argala given/received | F | F | F | F | NONEXISTENCE |
| 35 | B-V | Vedha (SBC/latta) | F | F | F | F | NONEXISTENCE |
| 36 | B-V | Tara bala from Moon | T | T | T | T | graha_tara_bala / tara_bala |
| 37 | B-VI | Lordships + functional class + yogakaraka | T | T | T | T | graha_functional_class_per_ascendant, graha_yoga_karaka_flag, lord_in_house_per_varga |
| 38 | B-VI | Kendradhipati/badhaka/maraka | F | F | F | F | NONEXISTENCE — no badhaka/maraka label |
| 39 | B-VI | Naisargika + chara karaka + karakamsa | T | T | T | T | karaka_chara_position, karakamsa_position, karaka_web_per_varga |
| 40 | B-VI | Arudha involvement | T | T | T | T | arudha_pada, bhava_arudha |
| 41 | B-VI | Yoga participation (every family) | T | T | T | T | yoga_label (surgical) — **DROWNED** in bodha_msr_signals (199 signals, class-7 secondary) |
| 42 | B-VI | Dosha participation | T | T | T | T | dosha_label (surgical) — drowned in 110 dosha signals |
| 43 | B-VI | 22nd drekkana / 64th navamsha | F | F | F | F | NONEXISTENCE — no drekkana_22/navamsha_64/khareshwara |
| 44 | B-VII | Vimshottari lordship now + windows | T | T | T | T | chart_dashas lord_graha, sandhi_with_next_dasha_lord |
| 45 | B-VII | Dasha-quality context | T | T | T | T | chart_dashas lord_natal_dignity_d1/house_d1 |
| 46 | B-VII | Other dasha systems | T | T | T | T | chart_dashas system_id (multi-system) |
| 47 | B-VII | Transit now (gochara/vedha/murthi/AV) | T | **F** | F | **F** | **HBNR** — kala_* served-only-by-down-pipeline |
| 48 | B-VII | Sade-sati/dhaiya | — | — | — | — | N/A (Saturn/Moon dossier scope) — UNANSWERABLE-BY-DESIGN |
| 49 | B-VII | Double-transit (Sa+Ju) on natal | T | **F** | F | **F** | **HBNR** — kala_activation down-pipeline |
| 50 | B-VII | Varshaphal role + tajaka aspects | T | T | T | T | aspect_tajik, chart_dashas varsha_year_lord |
| 51 | B-VII | Eclipses/stations on natal degree | F | F | F | F | NONEXISTENCE |
| 52 | B-VII | **Structural×temporal convergence (R-45)** | T | **F** | F | **F** | **HBNR** — bodha_convergence(30)/kala_convergence(6484) down-pipeline |
| 53 | B-VIII | KP significator ladder | T | T | T | T | graha_kp_lords, cusp_kp_lords |
| 54 | B-VIII | Nadi roles (jeeva/karma, bhrigu-bindu) | F | F | F | F | NONEXISTENCE — nadi jeeva/karma not computed |
| 55 | B-VIII | Deity web (nakshatra deity/adhidevata) | T | **F** | F | **F** | **HBNR** — reference/bg catalog truly-unreachable |
| 56 | B-VIII | Remedial priority vs afflictions | T | **F** | F | **F** | **HBNR** — chart-specific bodha_rm_* down-pipeline (generic brahma_remedy_corpus surgical) |
| 57 | B-VIII | Medical significations | T | **F** | F | **F** | **HBNR** — bg_medical_mappings truly-unreachable |
| 58 | B-VIII | Sambandha table (varna/guna/tattva…) | T | **F** | F | **F** | **HBNR** — reference_planets truly-unreachable (graha_sign_attributes partial) |
| 59 | B-VIII | Nodal axis agency relations | F | F | F | F | NONEXISTENCE — node-agency rules not computed |
| 60 | B-VIII | Special-lagna relations | F | F | F | F | NONEXISTENCE — graha house-from-special-lagna not stored |
| 61 | disc | Panchanga/muhurta window catalog | T | T | T | T | panchanga_* in chart_facts surgical (muhurta windows in phala down-pipeline — note) |
| 62 | disc | Lal Kitab special point | T | T | T | T | lal_kitab_special_point (surgical) |
| 63 | disc | Maharishi-specific point | T | T | T | T | maharsi_specific_point (surgical) |
| 64 | disc | Chart-level composite/rollup analytics | T | T | T | T | composite_dispositor_strength, graha_composite_state_classification, _special_state_rollup |
| 65 | disc | Contradiction-pair / convergence-count | T | T | T | T | contradiction_pair, convergence_count IN chart_facts (surgical) |
| 66 | disc | Karaka-bhava concordance/overlap | T | T | T | T | karaka_bhava_concordance, karaka_house_lord_overlap_flag, karakatva_strength |
| 67 | disc | Midpoint (Western) | T | T | T | T | midpoint (100 rows, surgical) |
| 68 | disc | Nakshatra co-gravity/co-tenancy/stats | T | T | T | T | nakshatra_cogravity/_co_tenancy/_statistics/_cross_ayanamsha |
| 69 | disc | Swamsa position | T | T | T | T | swamsa_position |
| 70 | disc | Tajika hadda/triraashipathi/vargottama | T | T | T | T | tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific |
| 71 | disc | Esoteric sensitive-point web | T | T | T | T | esoteric_point_avayogi/brahma/yogi/pranapada_sphuta/mrityu… |
| 72 | disc | Pranic strength per graha | T | T | T | T | pranic_strength_per_graha |
| 73 | disc | Tri-deva role strength (Jaimini) | T | T | T | T | graha_tri_deva_role_strength, jaimini_tri_deva_role_per_graha |
| 74 | disc | Shani special-period catalog | — | — | — | — | N/A (Saturn-period facet; Mercury out of scope) — UNANSWERABLE-BY-DESIGN |
| 75 | disc | Saturn/Sun-derived special points | T | T | T | T | saturn_derived_point, sun_derived_upagraha (surgical) |

## Dossier rollup

| metric | value |
|---|---|
| facets_total | 75 |
| held_in_db (T) | 54 |
| held F — nonexistence (§2.1 UNREACHABLE-by-nonexistence) | 19 |
| N/A by design (Saturn/Moon scope) | 2 (facets 48, 74) |
| wire_reachable (surgical) | 47 |
| reachable_in_2_calls | 47 |
| usable_form (composable) | 47 |
| held-but-not-received (held T, wire F) | 7 (facets 47, 49, 52, 55, 56, 57, 58) |
| dossier_completeness_pct (usable/total) | 62.7% |
| dossier_verdict | **PARTIAL** |

**Verdict rationale.** Mercury's CORE dossier is rich and fully surgically reachable: position,
dignity, full shadbala tree, ishta/kashta, vimsopaka, ashtakavarga, all five avastha sets,
gandanta, parashari aspects, dispositor web, chara karaka + karakamsa, arudha, yoga/dosha
membership, functional class + yogakaraka, KP ladder, all four dasha-lordship facets, varshaphal,
plus the entire discovered esoteric/tajika/composite/pranic/tri-deva/midpoint layer (facets
61-73, 75). This is well above generic-astrology depth. It falls short of SYNTHESIZABLE because
(a) the structural×temporal convergence asset (facet 52, R-45) — the single most depth-critical
"which promises are ripe now" facet — is held but served-only-by-down-pipeline; (b) the entire
relational-derivation tier (rashi drishti, argala, kartari, vedha, sambandha, neecha-bhanga
enumeration) and the sensitive-degree tier (mrityu bhaga R-47, pushkara, saham) are computed
NOWHERE; (c) remedial-vs-affliction, medical, and deity facets are held only behind
down-pipeline/truly-unreachable channels. Material but bounded gaps → PARTIAL, not UNCOMPOSABLE.

## Findings (held-but-not-received + named nonexistence anchors; all primary class 1 UNREACHABLE)

Suspected layer for HBNR = MCP contract / serving-query (data present, no surgical tool path).
Suspected layer for nonexistence = data plane (writer never computed).

1. **[HIGH] Facet 52 — structural×temporal convergence (R-45).** held in bodha_convergence
   (30 rows) + kala_convergence (6484 rows) for 71aa; matrix channel `served-only-by-down-pipeline`.
   A consuming LLM cannot surgically ask "which of Mercury's yogas/promises are temporally ripe."
   Class 1 (served-only-by-down-pipeline subclass). Rediscovers R-45 anchor.
2. **[MED] Facet 47 — transit-now (gochara/vedha/murthi/AV filter).** kala_* down-pipeline;
   no surgical transit-for-Mercury path. Class 1.
3. **[MED] Facet 49 — double-transit (Saturn+Jupiter) on Mercury's natal points.** kala_activation
   down-pipeline. Class 1.
4. **[MED] Facet 56 — remedial priority reflecting Mercury's actual afflictions.** chart-specific
   prescriptions in bodha_rm_* (served-only-by-down-pipeline); only generic brahma_remedy_corpus is
   surgical, so affliction-matched priority is not retrievable. Class 1.
5. **[LOW] Facet 57 — medical significations from Mercury's afflictions.** bg_medical_mappings
   channel `truly-unreachable`. Class 1.
6. **[LOW] Facet 55 — deity web (nakshatra deity / adhidevata / ishta path).** reference/bg
   catalogs `truly-unreachable`. Class 1.
7. **[LOW] Facet 58 — sambandha table (varna/guna/tattva/direction/metal…).** reference_planets
   `truly-unreachable`; graha_sign_attributes covers only sign-tattva, not the graha sambandha table.
   Class 1.
8. **[MED] Facet 13 — mrityu bhaga (R-47 anchor).** UNREACHABLE-by-nonexistence: no mrityu_bhaga
   category exists per graha (esoteric_point_mrityu is a sphuta, not the per-sign mrityu-bhaga
   degree). Class 1 (data-plane). Rediscovers R-47 anchor. (Not counted in held_but_not_received —
   held_in_db=F — but reported as a named calibration-anchor finding.)

**Class-9 (UNGOVERNED JUDGMENT) note:** facets 41/42 (yoga/dosha participation) are surgically
present via yoga_label/dosha_label but require the consumer to KNOW to filter yoga rows by Mercury
as a constituent graha (constituents live in fact_value_jsonb) — no tool description implies this
join. Logged as a class-9 candidate; the same yoga surface is DROWNED (class 7) in bodha_msr_signals
(199 yoga signals). Not a held-but-not-received count, but recorded for the register dedupe pass.
