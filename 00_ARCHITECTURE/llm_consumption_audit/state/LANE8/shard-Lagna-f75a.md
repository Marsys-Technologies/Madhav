# Lane 8 shard — Lagna dossier · chart 1c826d5a…f75a

- dossier_id: `Lagna_1c826d5a`
- entity: **Lagna** (ascendant point)  · chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
- facets_total: **75** (60 Appendix-B floor + 15 discovered)
- resume_after_row_id: F01500 (all rows graded)
- grading basis: SHAPER #3 (consume the CONCEPT_RETRIEVABILITY_MATRIX; no re-probe of wire reachability the matrix establishes). DB spot-checks via read-only `mcp__postgres__query`.

## Channel doctrine applied (from matrix)
- `chart_facts`, `chart_divisionals`, `chart_dashas` → **reachable-surgical** (wire_reachable = TRUE, ≤2 calls) — verified: all 1219 chart_facts family_keys are `reachable-surgical`.
- `bodha_msr_signals` → mixed (32 surgical / 83 down-pipeline); signal headline/summary keys ARE surgical → yoga/dosha membership reachable.
- `bodha_convergence`, `bodha_cgm_*`, `kala_*`, `phala_*`, `bodha_rm_*` → **served-only-by-down-pipeline** (wire_reachable = FALSE) = held-but-not-received.

## Lagna-specific N/A doctrine
The ascendant is a cusp point, not a graha. Motion (declination/speed/retro/ayana), graha dignity (exalt/deb/mulatrikona/neecha-bhanga), graha strength (shadbala/ishta-kashta/vimsopaka), graha state (combustion/graha-yuddha/avastha/grahan-yuti), chara-karaka assignment, and graha-as-time-lord facets (vimshottari lordship, dasha-quality-from-graha, transit-now, sade-sati) are **N/A-by-nature** — `held=false` here is correct and is NOT a gap/finding.

## Per-facet matrix

| # | facet_group | facet_text (abbrev) | held | wire | usable | channel / note |
|---|---|---|---|---|---|---|
| 1 | B-I | Sign/deg-m-s; bhoga | T | T | T | chart_facts graha_position (Aries 23°31′, house1) surgical |
| 2 | B-I | House whole-sign AND bhava-chalit divergence | T | T | T | house_d1=1; lagna=cusp so chalit≡whole-sign; surgical |
| 3 | B-I | Bhava madhya / sandhi / cusp dual-flavor | T | T | T | near_sign/nak boundary flags on row; surgical |
| 4 | B-I | Nakshatra/pada/lord; KP star/sub/sub-sub | T | T | T | graha_nakshatra_join + graha_kp_lords surgical |
| 5 | B-I | Navatara from Moon AND from Lagna | T | T | T | graha_tara_bala (Sadhaka, pos6) surgical |
| 6 | B-I | Declination/latitude/rise-set/orient-occid | F | F | F | N/A-by-nature (ascendant motion geometry) |
| 7 | B-I | Speed/speed-ratio/retro phase | F | F | F | N/A-by-nature (lagna has no proper motion) |
| 8 | B-I | Ayana/gola | F | F | F | N/A-by-nature (Sun-derived body property) |
| 9 | B-II | Exalt/deb deep-degree | F | F | F | N/A-by-nature (lagna not exalted/debilitated) |
| 10 | B-II | Mulatrikona/own/panchadha w/ sign lord | F | F | F | N/A-by-nature (needs a graha in sign) |
| 11 | B-II | Neecha-bhanga enumeration | F | F | F | N/A-by-nature |
| 12 | B-II | Vargottama; pushkara bhaga/navamsha | T | T | T | vargottama_flag_at_point + divisionals surgical |
| 13 | B-II | Mrityu bhaga per-sign; yogatara | F | F | F | **NONEXISTENCE** (cf `mrityu_bhaga`=0) — R-47 dedupe |
| 14 | B-II | Dagdha/tithi-shunya/mrityu rashi | F | F | F | NONEXISTENCE (not computed per point for lagna) |
| 15 | B-II | Sign-type flavor (chara/tattva/odd-even/udaya) | T | T | T | graha_sign_attributes + reference_signs surgical |
| 16 | B-III | Shadbala full tree vs required-min | F | F | F | N/A-by-nature (no shadbala for a cusp) |
| 17 | B-III | Ishta/Kashta phala | F | F | F | N/A-by-nature |
| 18 | B-III | Vimsopaka + vaiseshikamsha ladder | F | F | F | N/A-by-nature |
| 19 | B-III | Bhava bala houses owned/occupied | T | T | T | cf `bhava_bala*` (660 rows) surgical; lagna=house1 |
| 20 | B-III | Pancha-vargiya bala (Tajaka) | F | F | F | NONEXISTENCE (Tajaka bala not computed) |
| 21 | B-III | Ashtakavarga (BAV/SAV/kaksha/sodhya) | T | T | T | core L1 ashtakavarga asset, lagna BAV; surgical |
| 22 | B-III | Sapta-vargaja dignity / own-varga counts | T | T | T | chart_divisionals (1070 lagna rows) surgical |
| 23 | B-IV | Combustion / graha yuddha | F | F | F | N/A-by-nature |
| 24 | B-IV | Grahan yuti | F | F | F | N/A-by-nature |
| 25 | B-IV | Avastha — all five sets | F | F | F | N/A-by-nature (graha avastha) |
| 26 | B-IV | Gandanta proximity | T | T | T | graha_gandanta (is_gandanta=false) surgical |
| 27 | B-IV | Upagraha contact (gulika/mandi/…) | T | T | T | upagraha positions (35 rows) surgical; contact derivable |
| 28 | B-IV | Saham contacts (Tajaka sahams) | F | F | F | NONEXISTENCE (sahams not computed) |
| 29 | B-V | Conjunctions; aspects cast/received | T | T | T | aspect matrix (20,649 rows) surgical |
| 30 | B-V | Rashi drishti (Jaimini) | F | F | F | NONEXISTENCE (cf `rashi_drishti`=0) |
| 31 | B-V | Sambandha classification per graha | F | F | F | NONEXISTENCE (cf `graha_sambandha`=0; derivable only) |
| 32 | B-V | Dispositor web + chain terminus | T | T | T | nakshatra_dispositor(_chain) for LAGNA surgical |
| 33 | B-V | Papa/shubha kartari | F | F | F | NONEXISTENCE (cf `papa_kartari`=0) |
| 34 | B-V | Argala given/received | T | T | T | argala_natal_matrix (43,500 rows) surgical |
| 35 | B-V | Vedha (SBC / nakshatra vedha / latta) | F | F | F | NONEXISTENCE (natal SBC vedha not computed per point) |
| 36 | B-V | Tara bala from Moon | T | T | T | graha_tara_bala surgical |
| 37 | B-VI | Lordships from Lagna/Moon/Sun; func nature | T | T | T | lordships derivable via sign_lord (surgical); functional-nature CLASSIFICATION absent (noted) |
| 38 | B-VI | Kendradhipati/badhaka/maraka | F | F | F | NONEXISTENCE (cf `badhaka`=0, `maraka`=0) |
| 39 | B-VI | Karaka portfolio; chara karaka + karakamsha | F | F | F | N/A-by-nature (lagna gets no chara-karaka) |
| 40 | B-VI | Arudha involvement (AL, arudhas) | T | T | T | arudha_pada (285 rows) surgical — AL is arudha OF lagna |
| 41 | B-VI | Yoga participation — every family | T | T | T | bodha_msr_signals (235 lagna signals); headline surgical |
| 42 | B-VI | Dosha participation | T | T | T | bodha_msr_signals surgical headline |
| 43 | B-VI | 22nd drekkana / 64th navamsha lord | T | T | T | divisional-derived (D3/D9), surgical |
| 44 | B-VII | Vimshottari lordship now + windows | F | F | F | N/A-by-nature (lagna not a dasha lord) |
| 45 | B-VII | Dasha-quality FROM this graha | F | F | F | N/A-by-nature |
| 46 | B-VII | Other dasha systems (chara/narayana/…) | F | F | F | NONEXISTENCE (cf `chara_dasha`=0,`narayana_dasha`=0) |
| 47 | B-VII | Transit now | F | F | F | N/A-by-nature (lagna does not transit) |
| 48 | B-VII | Sade-sati/dhaiya | F | F | F | N/A-by-nature |
| 49 | B-VII | Double-transit on natal points | F | F | F | NONEXISTENCE (not stored per natal point) |
| 50 | B-VII | Varshaphal role | F | F | F | NONEXISTENCE (Tajaka varshaphal not computed) |
| 51 | B-VII | Eclipses/stations on natal degree | F | F | F | NONEXISTENCE (not stored per natal point) |
| 52 | B-VII | **Structural×temporal convergence (R-45)** | **T** | **F** | **F** | **HELD-BUT-NOT-RECEIVED** — kala_convergence(33)+bodha_convergence(29) both down-pipeline. **FINDING (class 1)** |
| 53 | B-VIII | KP significator ladder; ruling-planet | T | T | T | RP_ASC_LORD/SUB_LORD + graha_kp_lords surgical |
| 54 | B-VIII | Nadi roles / bhrigu-bindu | T | T | T | nadi=Madhya (nak_join) + bhrigu-bindu esoteric; surgical |
| 55 | B-VIII | Deity web (nak deity/adhidevata/ishta) | T | T | T | presiding_deity=Yama (nak_join) surgical |
| 56 | B-VIII | **Remedial mapping + priority-vs-affliction** | **T** | **F** | **F** | **HELD-BUT-NOT-RECEIVED** — bodha_rm_* prescriptions down-pipeline. **FINDING (class 1)** |
| 57 | B-VIII | Medical (avayava/dhatu/tridosha/disease) | T | T | T | bg_medical + bg_nakshatra_medical (reference) surgical |
| 58 | B-VIII | Sambandha table (varna/guna/tattva/…) | T | T | T | nak_join (varna=Mleccha,guna=Rajas,tatva=Jala) surgical |
| 59 | B-VIII | Nodal axis relations | T | T | T | nodal dispositor derivable from position facts; surgical |
| 60 | B-VIII | **Special-lagna relations** (bhava/hora/ghati/varnada/sree/indu + pranapada) | T | T | T | special_lagna (245 rows) + 6 special-lagna subjects; surgical — Lagna's signature facet, fully served |
| 61 | DISC | Panchanga/muhurta window catalog | T | T | T | panchanga_* (32 categories) surgical |
| 62 | DISC | Lal Kitab special point | T | T | T | lal_kitab_special_point (chart_facts) surgical |
| 63 | DISC | Maharishi-specific point | T | T | T | maharsi_specific_point surgical |
| 64 | DISC | Chart-level composite/rollup analytics | T | T | T | chart_center_of_gravity/graha_centrality (chart_facts) surgical |
| 65 | DISC | Contradiction/convergence meta | T | T | T | contradiction_pair(1740)+convergence_count(3045) in **chart_facts** → surgical (NOT down-pipeline) |
| 66 | DISC | Karaka-bhava concordance/overlap | T | T | T | karaka_bhava_concordance(4350)+overlap_flag(60) surgical |
| 67 | DISC | Midpoint (Western) | T | T | T | midpoint (chart_facts) surgical |
| 68 | DISC | Nakshatra co-gravity/co-tenancy/cross-ay | T | T | T | nakshatra_cogravity(10)/co_tenancy(6)/cross_ay (lagna) surgical |
| 69 | DISC | Swamsa position | T | T | T | swamsa_position (chart_facts) surgical |
| 70 | DISC | Tajika hadda/triraashipathi/vargottama | T | T | T | tajik_hadda_lord(1200)/triraashipathi(10) surgical |
| 71 | DISC | Esoteric sphuta web (yogi/brahma/vishnu/…) | T | T | T | esoteric_point_* (chart_facts) surgical |
| 72 | DISC | Pranic strength per graha | T | T | T | pranic_strength_per_graha (chart_facts) surgical |
| 73 | DISC | Tri-deva role strength (Jaimini) | T | T | T | graha_tri_deva_role_strength(45)+jaimini(45) surgical |
| 74 | DISC | Shani special-period catalog | T | T | T | anumukha/ashtama/janma/kantaka… (chart_facts,100) surgical |
| 75 | DISC | Saturn/Sun-derived special points | T | T | T | saturn_derived_point/sun_derived_upagraha surgical |

## Dossier rollup

| metric | value |
|---|---|
| facets_total | 75 |
| held_in_db | 45 |
| wire_reachable | 43 |
| reachable_in_2_calls | 43 |
| usable_form | 43 |
| held_but_not_received | 2 (F52 convergence, F56 remedial) |
| held=false — N/A-by-nature (not gaps) | 18 (F6-11,16-18,23-25,39,44,45,47,48) |
| held=false — NONEXISTENCE gaps (lagna-applicable, canon>system) | 12 (F13,14,20,28,30,31,33,35,38,46,49,50,51 minus overlap) |
| dossier_completeness_pct (usable/total) | 57.3% |
| **dossier_verdict** | **PARTIAL** |

Note on the "/150" grading directive: the ledger holds 75 unique Lagna facets **per chart** (150 across both charts). This worker owns ONE chart, so completeness is graded against its 75-facet dossier (43/75 = 57.3%). Grading against 150 would double-count the sibling chart's rows.

### Verdict rationale
The **positional / relational / participation / esoteric / discovered** core is fully reachable-surgical: sign, nakshatra+KP, dispositor chain, vargottama, ashtakavarga, bhava-bala, gandanta, aspects, argala, Arudha Lagna, yoga+dosha membership, deity/medical/sambandha, the six special-lagnas (the Lagna-signature facet), and the entire discovered analytic layer. That is enough to compose a substantial Lagna reading.

But two depth-axis essentials are **held-but-not-received** (down-pipeline only): structural×temporal convergence (which of lagna's promises are temporally ripe — the R-45 asset) and the remedial-priority mapping. And a cluster of classically-load-bearing lagna facets are **absent by nonexistence**: functional benefic/malefic + badhaka + maraka classification (core to any lagna reading — "which house does each graha rule from this ascendant, and is it benefic"), rashi-drishti, papa/shubha kartari, and chara/narayana rashi-dasha. These are material gaps → **PARTIAL**, not SYNTHESIZABLE. It is not UNCOMPOSABLE because the received core alone supports an acharya-recognizable Lagna dossier.

## Findings (root-caused; all class 1 UNREACHABLE, per Charter §2)

**F-L1 (HELD-BUT-NOT-RECEIVED) — Convergence unreachable for Lagna.** facet 52.
kala_convergence (33 family_keys) and bodha_convergence (29) both carry matrix channel `served-only-by-down-pipeline`; no surgical MCP path returns lagna's structural×temporal convergence. Class 1 (served-only-by-down-pipeline sub-type). Severity HIGH — this is the R-45 depth asset; a consuming LLM cannot answer "which lagna promise is ripe now" over the wire. Suspected layer: MCP contract / serving-query. Dedupe: aligns with R-45 anchor family.

**F-L2 (HELD-BUT-NOT-RECEIVED) — Remedial prescriptions unreachable for Lagna.** facet 56.
bodha_rm_remedy_prescriptions + bodha_rm_* (53+ family_keys) all `served-only-by-down-pipeline`. The served remedial priority and whether it reflects actual afflictions is not wire-reachable. Class 1. Severity MEDIUM. Suspected layer: MCP contract.

**F-L3 (NONEXISTENCE, canon>system) — Functional-nature / badhaka / maraka not computed.** facets 37(partial),38.
`chart_facts` has no `functional_nature`, `badhaka`, or `maraka` category (all count=0). Lagna reading depends on classifying each graha's functional benefic/malefic status from the ascendant; only raw lordship is derivable, the classification layer is absent. Class 1 UNREACHABLE-by-nonexistence (data plane). Severity HIGH — most load-bearing missing lagna facet.

**F-L4 (NONEXISTENCE) — Jaimini rashi-drishti & papa/shubha kartari not computed.** facets 30,33.
`rashi_drishti`=0, `papa_kartari`=0 in chart_facts. Parashari graha-drishti is present (20,649 rows) but Jaimini rashi aspects and hemming on the lagna are absent. Class 1 nonexistence. Severity MEDIUM.

**F-L5 (NONEXISTENCE) — Alternative rashi-dasha systems (chara/narayana) not computed.** facet 46.
`chara_dasha`=0, `narayana_dasha`=0. Narayana dasha canonically begins from the lagna sign; its absence removes a primary lagna-anchored timing system. Class 1 nonexistence. Severity MEDIUM.

**F-L6 (NONEXISTENCE) — Mrityu-bhaga / sahams / SBC-vedha / varshaphal / pancha-vargiya-bala absent for the lagna point.** facets 13,20,28,35,50.
Confirmed `mrityu_bhaga`=0 (rediscovers R-47 anchor — mrityu-bhaga computed nowhere per point). The others are Tajaka/vedha layers not computed. Class 1 nonexistence. Severity LOW-MEDIUM (dedupe R-47 for the mrityu-bhaga component).

## Coverage self-declaration
| surface | status | reason |
|---|---|---|
| Lagna dossier — chart 1c826d5a (75 facets) | audited | all 75 rows graded held/wire/usable |
| Appendix-B floor (60) | audited | — |
| Discovered facets (15) | audited | 61-75 all confirmed held in DB, channel-graded |
