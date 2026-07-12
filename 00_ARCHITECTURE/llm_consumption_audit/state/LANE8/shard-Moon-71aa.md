# Lane 8 shard — Moon dossier, chart 482012f1 (last4 71aa)

- dossier_id: `Moon_482012f1`
- entity: Moon · chart_id: `482012f1-710e-4a25-994a-93821f5871aa`
- facets graded: 75 (60 Appendix-B floor + 15 discovered) — the ledger holds 75 rows for entity=Moon on THIS chart (150 across both charts).
- resume_after_row_id: F01482 (final row; shard complete)
- rubric note: `usable_form` graded per Charter §7.1 (referential resolvability / narration integrity / budget proportionality / signal-to-trivia). Charter §7.1 is DRAFT pending Cowork ratification — this grading is therefore PROVISIONAL per Brief §5.

## Method (SHAPER #3 — consume the matrix, don't re-probe)

`wire_reachable` was read from `CONCEPT_RETRIEVABILITY_MATRIX.jsonl` per the backing table's `channel`:
- **reachable-surgical** (wire=T): `chart_facts`, `chart_divisionals`, `chart_dashas`, `bodha_msr_signals` (yoga/dosha subset), `brahma_ontology`, `brahma_remedy_corpus`.
- **served-only-by-down-pipeline** (wire=F): all `kala_*`, `bodha_rm_*`, `bodha_cgm_*`, `phala_*`, `mimamsa_*`.
- **truly-unreachable** (wire=F): `bg_medical_mappings`, `bg_transit_*`, `reference_*`.

`held_in_db` spot-checked with read-only SQL:
- `chart_facts` (fact_subject ILIKE '%moon%'): 90 fact_categories present — full positional/dignity/strength/avastha/aspect/sambandha/karaka/dispositor/ashtakavarga/vimsopaka/tara/KP/gandanta/midpoint/lal-kitab/esoteric/pranic/tri-deva/nakshatra families.
- `chart_dashas`: 8 dasha systems; Moon appears as lord_graha across periods (MD/AD windows held).
- `chart_divisionals`: Moon placed in 30 vargas (2280 rows).
- `bodha_msr_signals`: 2741 signals reference Moon in configuration_jsonb.
- `kala_convergence`: 6484 convergence rows for this chart (Moon-participating subset present).

## Per-facet matrix

| # | facet_group | facet_text (abbrev) | held | wire | usable | channel |
|---|---|---|---|---|---|---|
| 1 | B-I | Sign/dms/bhoga | T | T | T | reachable-surgical (chart_facts) |
| 2 | B-I | House whole-sign + bhava-chalit | T | T | T | reachable-surgical (chart_facts; chalit-divergence partial) |
| 3 | B-I | Bhava madhya / sandhi proximity | T | T | T | reachable-surgical (chart_facts) |
| 4 | B-I | Nakshatra/pada/lord; KP star/sub | T | T | T | reachable-surgical (chart_facts) |
| 5 | B-I | Navatara from Moon & Lagna | T | T | T | reachable-surgical (chart_facts tara) |
| 6 | B-I | Declination/latitude/rise-set/oriental | F | F | F | NOT COMPUTED (nonexistence) |
| 7 | B-I | Speed/retrograde/stationary | T | T | T | reachable-surgical (chart_facts) |
| 8 | B-I | Ayana/gola | F | F | F | NOT COMPUTED (per-graha declination-dependent) |
| 9 | B-II | Exalt/debil deep-degree | T | T | T | reachable-surgical (chart_facts) |
| 10 | B-II | Mulatrikona/own/panchadha | T | T | T | reachable-surgical (chart_facts) |
| 11 | B-II | Neecha-bhanga enumeration | F | F | F | N/A — Moon not debilitated |
| 12 | B-II | Vargottama/pushkara | T | T | T | reachable-surgical (chart_facts + chart_divisionals) |
| 13 | B-II | Mrityu bhaga / yogatara | F | F | F | NOT COMPUTED (per R-47 family) |
| 14 | B-II | Dagdha/tithi-shunya/mrityu-rashi | F | F | F | NOT COMPUTED |
| 15 | B-II | Sign-type flavor | T | T | T | reachable-surgical (graha_sign_attributes) |
| 16 | B-III | Shadbala complete tree | T | T | T | reachable-surgical (chart_facts shadbala + per_varga) |
| 17 | B-III | Ishta/Kashta phala | T | T | T | reachable-surgical (chart_facts) |
| 18 | B-III | Vimsopaka + vaiseshikamsha | T | T | T | reachable-surgical (chart_facts) |
| 19 | B-III | Bhava bala owned/occupied | T | T | T | reachable-surgical (chart_facts bhava subject) |
| 20 | B-III | Pancha-vargiya bala (Tajaka) | F | F | F | NOT COMPUTED (no natal Tajaka) |
| 21 | B-III | Ashtakavarga BAV/SAV/sodhya | T | T | T | reachable-surgical (chart_facts; transit-AV sub-part absent) |
| 22 | B-III | Sapta-vargaja dignity tally | T | T | T | reachable-surgical (chart_facts) |
| 23 | B-IV | Combustion / graha yuddha | T | T | T | reachable-surgical (chart_facts) |
| 24 | B-IV | Grahan yuti (eclipse assoc.) | F | F | F | NOT COMPUTED |
| 25 | B-IV | Avastha ALL FIVE | T | T | T | reachable-surgical (all 5 avastha categories present) |
| 26 | B-IV | Gandanta proximity | T | T | T | reachable-surgical (graha_gandanta) |
| 27 | B-IV | Upagraha contact | T | T | T | reachable-surgical (chart_facts; marginal) |
| 28 | B-IV | Saham (Tajaka) | F | F | F | NOT COMPUTED |
| 29 | B-V | Conjunctions/aspects/sputa-drishti | T | T | T | reachable-surgical (chart_facts) |
| 30 | B-V | Rashi drishti (Jaimini) | T | T | T | reachable-surgical (chart_facts) |
| 31 | B-V | Sambandha classification | T | T | T | reachable-surgical (sambandha_grade 1160) |
| 32 | B-V | Dispositor web / terminus | T | T | T | reachable-surgical (dispositor_tree/chain) |
| 33 | B-V | Papa/shubha kartari | T | T | T | reachable-surgical (bodha_msr kartari) |
| 34 | B-V | Argala given/received | T | T | T | reachable-surgical (chart_facts; marginal) |
| 35 | B-V | Vedha (SBC/nakshatra/latta) | F | F | F | NOT COMPUTED natally (bg_transit_vedha unreachable) |
| 36 | B-V | Tara bala from Moon | T | T | T | reachable-surgical (chart_facts tara) |
| 37 | B-VI | Lordships/functional/yogakaraka | T | T | T | reachable-surgical (chart_facts) |
| 38 | B-VI | Kendradhipati/badhaka/maraka | T | T | T | reachable-surgical (chart_facts functional class) |
| 39 | B-VI | Karaka portfolio + chara karaka | T | T | T | reachable-surgical (karaka_web + jaimini) |
| 40 | B-VI | Arudha involvement | T | T | T | reachable-surgical (chart_facts; marginal) |
| 41 | B-VI | Yoga participation (every family) | T | T | T | reachable-surgical (bodha_msr yoga subset) — see DROWNED note |
| 42 | B-VI | Dosha participation | T | T | T | reachable-surgical (dosha_label + msr) |
| 43 | B-VI | 22nd drekkana / 64th navamsha | T | T | T | reachable-surgical (chart_divisionals D3/D9) |
| 44 | B-VII | Vimshottari lordship now + windows | T | T | T | reachable-surgical (chart_dashas; "now" = ≤2 calls) |
| 45 | B-VII | Dasha-quality context (from this graha) | T | F | F | **HELD-NOT-RECEIVED** — relativized view in kala_* (served-only) |
| 46 | B-VII | Other dasha systems (yogini/chara/…) | T | T | T | reachable-surgical (chart_dashas 8 systems) |
| 47 | B-VII | Transit now | F | F | F | NOT COMPUTED (real-time; bg_transit_engine unreachable) |
| 48 | B-VII | Sade-sati/dhaiya (as receiver) | F | F | F | NOT COMPUTED (transit-based) |
| 49 | B-VII | Double-transit participation | F | F | F | NOT COMPUTED (transit-based) |
| 50 | B-VII | Varshaphal role | F | F | F | NOT COMPUTED (Tajaka) |
| 51 | B-VII | Eclipses/stations on natal degree | F | F | F | NOT COMPUTED |
| 52 | B-VII | Structural×temporal convergence (R-45) | T | F | F | **HELD-NOT-RECEIVED** — kala_convergence (6484 rows) served-only |
| 53 | B-VIII | KP significator ladder / ruling planet | T | T | T | reachable-surgical (kp_lords/ruling_planets/significator_path) |
| 54 | B-VIII | Nadi/bhrigu-bindu | T | T | T | reachable-surgical (esoteric_point families) |
| 55 | B-VIII | Deity web (nakshatra deity/adhidevata) | T | T | T | reachable-surgical (nakshatra_join; ishta-path partial) |
| 56 | B-VIII | Remedial priority reflects afflictions | T | F | F | **HELD-NOT-RECEIVED** — chart-tuned priority in bodha_rm_* (served-only) |
| 57 | B-VIII | Medical significations from afflictions | T | F | F | **HELD-NOT-RECEIVED** — bg_medical_mappings truly-unreachable |
| 58 | B-VIII | Sambandha table (varna/guna/tattva/…) | T | T | T | reachable-surgical (brahma_ontology) |
| 59 | B-VIII | Nodal axis relations | T | T | T | reachable-surgical (chart_facts; marginal) |
| 60 | B-VIII | Special-lagna relations | T | T | T | reachable-surgical (chart_facts special-lagna points) |
| 61 | DISC | Panchanga/muhurta window catalog | T | T | T | reachable-surgical (chart_facts panchanga_*) |
| 62 | DISC | Lal Kitab special point | T | T | T | reachable-surgical (lal_kitab_special_point) |
| 63 | DISC | Maharishi-specific point | T | T | T | reachable-surgical (chart_facts) |
| 64 | DISC | Chart-level composite overlays | T | T | T | reachable-surgical (chart_cluster/centrality/composite_*) |
| 65 | DISC | Contradiction/convergence meta | T | T | T | reachable-surgical (convergence_count in chart_facts) |
| 66 | DISC | Karaka-bhava concordance | T | T | T | reachable-surgical (chart_facts) |
| 67 | DISC | Midpoint (Western) | T | T | T | reachable-surgical (midpoint, 200 rows) |
| 68 | DISC | Nakshatra co-gravity/statistics | T | T | T | reachable-surgical (nakshatra_cross_ayanamsha etc.) |
| 69 | DISC | Swamsa position | T | T | T | reachable-surgical (swamsa_position) |
| 70 | DISC | Tajika hadda/triraashipathi | T | T | T | reachable-surgical (chart_facts tajik families) |
| 71 | DISC | Esoteric sphuta point web | T | T | T | reachable-surgical (esoteric_point_* incl sri_yantra) |
| 72 | DISC | Pranic strength | T | T | T | reachable-surgical (pranic_strength_per_graha) |
| 73 | DISC | Tri-deva role strength (Jaimini) | T | T | T | reachable-surgical (graha_tri_deva + jaimini) |
| 74 | DISC | Shani special-period catalog | T | T | T | reachable-surgical (chart_facts; marginal) |
| 75 | DISC | Saturn/Sun-derived special points | T | T | T | reachable-surgical (saturn/sun-derived categories) |

## Dossier rollup

- facets_total: 75
- held_in_db: 61
- wire_reachable: 57
- reachable_in_2_calls: 57
- usable_form (composable): 57
- held_but_not_received: 4 (facets 45, 52, 56, 57)
- not-computed / nonexistence (held=F): 14 (facets 6, 8, 11, 13, 14, 20, 24, 28, 35, 47, 48, 49, 50, 51) — mostly transit/Tajaka/declination and the genuinely-N/A neecha-bhanga
- dossier_completeness_pct (usable_form / 75): **76.0%**
- **dossier_verdict: PARTIAL** — Moon's static natal core (position, dignity, full strength battery, all five avastha, relational web, yoga/dosha participation, dasha lordship, 30-varga chain, KP, esoteric points, composites) is fully wire-composable at acharya depth. Material gaps: (a) the entire TEMPORAL/transit dimension (facets 47–51) is not computed natally; (b) the R-45 structural×temporal convergence layer and the chart-tuned remedial/medical layers are HELD in DB but sealed behind the down-pipeline channel — an acharya dossier that must speak to "what is ripe now" and "afflicted-body remedial priority" cannot be composed over the wire.

## Findings (held-but-not-received → Charter §2 failure class)

**L8-Moon-71aa-01 — Structural×temporal convergence unreachable (R-45).** facet 52 / row F01022. `kala_convergence` holds 6484 convergence rows for this chart (Moon-participating subset present), channel = served-only-by-down-pipeline. A consuming LLM cannot retrieve which of Moon's yogas/promises are temporally ripe (recent past + near future) over the MCP wire. **Class 1 UNREACHABLE** (served-only-by-down-pipeline sub-type). Severity: HIGH. Dedupe: relates to anchor R-45; this is the entity-facet instantiation for Moon.

**L8-Moon-71aa-02 — Dasha-quality relativized context unreachable.** facet 45 / row F00882. `chart_dashas` exposes lord_natal_dignity/house (reachable), but the relativized "dignity/house of each running lord FROM Moon and vice versa" is a kala_* down-pipeline derivation. Not composable in ≤2 calls as the relativized matrix. **Class 1 UNREACHABLE** (served-only-by-down-pipeline). Severity: MEDIUM.

**L8-Moon-71aa-03 — Chart-tuned remedial priority unreachable.** facet 56 / row F01102. Generic remedy corpus (`brahma_remedy_corpus`) is reachable, but the chart-specific served remedial priority and its "does-it-reflect-actual-afflictions" adjudication live in `bodha_rm_*` (served-only-by-down-pipeline). **Class 1 UNREACHABLE**. Severity: MEDIUM.

**L8-Moon-71aa-04 — Medical significations unreachable.** facet 57 / row F01122. Moon→body-part/dhatu/dosha/disease mappings live in `bg_medical_mappings` (truly-unreachable) and `bg_nakshatra_medical` (served-only); the per-graha afflicted-body medical synthesis is not wire-retrievable. **Class 1 UNREACHABLE** (truly-unreachable sub-type). Severity: LOW-MEDIUM.

**Secondary (not held-but-not-received; logged for depth-axis).**
- DROWNED risk (Class 7) on facet 41: 2741 `bodha_msr_signals` reference Moon; an unfiltered "Moon's yogas" retrieval buries the signal. Surgical retrieval mitigates, so graded usable=T, but the volume is a depth-axis hazard.
- Nonexistence (Class 1 by-nonexistence) for the 14 held=F facets — chiefly the transit dimension (47–51), Tajaka/varshaphal (20, 28, 50), declination/ayana (6, 8), mrityu-bhaga/dagdha (13, 14), SBC vedha (35). These feed the Section-6 concept-completeness register, not the held-but-not-received count.
