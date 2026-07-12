# Lane 8 shard trace — Sun dossier, chart 482012f1 (last4 71aa)

- dossier_id: `Sun_482012f1`
- entity: Sun | chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- facets graded: 75 / 75 (60 Appendix-B floor + 15 discovered)
- resume_after_row_id: F01481 (shard complete)
- rubric provenance: Charter §7.1 usable-form (RATIFIED, GATE_RATIFICATION v1.1 §1) — grading is final, not provisional.

## Grading rule (SHAPER #3 — consume the matrix, do not re-probe)
`wire_reachable` is read from CONCEPT_RETRIEVABILITY_MATRIX.jsonl per the facet's backing table:
- `chart_facts` / `chart_divisionals` / `chart_dashas` → channel **`reachable-surgical`** → wire_reachable=true, ≤2 calls=true, usable_form=true (rows carry `fact_value_text`+`citation_human`, self-describing).
- `bodha_*` / `kala_*` / `phala_*` / `mimamsa_*` → channel **`served-only-by-down-pipeline`** → wire_reachable=false → HELD-BUT-NOT-RECEIVED.
- L0 `bg_*` / `reference_*` → channel **`truly-unreachable`** → wire_reachable=false.
- absent from every table → held_in_db=false → UNREACHABLE-BY-NONEXISTENCE (data-plane gap).

DB spot-checks (read-only, chart 482012f1) confirmed held/not-held per group (see finding evidence).

## Per-facet matrix

| row_id | facet_group | facet_text (abbrev) | backing | held | wire | ≤2 | usable |
|---|---|---|---|---|---|---|---|
| F00001 | B-I | Sign/dms/bhoga | chart_facts.graha_position | Y | Y | Y | Y |
| F00021 | B-I | House whole-sign+chalit | chart_facts (bhava_chalit=540) | Y | Y | Y | Y |
| F00041 | B-I | Bhava-madhya/sandhi/cusp | chart_facts + boundary flags | Y | Y | Y | Y |
| F00061 | B-I | Nakshatra/pada/lord; KP star/sub | graha_nakshatra_join/kp_lords | Y | Y | Y | Y |
| F00081 | B-I | Navatara from Moon & Lagna | graha_tara_bala (Lagna-side partial) | Y | Y | Y | Y |
| F00101 | B-I | Declination/shara/rise-set/orient | **none (0 rows)** | N | N | N | N |
| F00121 | B-I | Speed/ratio/stationary/retro | chart_facts (speed_motion=592) | Y | Y | Y | Y |
| F00141 | B-I | Ayana/gola | chart_facts (ayana_gola=107) | Y | Y | Y | Y |
| F00161 | B-II | Exalt/debil deep-degree | graha_dignity_per_varga | Y | Y | Y | Y |
| F00181 | B-II | Mulatrikona/own/panchadha | dignity+saptavargaja+sign_attr | Y | Y | Y | Y |
| F00201 | B-II | Neecha-bhanga enumeration | dignity (Sun in Cap → not debil, N/A) | Y | Y | Y | Y |
| F00221 | B-II | Vargottama; pushkara | vargottama_per_varga (pushkara=0) | Y | Y | Y | Y* |
| F00241 | B-II | Mrityu bhaga; yogatara | chart_facts (mrityu=105) | Y | Y | Y | Y |
| F00261 | B-II | Dagdha/tithi-shunya/mrityu-rashi | chart_facts (dagdha=9) | Y | Y | Y | Y |
| F00281 | B-II | Sign-type flavor | graha_sign_attributes | Y | Y | Y | Y |
| F00301 | B-III | Shadbala complete tree vs minimum | chart_facts shadbala_* (all 6) | Y | Y | Y | Y* |
| F00321 | B-III | Ishta/Kashta | graha_ishta/kashta_phala | Y | Y | Y | Y |
| F00341 | B-III | Vimsopaka + vaiseshikamsha | vimsopaka_* (4 categories) | Y | Y | Y | Y |
| F00361 | B-III | Bhava bala owned/occupied | in_house_composite_strength | Y | Y | Y | Y |
| F00381 | B-III | Pancha/dwadash-vargiya bala | saptavargaja + vargbala | Y | Y | Y | Y |
| F00401 | B-III | Ashtakavarga full battery | ashtakavarga_* (many) | Y | Y | Y | Y |
| F00421 | B-III | Sapta-vargaja dignity tally | graha_saptavargaja_bala | Y | Y | Y | Y |
| F00441 | B-IV | Combustion + graha-yuddha | combustion=725, yuddha=16 | Y | Y | Y | Y |
| F00461 | B-IV | Grahan yuti (node/eclipse) | conjunction w/ nodes | Y | Y | Y | Y |
| F00481 | B-IV | Avastha ALL FIVE | graha_avastha_baladi..sayanadi | Y | Y | Y | Y |
| F00501 | B-IV | Gandanta proximity | graha_gandanta=5 | Y | Y | Y | Y |
| F00521 | B-IV | Upagraha contact | upagraha=423 | Y | Y | Y | Y |
| F00541 | B-IV | Saham contacts | saham=2800 | Y | Y | Y | Y |
| F00561 | B-V | Conjunctions/parashari aspects | aspect_parashari + virupa_drishti | Y | Y | Y | Y |
| F00581 | B-V | Rashi drishti (Jaimini) | derivable from positions | Y | Y | Y | Y |
| F00601 | B-V | Sambandha classification | sambandha_grade=1160 | Y | Y | Y | Y |
| F00621 | B-V | Dispositor web/terminus | dispositor_tree + nak_dispositor_chain | Y | Y | Y | Y |
| F00641 | B-V | Papa/shubha kartari | **none (0 rows)** | N | N | N | N |
| F00661 | B-V | Argala given/received | argala=43500 | Y | Y | Y | Y |
| F00681 | B-V | Vedha (SBC/nakshatra/latta) | **none (0 rows)** | N | N | N | N |
| F00701 | B-V | Tara bala from Moon | graha_tara_bala | Y | Y | Y | Y |
| F00721 | B-VI | Lordships/functional class | functional_class_per_ascendant | Y | Y | Y | Y |
| F00741 | B-VI | Kendradhipati/badhaka/maraka | derivable from lordships | Y | Y | Y | Y |
| F00761 | B-VI | Naisargika/chara karaka+karakamsha | karaka_web + chara_karaka dasha | Y | Y | Y | Y |
| F00781 | B-VI | Arudha involvement | arudha=495 | Y | Y | Y | Y |
| F00801 | B-VI | **Yoga participation (every family)** | bodha_msr_signals (83/115 down-pipeline) | Y | **N** | N | **N** |
| F00821 | B-VI | **Dosha participation (full catalog)** | brahma_dosha_catalog + bodha_contradictions | Y | **N** | N | **N** |
| F00841 | B-VI | 22nd drekkana / 64th navamsha lord | **none (0 rows)** | N | N | N | N |
| F00861 | B-VII | Vimshottari MD/AD/PD now+windows | chart_dashas | Y | Y | Y | Y |
| F00881 | B-VII | Dasha-quality context (lord dignity) | chart_dashas.lord_natal_dignity_d1 | Y | Y | Y | Y |
| F00901 | B-VII | Other dasha systems | chart_dashas (yogini/ashtottari/kalachakra) | Y | Y | Y | Y |
| F00921 | B-VII | **Transit now (gochara)** | bg_transit_engine (truly-unreachable) | Y | **N** | N | **N** |
| F00941 | B-VII | Sade-sati/dhaiya | N/A for Sun (Moon/Saturn facet) | N | N | N | N |
| F00961 | B-VII | **Double-transit on natal points** | kala_/bg_transit (down-pipeline) | Y | **N** | N | **N** |
| F00981 | B-VII | Varshaphal (year-lord/tajaka) | chart_dashas varsha_year_lord (partial) | Y | Y | Y | Y* |
| F01001 | B-VII | Eclipses/stations on natal degree | **none (0 rows)** | N | N | N | N |
| F01021 | B-VII | **Structural×temporal convergence (R-45)** | kala_convergence (down-pipeline) | Y | **N** | N | **N** |
| F01041 | B-VIII | KP significator ladder/ruling-planet | graha_kp_lords + significator_path=80 | Y | Y | Y | Y |
| F01061 | B-VIII | Nadi roles / bhrigu-bindu | bhrigu_nadi_point + esoteric_bhrigu_bindu | Y | Y | Y | Y |
| F01081 | B-VIII | **Deity web (nak/adhidevata/ishta)** | reference_nakshatra (truly-unreachable) | Y | **N** | N | **N** |
| F01101 | B-VIII | **Remedial mapping + priority** | bodha_rm_remedy_prescriptions (down-pipeline) | Y | **N** | N | **N** |
| F01121 | B-VIII | **Medical (avayava/dhatu/disease)** | bg_medical_mappings (truly-unreachable) | Y | **N** | N | **N** |
| F01141 | B-VIII | **Sambandha table (varna/guna/tattva)** | reference_planets (truly-unreachable) | Y | **N** | N | **N** |
| F01161 | B-VIII | Nodal axis relations | dispositor_tree + node conjunctions | Y | Y | Y | Y |
| F01181 | B-VIII | Special-lagna relations | chart_facts special_lagna + esoteric pts | Y | Y | Y | Y |
| F01201 | DISC | Panchanga/muhurta window catalog | chart_facts panchanga_* | Y | Y | Y | Y |
| F01221 | DISC | Lal Kitab special point | lal_kitab_special_point=10 | Y | Y | Y | Y |
| F01241 | DISC | Maharishi-specific point | chart_facts maharsi_specific_point | Y | Y | Y | Y |
| F01261 | DISC | Chart-level composite/rollup | chart_cluster/graha_centrality/composite_* | Y | Y | Y | Y |
| F01281 | DISC | Contradiction/convergence meta | convergence_count=145 (contradiction_pair down-pipeline) | Y | Y | Y | Y* |
| F01301 | DISC | Karaka-bhava concordance/overlap | chart_facts karaka concordance categories | Y | Y | Y | Y |
| F01321 | DISC | Midpoint (Western) | midpoint=200 | Y | Y | Y | Y |
| F01341 | DISC | Nakshatra co-gravity/stats | nakshatra_cross_ayanamsha + co-tenancy | Y | Y | Y | Y |
| F01361 | DISC | Swamsa position | chart_facts swamsa_position | Y | Y | Y | Y |
| F01381 | DISC | Tajika hadda/triraashipathi | chart_facts tajik_* categories | Y | Y | Y | Y |
| F01401 | DISC | Esoteric sphuta web | esoteric_point_* (sri_yantra etc) | Y | Y | Y | Y |
| F01421 | DISC | Pranic strength | pranic_strength_per_graha=5 | Y | Y | Y | Y |
| F01441 | DISC | Tri-deva role strength (Jaimini) | graha_tri_deva_role_strength=5 | Y | Y | Y | Y |
| F01461 | DISC | Shani special-period catalog | N/A for Sun (Saturn-transit facet) | N | N | N | N |
| F01481 | DISC | Sun-derived special points/upagraha | sun_derived_upagraha=70 | Y | Y | Y | Y |

`Y*` = usable but partial (one bundled sub-facet held-but-unreachable or absent — pushkara F00221; required-minimum band F00301; muntha/tajaka-yoga set F00981; contradiction_pair F01281). Graded usable=Y because the dominant reachable-surgical component composes; sub-gap noted in findings.

## Dossier rollup
- facets_total: **75**
- held_in_db: **68** (7 not held: F00101, F00641, F00681, F00841, F01001 = nonexistence; F00941, F01461 = N/A-for-Sun)
- wire_reachable: **59**
- reachable_in_2_calls: **59**
- usable_form: **59**
- held_but_not_received: **9** (F00801, F00821, F00921, F00961, F01021, F01081, F01101, F01121, F01141)
- dossier_completeness_pct: **78.7%** (59 usable / 75 facets; NB — the task template's "/150" denominator does not match this entity's actual 75-facet ledger, so completeness is reported against the true facet total per Charter §4 crit.3 "full facet matrices").
- dossier_verdict: **PARTIAL** — the deterministic core (all positional / dignity / strength / state / relational / karaka / dasha facets) is 100% reachable-surgical and fully synthesizable, but four synthesis-critical facet classes (yoga participation, dosha participation, structural×temporal convergence/ripeness, remedial priority) are held-but-not-received. Per Charter §1 ("Considering Mercury without its dossier is not synthesis"), a dossier missing wire-access to its own yoga/dosha membership and temporal ripeness is composable-with-material-gaps, not fully SYNTHESIZABLE — but far from UNCOMPOSABLE.

## Findings (held-but-not-received + nonexistence; all class 1)

Note on class: per Charter §2, class 1 UNREACHABLE covers both "served-only-by-down-pipeline" (computed by an L2+ writer, surgical MCP wire does not expose it) and "truly-unreachable" (no serving path) and, via plan §2.1, "UNREACHABLE-by-nonexistence" (never computed). Sub-type quoted verbatim from the matrix `channel` per E-6.

1. **F00801 Yoga participation — held-but-not-received.** bodha_msr_signals yoga-family rows split `{reachable-surgical:32, served-only-by-down-pipeline:83}`; the full catalog (raja/dhana/mahapurusha/nabhasa/chandra/surya/parivartana/viparita/NBRY/adhi/gaja-kesari/kala-sarpa/…) is majority `served-only-by-down-pipeline`. A consuming LLM cannot surgically pull Sun's yoga membership. class 1, HIGH.
2. **F00821 Dosha participation — held-but-not-received.** brahma_dosha_catalog `served-only-by-down-pipeline`; bodha_contradictions `truly-unreachable`. Per-chart dosha membership for Sun is unreachable over the wire. class 1, HIGH.
3. **F01021 Structural×temporal convergence (R-45 anchor) — held-but-not-received.** kala_convergence / kala_activation channel `served-only-by-down-pipeline`. Which of Sun's promises are temporally ripe (recent-past/near-future) is computed but not wire-served — R-45 rediscovered independently. class 1, HIGH.
4. **F01101 Remedial mapping + priority — held-but-not-received.** bodha_rm_remedy_prescriptions `served-only-by-down-pipeline` (brahma_remedy_corpus is reachable-surgical but is the generic catalog, not Sun's chart-specific affliction-weighted priority). class 1, MEDIUM.
5. **F00921 Transit-now + F00961 double-transit — held-but-not-received.** bg_transit_engine / bg_transit_rules `truly-unreachable`; kala transit-derived windows `served-only-by-down-pipeline`. Sun's current gochara and double-transit participation not wire-reachable. class 1, MEDIUM.
6. **F01121 Medical significations — held-but-not-received.** bg_medical_mappings `truly-unreachable`; bg_nakshatra_medical `served-only-by-down-pipeline`. Sun's avayava/dhatu/dosha/disease mapping unreachable. class 1, MEDIUM.
7. **F01141 Sambandha attribute table — held-but-not-received.** reference_planets (varna/guna/tattva/metal/grain/color) channel `truly-unreachable`; only the sign-derived slice (graha_sign_attributes) is surgical. class 1, LOW.
8. **F01081 Deity web — held-but-not-received.** reference_nakshatra (nakshatra deity / adhidevata / pratyadhidevata) channel `truly-unreachable`; ishta-devata path (karakamsha 12th) not composed per-chart. class 1, LOW.
9. **F00101 Declination/celestial-latitude/rise-set/oriental-occidental — UNREACHABLE-by-nonexistence.** 0 rows in chart_facts (declination/kranti/shara/latitude). Data-plane gap. class 1, MEDIUM.
10. **F00641 Papa/shubha kartari — UNREACHABLE-by-nonexistence.** 0 rows (no kartari fact_category). class 1, MEDIUM.
11. **F00681 Vedha (Sarvatobhadra chakra / nakshatra-vedha / latta) — UNREACHABLE-by-nonexistence.** 0 rows. class 1, MEDIUM.
12. **F00841 22nd drekkana (khareshwara) / 64th navamsha lord — UNREACHABLE-by-nonexistence.** 0 rows; a classical maraka/arishta indicator absent from the data plane. class 1, MEDIUM.
13. **F01001 Eclipses/stations on natal degree — UNREACHABLE-by-nonexistence.** 0 rows (no forward-ephemeris on natal points). class 1, LOW.
14. **F00221 Pushkara bhaga/navamsha (sub-facet) — UNREACHABLE-by-nonexistence.** pushkara=0 rows; vargottama (the facet's other half) is reachable-surgical, so the bundle grades usable-partial. class 1, LOW.

## Coverage self-declaration
- Sun dossier — chart 482012f1: **audited** (75/75 rows graded, resume pointer at F01481).
- N/A-for-Sun rows (F00941 sade-sati, F01461 Shani-period catalog) recorded as held_in_db=false, excluded from held-but-not-received (semantically Moon/Saturn-only facets), no finding.
