# Lane 8 shard — Rahu dossier · chart 482012f1 (last4 71aa)

- dossier_id: `Rahu_482012f1`
- entity: Rahu · chart_id: `482012f1-710e-4a25-994a-93821f5871aa`
- facets_total (this dossier, per ledger filter): **75** (60 floor + 15 discovered)
  - Note: task template says "150" — that is the entity's row count across BOTH charts (75×2). One dossier = one (entity,chart) = 75 rows per Charter/brief §9(b). Completeness graded against 75.
- resume_after_row_id: F01488 (shard complete)
- method: SHAPER #3 — `wire_reachable = (backing-table channel == reachable-surgical)` consumed from CONCEPT_RETRIEVABILITY_MATRIX; `held_in_db` confirmed by read-only `mcp__postgres__query` batch spot-checks (Rahu subjects `RAH_MEAN` / `RAHU` / `RAH-KET` / derived-point subjects; chart-level categories).

## Rollup
| metric | value |
|---|---|
| facets_total | 75 |
| held_in_db | 62 |
| wire_reachable | 57 |
| reachable_in_2_calls | 57 |
| usable_form | 57 |
| held_but_not_received | 5 |
| absent-by-nonexistence (held=false) | 13 |
| dossier_completeness_pct (usable/75) | 76.0% |
| dossier_verdict | **PARTIAL** |

Verdict rationale: the load-bearing spine of Rahu's dossier — position, dignity, avastha (all 5 sets), full shadbala tree, ishta/kashta, vimsopaka, bhava/ashtakavarga strength, varga chain, aspects/sambandha/argala/dispositor web, karaka portfolio, arudha, yoga+dosha participation (bodha_msr_signals), vimshottari + multi-system dasha, sade-sati, varshaphal/tajaka, KP, nadi, and the full discovered layer — is held AND wire-reachable-surgical AND usable. Composable at acharya depth for the majority of the dossier. But there are MATERIAL gaps: (a) 5 held-but-not-received facets locked behind served-only / truly-unreachable channels (convergence R-45, contradiction meta, medical, deity web, graha sambandha-attribute table); (b) 13 facets absent-by-nonexistence including grahan-yuti for a NODE, rashi drishti, kartari, SBC vedha/latta, neecha-bhanga enumeration, 22nd/64th drekkana. Not UNCOMPOSABLE (spine intact); not SYNTHESIZABLE (node-critical grahan facet and R-45 convergence both unreceivable). → PARTIAL.

## Per-facet matrix
| row | facet_group | facet_text (abbrev) | held_in_db | wire_reachable | usable_form | backing table · channel |
|---|---|---|---|---|---|---|
| F00008 | B-I | sign/deg/bhoga | ✓ | ✓ | ✓ | chart_facts graha_position · reachable-surgical |
| F00028 | B-I | house WS + bhava-chalit divergence | ✓ | ✓ | ✓ | chart_facts (WS held; chalit/Sripati absent) · reachable-surgical |
| F00048 | B-I | bhava-madhya/sandhi/cusp dual | ✓ | ✓ | ✓ | chart_facts graha_gandanta + boundary flags · reachable-surgical |
| F00068 | B-I | nakshatra/pada/lord/KP star-sub | ✓ | ✓ | ✓ | chart_facts graha_nakshatra/pada/kp_lords · reachable-surgical |
| F00088 | B-I | navatara from Moon AND Lagna | ✓ | ✓ | ✓ | chart_facts tara_bala/graha_tara_bala · reachable-surgical |
| F00108 | B-I | declination/latitude/rise-set/oriental | ✗ | – | ✗ | none (no kranti/shara/udaya keys) · nonexistence |
| F00128 | B-I | speed/retro geometry | ✓ | ✓ | ✓ | chart_facts retrograde_flag (speed-ratio absent) · reachable-surgical |
| F00148 | B-I | ayana/gola | ✗ | – | ✗ | none · nonexistence |
| F00168 | B-II | exalt/debil deep-degree | ✓ | ✓ | ✓ | chart_facts special_state_rollup + degree_in_sign · reachable-surgical |
| F00188 | B-II | mulatrikona/panchadha | ✓ | ✓ | ✓ | chart_facts sign_lord/effective_dignity · reachable-surgical |
| F00208 | B-II | neecha-bhanga enumeration | ✗ | – | ✗ | none (not computed) · nonexistence |
| F00228 | B-II | vargottama/pushkara | ✓ | ✓ | ✓ | chart_facts is_vargottama (pushkara absent) · reachable-surgical |
| F00248 | B-II | mrityu bhaga | ✓ | ✓ | ✓ | chart_facts mrityu_bhaga · reachable-surgical |
| F00268 | B-II | dagdha/tithi-shunya/mrityu-rashi | ✗ | – | ✗ | none (unconfirmed) · nonexistence |
| F00288 | B-II | sign-type flavor | ✓ | ✓ | ✓ | chart_facts graha_sign_attributes · reachable-surgical |
| F00308 | B-III | shadbala complete tree | ✓ | ✓ | ✓ | chart_facts graha_shadbala_* (RAH_MEAN; normative-band ratio absent) · reachable-surgical |
| F00328 | B-III | ishta/kashta phala | ✓ | ✓ | ✓ | chart_facts ishta/kashta · reachable-surgical |
| F00348 | B-III | vimsopaka + vaiseshikamsha | ✓ | ✓ | ✓ | chart_facts vimsopaka · reachable-surgical |
| F00368 | B-III | bhava bala owned/occupied | ✓ | ✓ | ✓ | chart_facts bhava_bala (occupied) · reachable-surgical |
| F00388 | B-III | pancha/dwadash-vargiya | ✓ | ✓ | ✓ | chart_facts tajik · reachable-surgical |
| F00408 | B-III | ashtakavarga (SAV occ sign) | ✓ | ✓ | ✓ | chart_facts ashtakavarga (SAV; Rahu-BAV n/a) · reachable-surgical |
| F00428 | B-III | sapta-vargaja/own-varga | ✓ | ✓ | ✓ | chart_facts dispositor_chain_per_varga + chart_divisionals · reachable-surgical |
| F00448 | B-IV | combustion/graha-yuddha | ✓ | ✓ | ✓ | chart_facts combustion_state=none (node n/a) · reachable-surgical |
| F00468 | B-IV | grahan yuti (node+luminary eclipse) | ✗ | – | ✗ | none (no grahan category) · nonexistence — NODE-CRITICAL |
| F00488 | B-IV | avastha all five sets | ✓ | ✓ | ✓ | chart_facts graha_avastha_* + per_varga · reachable-surgical |
| F00508 | B-IV | gandanta proximity | ✓ | ✓ | ✓ | chart_facts graha_gandanta · reachable-surgical |
| F00528 | B-IV | upagraha contact | ✓ | ✓ | ✓ | chart_facts upagraha_position/gulika_mandi · reachable-surgical |
| F00548 | B-IV | saham contacts | ✓ | ✓ | ✓ | chart_facts saham_position · reachable-surgical |
| F00568 | B-V | conjunctions/aspects cast+recv | ✓ | ✓ | ✓ | chart_facts aspect_parashari_given/received · reachable-surgical |
| F00588 | B-V | rashi drishti (Jaimini) | ✗ | – | ✗ | none (not computed) · nonexistence |
| F00608 | B-V | sambandha classification | ✓ | ✓ | ✓ | chart_facts sambandha · reachable-surgical |
| F00628 | B-V | dispositor web/chain terminus | ✓ | ✓ | ✓ | chart_facts graha_dispositor_chain/nakshatra_dispositor · reachable-surgical |
| F00648 | B-V | papa/shubha kartari | ✗ | – | ✗ | none (not computed) · nonexistence |
| F00668 | B-V | argala given/received | ✓ | ✓ | ✓ | chart_facts argala · reachable-surgical |
| F00688 | B-V | SBC vedha/nakshatra-vedha/latta | ✗ | – | ✗ | none (bg_transit_vedha not per-chart) · nonexistence |
| F00708 | B-V | tara bala from Moon | ✓ | ✓ | ✓ | chart_facts tara_bala · reachable-surgical |
| F00728 | B-VI | lordships/functional benefic-malefic | ✓ | ✓ | ✓ | chart_facts lordship/functional · reachable-surgical |
| F00748 | B-VI | kendradhipati/badhaka/maraka | ✓ | ✓ | ✓ | chart_facts lordship (partial) · reachable-surgical |
| F00768 | B-VI | karaka portfolio (naisargika+chara) | ✓ | ✓ | ✓ | chart_facts karaka_chara_position/karakatva · reachable-surgical |
| F00788 | B-VI | arudha involvement | ✓ | ✓ | ✓ | chart_facts arudha · reachable-surgical |
| F00808 | B-VI | yoga participation (every family) | ✓ | ✓ | ✓ | bodha_msr_signals (1951 Rahu signals) · reachable-surgical |
| F00828 | B-VI | dosha participation | ✓ | ✓ | ✓ | chart_facts dosha + bodha_msr_signals · reachable-surgical |
| F00848 | B-VI | 22nd/64th drekkana | ✗ | – | ✗ | none (not computed) · nonexistence |
| F00868 | B-VII | vimshottari now + windows | ✓ | ✓ | ✓ | chart_dashas · reachable-surgical |
| F00888 | B-VII | dasha-quality context | ✓ | ✓ | ✓ | chart_dashas lord_natal_* · reachable-surgical |
| F00908 | B-VII | other dasha systems | ✓ | ✓ | ✓ | chart_dashas system_id (yogini/chara/ashtottari) · reachable-surgical |
| F00928 | B-VII | transit now / gochara | ✗ | – | ✗ | bg_transit_engine truly-unreachable + not stored per-chart · nonexistence/dynamic |
| F00948 | B-VII | sade-sati/dhaiya as receiver | ✓ | ✓ | ✓ | chart_facts sade_sati_phase · reachable-surgical |
| F00968 | B-VII | double-transit (Sa+Ju) | ✗ | – | ✗ | dynamic; not stored · nonexistence/dynamic |
| F00988 | B-VII | varshaphal/tajaka set | ✓ | ✓ | ✓ | chart_facts tajik/varsha · reachable-surgical |
| F01008 | B-VII | eclipses/stations on natal deg | ✗ | – | ✗ | dynamic ephemeris; not stored · nonexistence/dynamic |
| F01028 | B-VII | structural×temporal convergence (R-45) | ✓ | ✗ | ✗ | **kala_convergence (6484 rows) · served-only-by-down-pipeline** → HELD-BUT-NOT-RECEIVED |
| F01048 | B-VIII | KP significator ladder | ✓ | ✓ | ✓ | chart_facts kp_cuspal_significators · reachable-surgical |
| F01068 | B-VIII | nadi/bhrigu-bindu | ✓ | ✓ | ✓ | chart_facts bhrigu_nadi_point · reachable-surgical |
| F01088 | B-VIII | deity web (nakshatra/adhidevata) | ✓ | ✗ | ✗ | **reference_nakshatra L0 · truly-unreachable** → HELD-BUT-NOT-RECEIVED |
| F01108 | B-VIII | remedial mapping | ✓ | ✓ | ✓ | brahma_remedy_corpus reachable-surgical + bodha_msr remedy_hooks (affliction-priority via bodha_rm served-only) |
| F01128 | B-VIII | medical (avayava/dhatu/dosha) | ✓ | ✗ | ✗ | **bg_medical_mappings L0 · truly-unreachable** → HELD-BUT-NOT-RECEIVED |
| F01148 | B-VIII | sambandha table (varna/guna/color) | ✓ | ✗ | ✗ | **reference_planets L0 · truly-unreachable** → HELD-BUT-NOT-RECEIVED |
| F01168 | B-VIII | nodal axis relations/agency | ✗ | – | ✗ | none (nodal-agency rules not computed) · nonexistence |
| F01188 | B-VIII | special-lagna relations | ✓ | ✓ | ✓ | chart_facts special_lagna · reachable-surgical |
| F01208 | DISC | panchanga/muhurta catalog | ✓ | ✓ | ✓ | chart_facts panchanga_* · reachable-surgical |
| F01228 | DISC | lal kitab special point | ✓ | ✓ | ✓ | chart_facts lal_kitab_special_point · reachable-surgical |
| F01248 | DISC | maharshi specific point | ✓ | ✓ | ✓ | chart_facts maharsi_specific_point · reachable-surgical |
| F01268 | DISC | chart-level composite rollups | ✓ | ✓ | ✓ | chart_facts composite_dispositor_strength/composite_state · reachable-surgical |
| F01288 | DISC | contradiction/convergence meta | ✓ | ✗ | ✗ | **kala_convergence served-only + bodha_contradictions EMPTY(0)** → HELD-BUT-NOT-RECEIVED |
| F01308 | DISC | karaka-bhava concordance | ✓ | ✓ | ✓ | chart_facts karakatva_strength_per_significance · reachable-surgical |
| F01328 | DISC | midpoint (Western) | ✓ | ✓ | ✓ | chart_facts midpoint · reachable-surgical |
| F01348 | DISC | nakshatra co-gravity/stats | ✓ | ✓ | ✓ | chart_facts nakshatra_cross_ayanamsha/cogravity · reachable-surgical |
| F01368 | DISC | swamsa position | ✓ | ✓ | ✓ | chart_facts swamsa_position · reachable-surgical |
| F01388 | DISC | tajik hadda/triraashipathi | ✓ | ✓ | ✓ | chart_facts tajik_* · reachable-surgical |
| F01408 | DISC | esoteric sphuta web | ✓ | ✓ | ✓ | chart_facts esoteric_point_avayogi/… · reachable-surgical |
| F01428 | DISC | pranic strength | ✓ | ✓ | ✓ | chart_facts pranic_strength_per_graha · reachable-surgical |
| F01448 | DISC | tri-deva role strength | ✓ | ✓ | ✓ | chart_facts graha_tri_deva_role_strength · reachable-surgical |
| F01468 | DISC | shani special-period catalog | ✓ | ✓ | ✓ | chart_facts shani_*_period (1105) · reachable-surgical |
| F01488 | DISC | saturn/sun-derived point | ✓ | ✓ | ✓ | chart_facts saturn_derived_point · reachable-surgical |

## Findings (held-but-not-received → root-caused, Charter §2 taxonomy)

**FND-Rahu-1 · F01028 · structural×temporal convergence (R-45 asset).** Class 1 UNREACHABLE (served-only-by-down-pipeline). `kala_convergence` holds 6,484 convergence rows for this chart but the matrix marks the entire `kala_*` family `served-only-by-down-pipeline` — no surgical MCP tool fronts it for a consuming LLM. The single most important "which of Rahu's promises are temporally ripe" facet is computed and stored yet unreceivable. Severity: HIGH. Dedupe: this is the R-45 anchor class. Suspected layer: MCP contract / serving-query.

**FND-Rahu-2 · F01288 · contradiction/convergence meta.** Class 1 UNREACHABLE (served-only) with a secondary Class 4 EMPTY SHELL note: convergence-count side is served-only (`kala_convergence`), and the contradiction side (`bodha_contradictions`) returns **0 rows** for this chart — advertised meta-analytic layer is both unreachable and empty. Severity: MEDIUM. Suspected layer: L-writer (bodha_contradictions empty) + MCP contract.

**FND-Rahu-3 · F01128 · medical significations.** Class 1 UNREACHABLE (truly-unreachable). `bg_medical_mappings` (L0 catalog holding avayava/dhatu/tridosha/disease mappings) is channel `truly-unreachable`; 0 per-chart medical facts in `chart_facts`. Rahu's medical significations from its afflictions cannot be received. Severity: MEDIUM. Suspected layer: data plane / MCP contract.

**FND-Rahu-4 · F01088 · deity web.** Class 1 UNREACHABLE (truly-unreachable). nakshatra deity / adhidevata / pratyadhidevata live in `reference_nakshatra` (channel truly-unreachable); not materialized per-chart in `chart_facts` (0). The ishta-devata indication path for Rahu is uncomposable. Severity: LOW-MEDIUM. Suspected layer: data plane.

**FND-Rahu-5 · F01148 · graha sambandha-attribute table.** Class 1 UNREACHABLE (truly-unreachable). varna/guna/tattva/gender/direction/season/taste/metal/grain/color for Rahu live in `reference_planets` (truly-unreachable); not per-chart. Severity: LOW. Suspected layer: data plane.

## Notable absent-by-nonexistence (feed §6 concept-completeness register; NOT held-but-not-received)
Class 1 UNREACHABLE-by-nonexistence — computed nowhere per graha:
- **F00468 grahan yuti** — NODE-CRITICAL: no node+luminary eclipse-association facet exists though Rahu is a shadow-graha whose defining act is grahan. High-value gap.
- F00588 rashi drishti (Jaimini) · F00648 papa/shubha kartari · F00688 SBC vedha/nakshatra-vedha/latta · F00208 neecha-bhanga enumeration · F00848 22nd/64th drekkana (khareshwara) · F01168 nodal-axis agency rules.
- F00108 declination/latitude/rise-set · F00148 ayana/gola · F00268 dagdha/tithi-shunya.
- F00928/F00968/F01008 transit-now / double-transit / eclipse-stations — dynamic gochara; `bg_transit_engine` truly-unreachable and nothing stored per-chart.

## §7.1 usable-form grading note (provisional flag)
Charter §7.1/§7.2 rubrics are RATIFIED (Charter v1.1 frontmatter, 2026-07-12) — grading is NOT provisional. All reachable-surgical facets pass §7.1: chart_facts rows are self-describing (fact_key + fact_value_text + citation_human), single-call resolvable, budget-bounded per surgical query; bodha_msr_signals expose `signal_summary_text`/`signal_headline_text` (resolvable narration, not bare IDs). No §7.1 class-6/7 failures among the received set.
