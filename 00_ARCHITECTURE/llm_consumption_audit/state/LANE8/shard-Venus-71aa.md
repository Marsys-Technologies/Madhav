# Lane 8 Shard Trace — Venus dossier — chart 482012f1 (last4 71aa)

dossier_id: Venus_482012f1  |  entity: Venus  |  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
resume_after_row_id: F01486   |  status: done   |  rows: 75/75

SHAPER #3 applied: wire_reachable read from CONCEPT_RETRIEVABILITY_MATRIX.jsonl channel per backing table (channel==reachable-surgical => wire_reachable). Reachability NOT re-probed. held_in_db confirmed via read-only mcp__postgres__query spot-checks on chart 482012f1.

NOTE on facet count: task template cited "150 facets / usable_form/150"; ground truth = **75 facets for THIS chart** (60 Appendix-B floor + 15 DISCOVERED). 150 = both charts (75×2). Graded against my chart's 75. completeness = usable/75.

| # | facet_group | facet_text | held_in_db | wire_reachable | ≤2 | usable_form | channel | backing table / evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | B-I | Sign, degree-minute-second; bhoga traversed | T | T | T | T | reachable-surgical | chart_facts — graha_position |
| 2 | B-I | House by whole-sign AND bhava-chalit (Sripati/Placidus) — divergence f | T | T | T | T | reachable-surgical | chart_facts — VEN-HOUSE_* + graha_position (WS + chalit) |
| 3 | B-I | Bhava madhya distance; bhava/rashi/nakshatra sandhi proximity; cusp du | T | T | T | T | reachable-surgical | chart_facts — near_sign/nakshatra_boundary_flag, sandhi |
| 4 | B-I | Nakshatra, pada, nakshatra lord; KP star/sub/sub-sub | T | T | T | T | reachable-surgical | chart_facts — graha_nakshatra_join + graha_kp_lords (star/sub/subsub) |
| 5 | B-I | Navatara class from Moon AND from Lagna (janma/sampat/vipat/kshema/pra | T | T | T | T | reachable-surgical | chart_facts — graha_tara_bala / navatara |
| 6 | B-I | Declination (kranti), celestial latitude (shara); rise/set state (uday | F | F | F | F | —(not held) | NONE(canon) — kranti/shara/declination=0 rows — NOT computed |
| 7 | B-I | Speed, speed-ratio to mean, stationary proximity; retrograde/direct ph | T | T | T | T | reachable-surgical | chart_facts — graha_position speed/retro geometry |
| 8 | B-I | Ayana placement (uttarayana/dakshinayana); gola | T | T | T | T | reachable-surgical | chart_facts — ayana/gola attributes |
| 9 | B-II | Exaltation/debilitation with exact deep-degree distance; ucha-abhilash | T | T | T | T | reachable-surgical | chart_facts — graha_effective_dignity + deep-degree |
| 10 | B-II | Mulatrikona / own / panchadha compound relation (natural × temporal) w | T | T | T | T | reachable-surgical | chart_facts — graha_sign_attributes / dignity compound |
| 11 | B-II | Neecha-bhanga condition enumeration (all classical grounds, each with  | F | F | F | F | —(not held) | NONE(canon) — neecha_bhanga=0 — NOT computed |
| 12 | B-II | Vargottama; pushkara bhaga; pushkara navamsha | T | T | T | F | reachable-surgical | chart_divisionals — vargottama HELD+reachable; pushkara bhaga/navamsha=0 NOT computed -> facet not composable |
| 13 | B-II | Mrityu bhaga (per-sign degree check); yogatara proximity | F | F | F | F | —(not held) | NONE(canon) — mrityu_bhaga=0 — NOT computed (R-47 anchor) |
| 14 | B-II | Dagdha / tithi-shunya / mrityu rashi ownership effects | T | T | T | T | reachable-surgical | chart_facts — dagdha/tithi-shunya/mrityu-rashi sign ownership (graha_sign_attributes) |
| 15 | B-II | Sign-type flavor: chara/sthira/dvisvabhava, odd/even, tattva, prishtod | T | T | T | T | reachable-surgical | chart_facts — graha_sign_attributes flavor |
| 16 | B-III | Shadbala complete tree: sthana (uccha/saptavargaja/ojayugma/kendradi/d | T | T | T | T | reachable-surgical | chart_facts — graha_shadbala_* full tree |
| 17 | B-III | Ishta/Kashta phala | T | T | T | T | reachable-surgical | chart_facts — graha_ishta_phala/graha_kashta_phala |
| 18 | B-III | Vimsopaka (shadvarga/saptavarga/dashavarga/shodashavarga) + vaiseshika | T | T | T | T | reachable-surgical | chart_facts — graha_vimsopaka_* (shad/sapta/dasa/shodasa) |
| 19 | B-III | Bhava bala of houses owned and occupied | T | T | T | T | reachable-surgical | chart_facts — bhava bala owned/occupied |
| 20 | B-III | Pancha-vargiya bala (Tajaka context); dwadash-vargiya where computed | T | T | T | T | reachable-surgical | chart_facts — pancha-vargiya/Tajaka bala |
| 21 | B-III | Ashtakavarga: BAV per-sign bindus + total; bindus in occupied sign; ka | T | T | T | T | reachable-surgical | chart_facts — ashtakavarga_pinda_bhinna/sarva/sodhita |
| 22 | B-III | Sapta-vargaja dignity tally; own-varga counts | T | T | T | T | reachable-surgical | chart_facts — graha_saptavargaja_bala_component |
| 23 | B-IV | Combustion with orb, applying/separating; graha yuddha (winner/loser,  | T | T | T | T | reachable-surgical | chart_facts — combustion=815 rows |
| 24 | B-IV | Grahan yuti (node + luminary eclipse association) | T | T | T | T | reachable-surgical | chart_facts — grahan yuti / node-luminary assoc |
| 25 | B-IV | Avastha sets — ALL FIVE: baladi (5), jagradadi (3), deepta-adi (9), la | T | T | T | T | reachable-surgical | chart_facts — graha_avastha baladi/deepta/jagrad/lajjitadi/sayanadi ALL FIVE |
| 26 | B-IV | Gandanta (rashi-nakshatra junction) proximity | T | T | T | T | reachable-surgical | chart_facts — graha_gandanta=50 |
| 27 | B-IV | Upagraha contact: gulika, mandi, dhuma, vyatipata, parivesha, indracha | T | T | T | T | reachable-surgical | chart_facts — upagraha=470 (gulika/mandi/dhuma...) |
| 28 | B-IV | Saham contacts (Tajaka sahams: punya, vidya, vivaha, mrityu, karma, …) | T | T | T | T | reachable-surgical | chart_facts — saham=2800 |
| 29 | B-V | Conjunctions (orb-aware); parashari aspects cast/received with sputa-d | T | T | T | T | reachable-surgical | chart_facts — aspect_parashari_given + special aspects |
| 30 | B-V | Rashi drishti (Jaimini) cast/received | T | T | T | T | reachable-surgical | chart_facts — rashi drishti (Jaimini) |
| 31 | B-V | Sambandha classification with each graha (exchange, mutual aspect, mut | T | T | T | T | reachable-surgical | chart_facts — sambandha classification |
| 32 | B-V | Dispositor web: sign dispositor, nakshatra dispositor, navamsha dispos | T | T | T | T | reachable-surgical | chart_facts — graha_dispositor_chain + nakshatra_dispositor_chain |
| 33 | B-V | Papa/shubha kartari on its position | F | F | F | F | —(not held) | NONE(canon) — kartari=0 — papa/shubha kartari NOT computed |
| 34 | B-V | Argala on its positions: shubha/papa/virodha, given and received | T | T | T | T | reachable-surgical | chart_facts — argala=43500 given+received |
| 35 | B-V | Vedha: Sarvatobhadra chakra vedhas on its nakshatra; nakshatra vedha p | F | F | F | F | —(not held) | NONE(canon) — sarvatobhadra vedha/latta=0 — NOT computed |
| 36 | B-V | Tara bala from Moon (and chandra kriya/vela/avastha for the Moon dossi | T | T | T | T | reachable-surgical | chart_facts — graha_tara_bala from Moon |
| 37 | B-VI | Lordships from Lagna, Moon, Sun; functional benefic/malefic/neutral; y | T | T | T | T | reachable-surgical | chart_facts — graha_functional_class_per_ascendant + yoga_karaka_flag |
| 38 | B-VI | Kendradhipati dosha; badhaka/badhakesh status; maraka lordship/associa | T | T | T | T | reachable-surgical | chart_facts — kendradhipati/badhaka/maraka (functional class derived) |
| 39 | B-VI | Naisargika karaka portfolio; sthira karaka; chara karaka (AK/AmK/BK/MK | T | T | T | T | reachable-surgical | chart_facts — ATMA/AMATYAKARAKA + naisargika karaka + karakamsha |
| 40 | B-VI | Arudha involvement: AL lord, arudhas of owned houses, graha arudha pos | T | T | T | T | reachable-surgical | chart_facts — ARUDHA_VE / BHAVA_ARUDHA |
| 41 | B-VI | Yoga participation — EVERY catalog family: raja (house-lord), dhana, m | T | T | T | T | reachable-surgical | bodha_msr_signals — 3140 Venus signals; msr reachable-surgical portion serves yoga membership (DROWNED/UNATTRIBUTED risk R-37/R-44 on served-only bulk) |
| 42 | B-VI | Dosha participation: mangal (from lagna/Moon/Venus), shrapit, pitru, g | T | T | T | T | reachable-surgical | chart_facts — dosha participation (mangal/etc) + brahma_dosha_catalog |
| 43 | B-VI | 22nd drekkana (khareshwara) and 64th navamsha lord status; sarpa/pasha | F | F | F | F | —(not held) | NONE(canon) — 22nd-drekkana/64th-navamsa/sarpa-drekkana=0 — NOT computed |
| 44 | B-VII | Vimshottari lordship now (MD/AD/PD/sookshma/prana) + next windows at e | T | T | T | T | reachable-surgical | chart_dashas — vimshottari MD/AD/PD lord + windows (reachable-surgical) |
| 45 | B-VII | Dasha-quality context: dignity/house of each running lord FROM this gr | T | T | T | T | reachable-surgical | chart_dashas — lord_natal_* dignity/house-from-graha columns |
| 46 | B-VII | Other dasha systems: yogini role; chara/narayana rashi-dasha periods o | T | T | T | T | reachable-surgical | chart_dashas — yogini/chara/ashtottari/kalachakra systems (yogini=83740) |
| 47 | B-VII | Transit now: sign/house from natal Moon and Lagna, gochara quality + v | F | F | F | F | —(not held) | bg_transit_engine — transit_gochara=0 stored; live transit not a natal fact / transit engine truly-unreachable |
| 48 | B-VII | Sade-sati/dhaiya involvement (Saturn dossier; Moon dossier as receiver | T | T | T | T | reachable-surgical | chart_facts — sade_sati/dhaiya=5182 |
| 49 | B-VII | Double-transit (Saturn+Jupiter) participation on natal points | F | F | F | F | —(not held) | bg_transit_engine — double-transit not stored; transit-dependent, not computed as natal fact |
| 50 | B-VII | Varshaphal role: year-lord candidacy, muntha relation, tajaka aspect s | T | T | T | T | reachable-surgical | chart_facts — varshaphal=1245 + tajik_hadda (muntha/year-lord/tajaka) |
| 51 | B-VII | Upcoming/recent eclipses and stations on its natal degree | F | F | F | F | —(not held) | bg_transit_engine — live eclipses/stations on natal degree not stored; ephemeris-live |
| 52 | B-VII | Structural×temporal convergence: which of its yogas/promises are tempo | T | F | F | F | served-only-by-down-pipeline | kala_convergence — kala_convergence=6484; channel served-only-by-down-pipeline -> NOT surgically reachable (R-45) |
| 53 | B-VIII | KP significator ladder roles (house-wise); ruling-planet membership | T | T | T | T | reachable-surgical | chart_facts — graha_kp_lords / significator ladder |
| 54 | B-VIII | Nadi roles (jeeva/karma pairs, bhrigu-bindu relation) where computed | T | T | T | T | reachable-surgical | chart_facts — nadi/jeeva-karma/bhrigu-bindu=405 |
| 55 | B-VIII | Deity web: nakshatra deity, adhidevata/pratyadhidevata; ishta-devata i | T | F | F | F | truly-unreachable | reference_nakshatra — nakshatra deity/adhidevata held only in reference_* catalog (truly-unreachable); chart_facts deity=0 |
| 56 | B-VIII | Remedial mapping: gemstone, beeja/vedic mantra, yantra, dana, vrata-va | T | F | F | F | served-only-by-down-pipeline | bodha_rm_remedy_prescriptions — remedial mapping held in bodha_rm_* (served-only-by-down-pipeline); chart_facts gemstone/mantra=0 |
| 57 | B-VIII | Medical: avayava/body-part, dhatu, vata-pitta-kapha, disease significa | T | F | F | F | truly-unreachable | bg_medical_mappings — medical avayava/dhatu held in bg_medical_mappings (truly-unreachable)/bg_nakshatra_medical (down-pipeline); chart_facts=0 |
| 58 | B-VIII | Sambandha table: varna, guna, tattva, gender, direction, season, taste | T | F | F | F | truly-unreachable | reference_planets — varna/guna/tattva/direction/metal static graha attrs held in reference_planets (truly-unreachable) |
| 59 | B-VIII | Nodal axis relations (every graha): nodal dispositor, placement in nod | T | T | T | T | reachable-surgical | chart_facts — VEN-RAH/VEN-KET nodal relations=20 each |
| 60 | B-VIII | Special-lagna relations (esp. for Lagna dossier): bhava/hora/ghati/var | T | T | T | T | reachable-surgical | chart_facts — special-lagna sphutas (PRANAPADA etc) + graha house-from |
| 61 | DISCOVERED | Birth-day muhurta + kalam window catalog: abhijit, brahma, choghadiya, | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: muhurta/choghadiya birth-day window catalog |
| 62 | DISCOVERED | Lal Kitab special-point system (lal_kitab_special_point) — a distinct  | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: lal_kitab=100 |
| 63 | DISCOVERED | Maharishi-tradition-specific sensitive point (maharsi_specific_point)  | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: maharishi sphutas (ATRI/BHARADWAJA_SPHUTA) |
| 64 | DISCOVERED | Chart-level composite/rollup analytics: center-of-gravity, chart clust | T | F | F | F | served-only-by-down-pipeline | bodha_cgm_nodes — DISCOVERED: graha centrality/COG in bodha_cgm_* (served-only-by-down-pipeline); composite_dispositor_strength IS in chart_facts but centrality metrics are not surgical |
| 65 | DISCOVERED | Cross-signal contradiction-pair flags and convergence-count tallies (c | T | F | F | F | truly-unreachable | bodha_contradictions — DISCOVERED: contradiction_pair table=0 rows for chart AND truly-unreachable; convergence_count only via msr |
| 66 | DISCOVERED | Karaka-bhava concordance, karaka/house-lord overlap flag, karakatva st | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: karaka_bhava_concordance=4350 |
| 67 | DISCOVERED | Midpoint positions (midpoint) — a Western/Uranian technique not presen | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: midpoint=1080 |
| 68 | DISCOVERED | Nakshatra co-gravity, co-tenancy, cross-ayanamsha comparison, and naks | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: nakshatra_cogravity/stats=45 |
| 69 | DISCOVERED | Swamsa (own-navamsha-derived sensitive point) position (swamsa_positio | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: swamsa_position=120 |
| 70 | DISCOVERED | Tajika sub-lord system: hadda (term) lord, triraashipathi (triplicity  | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: tajik_hadda/triraashipathi=1245 |
| 71 | DISCOVERED | Sensitive/esoteric sphuta point web beyond Bhrigu Bindu: avayogi, brah | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: sphuta web (AVAYOGI/BEEJA/mrityu-sphuta/pranapada/shiva) |
| 72 | DISCOVERED | Pranic strength per graha (pranic_strength_per_graha) — a distinct vit | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: pranic_strength_per_graha=5(VEN) |
| 73 | DISCOVERED | Tri-deva (Brahma/Vishnu/Shiva) role and strength per graha, Jaimini sy | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: graha_tri_deva_role_strength + jaimini_tri_deva |
| 74 | DISCOVERED | Shani special-period catalog beyond sade-sati/dhaiya: anumukha, ardha- | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: shani special-period catalog=1108 |
| 75 | DISCOVERED | Saturn-derived special point and Sun-derived upagraha beyond the named | T | T | T | T | reachable-surgical | chart_facts — DISCOVERED: saturn_derived=285 + sun-derived upagraha |

## Dossier rollup

| metric | value |
|---|---|
| facets_total (this chart) | 75 |
| held_in_db | 66 |
| wire_reachable (reachable-surgical) | 59 |
| reachable_in_2_calls | 59 |
| usable_form / composable | 58 |
| held_but_not_received | 8 |
| dossier_completeness_pct (usable/75) | 77.3% |
| dossier_verdict | PARTIAL |

## Findings (held-but-not-received + data-plane nonexistence; root-caused per Charter §2 taxonomy)

**F-VEN-1 — class 1 UNREACHABLE (served-only-by-down-pipeline).** Venus's structural×temporal
convergence (facet 52, the R-45 asset) is HELD: `kala_convergence` carries 6,484 windows for
chart 482012f1. Matrix channel = `served-only-by-down-pipeline` → no surgical MCP path serves
which of Venus's yogas/promises are temporally ripe (recent-past/near-future). A consuming LLM
cannot answer "is Venus's promise active now" over the wire. Suspected layer: MCP contract /
serving-query. Dedupe: extends R-45 (kala_activation empty-shell class) — the down-pipeline
gating of the whole kala convergence surface.

**F-VEN-2 — class 1 UNREACHABLE (served-only-by-down-pipeline).** Venus remedial priority
(facet 56, `bodha_rm_*`) and Venus graph-centrality / chart center-of-gravity (facet 64,
`bodha_cgm_nodes`, 5 Venus nodes) are held but channel = `served-only-by-down-pipeline`.
`chart_facts` gemstone/mantra = 0 rows — remedial exists ONLY in the down-pipeline RM surface.
Suspected layer: MCP contract. Dedupe: new (RM/CGM serving gap for entity dossier).

**F-VEN-3 — class 1 UNREACHABLE (truly-unreachable catalog).** Venus deity web (facet 55),
medical/avayava-dhatu mapping (facet 57), and static sambandha table varna/guna/tattva/
metal/direction (facet 58) are held only in L0 reference catalogs (`reference_nakshatra`,
`bg_medical_mappings`, `reference_planets`) whose matrix channel = `truly-unreachable`.
`chart_facts` deity/medical/remedial categories = 0. No tool joins the graha to its L0
attribute rows. Suspected layer: data plane / MCP contract (catalogs never fronted).

**F-VEN-4 — class 1 UNREACHABLE-BY-NONEXISTENCE (data plane).** Classical canon requires,
system never computed, for Venus: mrityu-bhaga (facet 13 — **R-47 anchor rediscovered**,
`%mrityu_bhaga%`=0), neecha-bhanga enumeration (facet 11, =0), papa/shubha kartari (facet 33,
=0), Sarvatobhadra-chakra vedha/latta (facet 35, =0), 22nd-drekkana/64th-navamsa/sarpa-drekkana
(facet 43, =0), pushkara bhaga/navamsha (facet 12, =0 — vargottama held but pushkara absent so
facet not composable), declination/celestial-latitude/kranti-shara (facet 6, =0). 7 sensitive-
degree/dignity facets absent from the data plane entirely. Suspected layer: data plane
(L-writer never wrote them). Dedupe: R-47 confirmed; 6 new nonexistence rows.

**F-VEN-5 — class 1 UNREACHABLE-BY-NONEXISTENCE / by-design (transit plane).** Venus transit-now
(facet 47, `transit_gochara`=0), double-transit Sa+Ju on natal points (facet 49), and live
eclipses/stations on Venus's natal degree (facet 51) are not stored as natal facts; the transit
engine (`bg_transit_engine`) is `truly-unreachable`. A dossier that must weigh current gochara
of Venus cannot. Suspected layer: architecture (no live-transit compute/serve path).

**F-VEN-6 — class 4 EMPTY SHELL / class 1.** Cross-signal contradiction-pair meta (facet 65)
resolves to `bodha_contradictions`, which returns **0 rows for this chart** and is
`truly-unreachable` by channel. The contradiction-pair analytic advertised for the dossier
returns nothing over any path. Suspected layer: L-writer + MCP contract.

**Rollup:** 66/75 held; 59 wire-reachable (surgical); 58 usable/composable; **8 held-but-not-
received** (facets 12,52,55,56,57,58,64,65). 9 further facets absent from the data plane
(nonexistence). Verdict PARTIAL: the STRUCTURAL Venus dossier (position, dignity, full shadbala/
ashtakavarga battery, all-five avastha, dispositor web, argala, karaka/arudha, vimshottari +
yogini/ashtottari dasha, varshaphal, and 14/15 DISCOVERED surfaces) composes at acharya depth
over reachable-surgical `chart_facts`/`chart_divisionals`/`chart_dashas`; the gaps are confined
to sensitive-degrees (data-plane nonexistence), live-transit, and the derived/esoteric served-
only surfaces (convergence, remedial, medical, deity, sambandha-catalog, graph-centrality).
Material but non-fatal → the dossier is composable with honest gaps, not UNCOMPOSABLE.

## §8 coverage self-declaration (this shard's row)
| surface | status | reason-if-deferred |
|---|---|---|
| Venus dossier — chart 482012f1 | audited | — |
