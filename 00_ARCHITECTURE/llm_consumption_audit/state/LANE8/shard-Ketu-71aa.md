# Lane 8 shard — Ketu — chart 482012f1 (last4 71aa)

dossier_id: Ketu_482012f1
resume_after_row_id: F01489
status: done

## Chart-specific Ketu anchors (from DB spot-check)
- Ketu (fact_subject KET_MEAN): Scorpio, longitude ~229.03deg, nakshatra Jyeshtha pada 1, house_d1 = 8, sign_lord Mars, nakshatra_lord Mercury, retrograde_flag=direct, combustion_state=none.
- Held in chart_facts: full shadbala tree, ishta/kashta, vimsopaka, dignity-per-varga, avastha (all 5 sets), gandanta, dispositor chains, kp_lords, tara_bala, tri_deva, pranic strength, sign_attributes, karaka_chara, upagraha (incl UPAKETU).
- NOT held (nonexistence): ashtakavarga for Ketu = 0 rows (nodes excluded — expected); mrityu-bhaga per graha (R-47); declination/latitude/ayana-gola; neecha-bhanga (Ketu not debilitated); pancha-vargiya bala; grahan-yuti; jaimini rashi-drishti; argala/kartari-as-facts; 22nd/64th lord; transit-now/eclipse/double-transit; nadi; special-lagna; midpoint (explicitly Western, absent); Tajika sub-lord.
- Held but down-pipeline (kala_convergence=6484 rows; bodha_rm_remedy=135 rows; bodha_msr Ketu signals=1571).

## Grading rule (SHAPER #3 — consumed CONCEPT_RETRIEVABILITY_MATRIX, not re-probed)
- chart_facts / chart_divisionals / chart_dashas = channel reachable-surgical -> wire_reachable=T, usable=T.
- bodha_* / kala_* / phala_* / mimamsa_* = served-only-by-down-pipeline -> held-but-not-received (class 1).
- bg_* / reference_* / yoga_* L0 catalogs = truly-unreachable -> held-but-not-received (class 1).

## Rollup
- facets_total: 75
- held_in_db: 48
- wire_reachable: 39
- reachable_in_2_calls: 39
- usable_form (received): 39
- held_but_not_received: 9
- dossier_completeness_pct (usable/total): 52.0%
- dossier_verdict: PARTIAL

## Per-facet matrix
| # | facet_group | facet_text | held | wire | ≤2 | usable | channel | backing |
|---|---|---|---|---|---|---|---|---|
| 1 | B-I Positional & coo | Sign, degree-minute-second; bhoga traversed | T | T | T | T | reachable-surgical | chart_facts |
| 2 | B-I Positional & coo | House by whole-sign AND bhava-chalit (Sripati/Placidus) —  | T | T | T | T | reachable-surgical | chart_facts |
| 3 | B-I Positional & coo | Bhava madhya distance; bhava/rashi/nakshatra sandhi proxim | T | T | T | T | reachable-surgical | chart_facts |
| 4 | B-I Positional & coo | Nakshatra, pada, nakshatra lord; KP star/sub/sub-sub | T | T | T | T | reachable-surgical | chart_facts/graha_kp_lords |
| 5 | B-I Positional & coo | Navatara class from Moon AND from Lagna (janma/sampat/vipa | T | T | T | T | reachable-surgical | chart_facts/graha_tara_bala |
| 6 | B-I Positional & coo | Declination (kranti), celestial latitude (shara); rise/set | F | F | F | F | nonexistent(data-plane) | — |
| 7 | B-I Positional & coo | Speed, speed-ratio to mean, stationary proximity; retrogra | T | T | T | T | reachable-surgical | chart_facts |
| 8 | B-I Positional & coo | Ayana placement (uttarayana/dakshinayana); gola | F | F | F | F | nonexistent(data-plane) | — |
| 9 | B-II Dignity & sign- | Exaltation/debilitation with exact deep-degree distance; u | T | T | T | T | reachable-surgical | chart_facts/graha_effective_dignity |
| 10 | B-II Dignity & sign- | Mulatrikona / own / panchadha compound relation (natural × | T | T | T | T | reachable-surgical | chart_facts/graha_dignity_per_varga |
| 11 | B-II Dignity & sign- | Neecha-bhanga condition enumeration (all classical grounds | F | F | F | F | nonexistent(data-plane) | — |
| 12 | B-II Dignity & sign- | Vargottama; pushkara bhaga; pushkara navamsha | T | T | T | T | reachable-surgical | chart_divisionals |
| 13 | B-II Dignity & sign- | Mrityu bhaga (per-sign degree check); yogatara proximity | F | F | F | F | nonexistent(data-plane) | — |
| 14 | B-II Dignity & sign- | Dagdha / tithi-shunya / mrityu rashi ownership effects | F | F | F | F | nonexistent(data-plane) | — |
| 15 | B-II Dignity & sign- | Sign-type flavor: chara/sthira/dvisvabhava, odd/even, tatt | T | T | T | T | reachable-surgical | chart_facts/graha_sign_attributes |
| 16 | B-III Strength syste | Shadbala complete tree: sthana (uccha/saptavargaja/ojayugm | T | T | T | T | reachable-surgical | chart_facts/graha_shadbala_* |
| 17 | B-III Strength syste | Ishta/Kashta phala | T | T | T | T | reachable-surgical | chart_facts/graha_ishta_phala |
| 18 | B-III Strength syste | Vimsopaka (shadvarga/saptavarga/dashavarga/shodashavarga)  | T | T | T | T | reachable-surgical | chart_facts/graha_vimsopaka_* |
| 19 | B-III Strength syste | Bhava bala of houses owned and occupied | T | T | T | T | reachable-surgical | chart_facts/bhava_bala_positional |
| 20 | B-III Strength syste | Pancha-vargiya bala (Tajaka context); dwadash-vargiya wher | F | F | F | F | nonexistent(data-plane) | — |
| 21 | B-III Strength syste | Ashtakavarga: BAV per-sign bindus + total; bindus in occup | F | F | F | F | nonexistent(data-plane) | — |
| 22 | B-III Strength syste | Sapta-vargaja dignity tally; own-varga counts | T | T | T | T | reachable-surgical | chart_facts/graha_saptavargaja |
| 23 | B-IV State & conditi | Combustion with orb, applying/separating; graha yuddha (wi | T | T | T | T | reachable-surgical | chart_facts/graha_yuddha_per_varga |
| 24 | B-IV State & conditi | Grahan yuti (node + luminary eclipse association) | F | F | F | F | nonexistent(data-plane) | — |
| 25 | B-IV State & conditi | Avastha sets — ALL FIVE: baladi (5), jagradadi (3), deepta | T | T | T | T | reachable-surgical | chart_facts/graha_avastha_* |
| 26 | B-IV State & conditi | Gandanta (rashi-nakshatra junction) proximity | T | T | T | T | reachable-surgical | chart_facts/graha_gandanta |
| 27 | B-IV State & conditi | Upagraha contact: gulika, mandi, dhuma, vyatipata, parives | T | T | T | T | reachable-surgical | chart_facts/upagraha_position |
| 28 | B-IV State & conditi | Saham contacts (Tajaka sahams: punya, vidya, vivaha, mrity | T | T | T | T | reachable-surgical | chart_facts/saham_position |
| 29 | B-V Relational web | Conjunctions (orb-aware); parashari aspects cast/received  | T | T | T | T | reachable-surgical | chart_facts/aspect_parashari_given |
| 30 | B-V Relational web | Rashi drishti (Jaimini) cast/received | F | F | F | F | nonexistent(data-plane) | — |
| 31 | B-V Relational web | Sambandha classification with each graha (exchange, mutual | T | T | T | T | reachable-surgical | chart_facts/nakshatra_lord_relationship |
| 32 | B-V Relational web | Dispositor web: sign dispositor, nakshatra dispositor, nav | T | T | T | T | reachable-surgical | chart_facts/graha_dispositor_chain |
| 33 | B-V Relational web | Papa/shubha kartari on its position | T | F | F | F | served-only-by-down-pipeline | bodha_msr_signals |
| 34 | B-V Relational web | Argala on its positions: shubha/papa/virodha, given and re | F | F | F | F | nonexistent(data-plane) | — |
| 35 | B-V Relational web | Vedha: Sarvatobhadra chakra vedhas on its nakshatra; naksh | F | F | F | F | nonexistent(data-plane) | — |
| 36 | B-V Relational web | Tara bala from Moon (and chandra kriya/vela/avastha for th | T | T | T | T | reachable-surgical | chart_facts/graha_tara_bala |
| 37 | B-VI Functional & ro | Lordships from Lagna, Moon, Sun; functional benefic/malefi | T | T | T | T | reachable-surgical | chart_facts/graha_functional_class_per_ascendant |
| 38 | B-VI Functional & ro | Kendradhipati dosha; badhaka/badhakesh status; maraka lord | F | F | F | F | nonexistent(data-plane) | — |
| 39 | B-VI Functional & ro | Naisargika karaka portfolio; sthira karaka; chara karaka ( | T | T | T | T | reachable-surgical | chart_facts/karaka_chara_position |
| 40 | B-VI Functional & ro | Arudha involvement: AL lord, arudhas of owned houses, grah | F | F | F | F | nonexistent(data-plane) | — |
| 41 | B-VI Functional & ro | Yoga participation — EVERY catalog family: raja (house-lor | T | F | F | F | served-only-by-down-pipeline | bodha_msr_signals |
| 42 | B-VI Functional & ro | Dosha participation: mangal (from lagna/Moon/Venus), shrap | T | F | F | F | served-only-by-down-pipeline | bodha_msr_signals/brahma_dosha_catalog |
| 43 | B-VI Functional & ro | 22nd drekkana (khareshwara) and 64th navamsha lord status; | F | F | F | F | nonexistent(data-plane) | — |
| 44 | B-VII Temporal (the  | Vimshottari lordship now (MD/AD/PD/sookshma/prana) + next  | T | T | T | T | reachable-surgical | chart_dashas |
| 45 | B-VII Temporal (the  | Dasha-quality context: dignity/house of each running lord  | T | T | T | T | reachable-surgical | chart_dashas |
| 46 | B-VII Temporal (the  | Other dasha systems: yogini role; chara/narayana rashi-das | T | T | T | T | reachable-surgical | chart_dashas |
| 47 | B-VII Temporal (the  | Transit now: sign/house from natal Moon and Lagna, gochara | F | F | F | F | nonexistent(data-plane) | — |
| 48 | B-VII Temporal (the  | Sade-sati/dhaiya involvement (Saturn dossier; Moon dossier | F | F | F | F | nonexistent(data-plane) | — |
| 49 | B-VII Temporal (the  | Double-transit (Saturn+Jupiter) participation on natal poi | F | F | F | F | nonexistent(data-plane) | — |
| 50 | B-VII Temporal (the  | Varshaphal role: year-lord candidacy, muntha relation, taj | T | T | T | T | reachable-surgical | chart_dashas/varsha_year_lord |
| 51 | B-VII Temporal (the  | Upcoming/recent eclipses and stations on its natal degree | F | F | F | F | nonexistent(data-plane) | — |
| 52 | B-VII Temporal (the  | Structural×temporal convergence: which of its yogas/promis | T | F | F | F | served-only-by-down-pipeline | kala_convergence |
| 53 | B-VIII Esoteric, rem | KP significator ladder roles (house-wise); ruling-planet m | T | T | T | T | reachable-surgical | chart_facts/graha_kp_lords |
| 54 | B-VIII Esoteric, rem | Nadi roles (jeeva/karma pairs, bhrigu-bindu relation) wher | F | F | F | F | nonexistent(data-plane) | — |
| 55 | B-VIII Esoteric, rem | Deity web: nakshatra deity, adhidevata/pratyadhidevata; is | T | F | F | F | truly-unreachable | reference_nakshatra |
| 56 | B-VIII Esoteric, rem | Remedial mapping: gemstone, beeja/vedic mantra, yantra, da | T | F | F | F | served-only-by-down-pipeline | bodha_rm_remedy_prescriptions |
| 57 | B-VIII Esoteric, rem | Medical: avayava/body-part, dhatu, vata-pitta-kapha, disea | T | F | F | F | truly-unreachable | bg_medical_mappings |
| 58 | B-VIII Esoteric, rem | Sambandha table: varna, guna, tattva, gender, direction, s | T | F | F | F | truly-unreachable | reference_signs/planets |
| 59 | B-VIII Esoteric, rem | Nodal axis relations (every graha): nodal dispositor, plac | T | T | T | T | reachable-surgical | chart_facts/graha_dispositor_chain |
| 60 | B-VIII Esoteric, rem | Special-lagna relations (esp. for Lagna dossier): bhava/ho | F | F | F | F | nonexistent(data-plane) | — |
| 61 | DISCOVERED — Panchan | Birth-day muhurta + kalam window catalog: abhijit, brahma, | F | F | F | F | nonexistent(data-plane) | — |
| 62 | DISCOVERED — Lal Kit | Lal Kitab special-point system (lal_kitab_special_point) — | F | F | F | F | nonexistent(data-plane) | — |
| 63 | DISCOVERED — Maharis | Maharishi-tradition-specific sensitive point (maharsi_spec | F | F | F | F | nonexistent(data-plane) | — |
| 64 | DISCOVERED — Chart-l | Chart-level composite/rollup analytics: center-of-gravity, | F | F | F | F | nonexistent(data-plane) | — |
| 65 | DISCOVERED — Contrad | Cross-signal contradiction-pair flags and convergence-coun | T | F | F | F | served-only-by-down-pipeline | bodha_contradictions/bodha_convergence |
| 66 | DISCOVERED — Karaka- | Karaka-bhava concordance, karaka/house-lord overlap flag,  | T | T | T | T | reachable-surgical | chart_facts/graha_yoga_karaka_flag |
| 67 | DISCOVERED — Western | Midpoint positions (midpoint) — a Western/Uranian techniqu | F | F | F | F | nonexistent(data-plane) | — |
| 68 | DISCOVERED — Nakshat | Nakshatra co-gravity, co-tenancy, cross-ayanamsha comparis | T | T | T | T | reachable-surgical | chart_facts/nakshatra_cogravity |
| 69 | DISCOVERED — Swamsa  | Swamsa (own-navamsha-derived sensitive point) position (sw | T | T | T | T | reachable-surgical | chart_facts/swamsa_position |
| 70 | DISCOVERED — Tajika  | Tajika sub-lord system: hadda (term) lord, triraashipathi  | F | F | F | F | nonexistent(data-plane) | — |
| 71 | DISCOVERED — Esoteri | Sensitive/esoteric sphuta point web beyond Bhrigu Bindu: a | T | T | T | T | reachable-surgical | chart_facts/esoteric_point/aprakasha_position |
| 72 | DISCOVERED — Pranic  | Pranic strength per graha (pranic_strength_per_graha) — a  | T | T | T | T | reachable-surgical | chart_facts/pranic_strength_per_graha |
| 73 | DISCOVERED — Tri-dev | Tri-deva (Brahma/Vishnu/Shiva) role and strength per graha | T | T | T | T | reachable-surgical | chart_facts/graha_tri_deva_role_strength |
| 74 | DISCOVERED — Shani s | Shani special-period catalog beyond sade-sati/dhaiya: anum | F | F | F | F | nonexistent(data-plane) | — |
| 75 | DISCOVERED — Saturn/ | Saturn-derived special point and Sun-derived upagraha beyo | T | T | T | T | reachable-surgical | chart_facts/upagraha_position(UPAKETU) |

## Findings (held-but-not-received; each class 1 UNREACHABLE mapped to matrix channel)
1. [HIGH] Yoga participation (facet 41) — 1571 Ketu signals in bodha_msr_signals but channel=served-only-by-down-pipeline; no surgical MCP path a consuming LLM can call to get Ketu's yoga membership. class 1.
2. [HIGH] Dosha participation (facet 42) — bodha_msr_signals + brahma_dosha_catalog; served-only-by-down-pipeline. class 1.
3. [HIGH] Structural x temporal convergence (facet 52, R-45 anchor) — kala_convergence holds 6484 rows; served-only-by-down-pipeline. class 1.
4. [HIGH] Remedial mapping (facet 56) — bodha_rm_remedy_prescriptions holds 135 rows; served-only-by-down-pipeline. class 1.
5. [MED] Papa/shubha kartari (facet 33) — derived, only via bodha down-pipeline. class 1.
6. [MED] Cross-signal contradiction/convergence-count (facet 65) — bodha_contradictions truly-unreachable + bodha_convergence down-pipeline. class 1.
7. [MED] Deity web / medical / sambandha reference table (facets 55,57,58) — L0 catalogs (reference_nakshatra, bg_medical_mappings, reference_signs/planets) channel=truly-unreachable; per-Ketu attributes never surfaced over wire. class 1.
8. [MED] Mrityu-bhaga per graha (facet 13, R-47 anchor) — UNREACHABLE-by-nonexistence; computed nowhere for Ketu (data-plane gap). class 1.
