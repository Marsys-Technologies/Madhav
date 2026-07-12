# Lane 8 Shard Trace — Rahu dossier · chart 1c826d5a (last4 f75a)

resume_after_row_id: F01498
dossier_id: Rahu_1c826d5a
status: done
rows_total: 75 · rows_done: 75

SHAPER #3 applied: wire_reachable read from CONCEPT_RETRIEVABILITY_MATRIX channel (reachable-surgical=True; served-only-by-down-pipeline / truly-unreachable=False). Reachability NOT re-probed. held_in_db spot-checked via read-only SQL on chart_facts/chart_dashas for RAH_MEAN.

## Per-facet retrievability matrix

| # | facet_group | facet_text (abbrev) | held_in_db | wire_reachable | usable_form | channel | note |
|---|---|---|---|---|---|---|---|
| 1 | B-I Positional & coordinate | Sign, degree-minute-second; bhoga traversed | T | T | T | reachable-surgical | graha_position (RAH_MEAN): longitude_sidereal,sign,sign_lord — DMS/bhoga derivable |
| 2 | B-I Positional & coordinate | House by whole-sign AND bhava-chalit (Sripati/Placidus) — divergence f… | T | T | T | reachable-surgical | graha_position house_d1 + cusp_kp_lords (bhava-chalit); WS house held |
| 3 | B-I Positional & coordinate | Bhava madhya distance; bhava/rashi/nakshatra sandhi proximity; cusp du… | T | T | T | reachable-surgical | graha_gandanta(RAH) + near_sign/nakshatra_boundary_flag; cusp dual-flavor |
| 4 | B-I Positional & coordinate | Nakshatra, pada, nakshatra lord; KP star/sub/sub-sub | T | T | T | reachable-surgical | graha_nakshatra_join,graha_pada_join,graha_kp_lords(RAH 43 hits) |
| 5 | B-I Positional & coordinate | Navatara class from Moon AND from Lagna (janma/sampat/vipat/kshema/pra… | T | T | T | reachable-surgical | graha_tara_bala(RAH),tara_bala; navatara from Moon held (from-Lagna partial) |
| 6 | B-I Positional & coordinate | Declination (kranti), celestial latitude (shara); rise/set state (uday… | F | F | F | n/a-not-in-db | graha_position holds NO declination/celestial-latitude/rise-set/ayana fields — not computed |
| 7 | B-I Positional & coordinate | Speed, speed-ratio to mean, stationary proximity; retrograde/direct ph… | T | T | T | reachable-surgical | graha_position retrograde_flag=RAH always-retrograde (speed value absent, minor) |
| 8 | B-I Positional & coordinate | Ayana placement (uttarayana/dakshinayana); gola | F | F | F | n/a-not-in-db | no ayana/gola field in graha_position — not computed |
| 9 | B-II Dignity & sign-based | Exaltation/debilitation with exact deep-degree distance; ucha-abhilash… | T | T | T | reachable-surgical | graha_effective_dignity_modified_by_aspects(RAH); dignity held |
| 10 | B-II Dignity & sign-based | Mulatrikona / own / panchadha compound relation (natural × temporal) w… | T | T | T | reachable-surgical | graha_dignity_per_varga (D*_RAH_MEAN, 145 rows) |
| 11 | B-II Dignity & sign-based | Neecha-bhanga condition enumeration (all classical grounds, each with … | F | F | F | n/a-not-in-db | no neecha_bhanga enumeration category (Rahu debilitation-grounds not enumerated) |
| 12 | B-II Dignity & sign-based | Vargottama; pushkara bhaga; pushkara navamsha | T | T | T | reachable-surgical | vargottama_per_varga,graha_vargottama_amplification_factor (pushkara partial) |
| 13 | B-II Dignity & sign-based | Mrityu bhaga (per-sign degree check); yogatara proximity | F | F | F | n/a-not-in-db | mrityu-bhaga not computed per graha (R-47 anchor) — no mrityu_bhaga category |
| 14 | B-II Dignity & sign-based | Dagdha / tithi-shunya / mrityu rashi ownership effects | T | T | T | reachable-surgical | panchanga_tithi/nakshatra_shoonya_rashi held (dagdha partial) |
| 15 | B-II Dignity & sign-based | Sign-type flavor: chara/sthira/dvisvabhava, odd/even, tattva, prishtod… | T | T | T | reachable-surgical | graha_sign_attributes(RAH 10 rows) |
| 16 | B-III Strength systems (full | Shadbala complete tree: sthana (uccha/saptavargaja/ojayugma/kendradi/d… | T | T | T | reachable-surgical | graha_shadbala_sthana/kala/cheshta/dig/drik/naisargika/total(RAH) — nodes INCLUDED in shadbala (normative-band absent, minor) |
| 17 | B-III Strength systems (full | Ishta/Kashta phala | F | F | F | n/a-not-in-db | graha_ishta_phala/graha_kashta_phala: 7 grahas only (JUP..VEN), NODES EXCLUDED |
| 18 | B-III Strength systems (full | Vimsopaka (shadvarga/saptavarga/dashavarga/shodashavarga) + vaiseshika… | F | F | F | n/a-not-in-db | graha_vimsopaka_* + vimsopaka_bala_per_graha: 7 grahas only, NODES EXCLUDED |
| 19 | B-III Strength systems (full | Bhava bala of houses owned and occupied | T | T | T | reachable-surgical | house_bhava_bala_total occupied house held (Rahu owns no house — n/a) |
| 20 | B-III Strength systems (full | Pancha-vargiya bala (Tajaka context); dwadash-vargiya where computed | F | F | F | n/a-not-in-db | no pancha-vargiya bala category for Rahu (Tajaka strength) — not computed |
| 21 | B-III Strength systems (full | Ashtakavarga: BAV per-sign bindus + total; bindus in occupied sign; ka… | F | F | F | n/a-not-in-db | ashtakavarga_bindu/pinda: 7 grahas+lagna only, NODES EXCLUDED (classical AV) |
| 22 | B-III Strength systems (full | Sapta-vargaja dignity tally; own-varga counts | F | F | F | n/a-not-in-db | graha_saptavargaja_bala_component: 7 grahas only, NODES EXCLUDED |
| 23 | B-IV State & condition | Combustion with orb, applying/separating; graha yuddha (winner/loser, … | F | F | F | n/a-not-in-db | combustion/graha_yuddha: n/a for nodes (doctrinally correct absence) |
| 24 | B-IV State & condition | Grahan yuti (node + luminary eclipse association) | T | T | T | reachable-surgical | eclipse_proximity_natal(ECLIPSE_PROXIMITY_BIRTH) — grahan yuti, THE node fact |
| 25 | B-IV State & condition | Avastha sets — ALL FIVE: baladi (5), jagradadi (3), deepta-adi (9), la… | T | T | T | reachable-surgical | graha_avastha baladi/jagrad/deepta/lajjitadi/sayanadi ALL held for RAH |
| 26 | B-IV State & condition | Gandanta (rashi-nakshatra junction) proximity | T | T | T | reachable-surgical | graha_gandanta(RAH 5 rows) |
| 27 | B-IV State & condition | Upagraha contact: gulika, mandi, dhuma, vyatipata, parivesha, indracha… | T | T | T | reachable-surgical | upagraha_position,sensitive_point_gulika_mandi,sun_derived_upagraha |
| 28 | B-IV State & condition | Saham contacts (Tajaka sahams: punya, vidya, vivaha, mrityu, karma, …) | T | T | T | reachable-surgical | saham_position (30 RAH-contact hits) |
| 29 | B-V Relational web | Conjunctions (orb-aware); parashari aspects cast/received with sputa-d… | T | T | T | reachable-surgical | aspect_parashari_given(RAH 15),virupa_drishti(435),conjunction_within_orb |
| 30 | B-V Relational web | Rashi drishti (Jaimini) cast/received | T | T | T | reachable-surgical | aspect_jaimini (sign-keyed; Rahu-sign rashi drishti derivable) |
| 31 | B-V Relational web | Sambandha classification with each graha (exchange, mutual aspect, mut… | T | T | T | reachable-surgical | sambandha_grade (D*_..._RAH_MEAN, 1160 hits) |
| 32 | B-V Relational web | Dispositor web: sign dispositor, nakshatra dispositor, navamsha dispos… | T | T | T | reachable-surgical | graha_dispositor_chain,nakshatra_dispositor_chain,dispositor_tree(RAH) |
| 33 | B-V Relational web | Papa/shubha kartari on its position | F | F | F | n/a-not-in-db | no papa/shubha kartari category — not computed |
| 34 | B-V Relational web | Argala on its positions: shubha/papa/virodha, given and received | T | T | T | reachable-surgical | argala_natal_matrix,net_argala_per_varga,virodha_argala_natal_matrix |
| 35 | B-V Relational web | Vedha: Sarvatobhadra chakra vedhas on its nakshatra; nakshatra vedha p… | F | F | F | n/a-not-in-db | no Sarvatobhadra-chakra / latta natal vedha category — not computed |
| 36 | B-V Relational web | Tara bala from Moon (and chandra kriya/vela/avastha for the Moon dossi… | T | T | T | reachable-surgical | graha_tara_bala(RAH 15 rows) |
| 37 | B-VI Functional & role-based | Lordships from Lagna, Moon, Sun; functional benefic/malefic/neutral; y… | F | F | F | n/a-not-in-db | graha_functional_class_per_ascendant + graha_yoga_karaka_flag: 7 grahas only, NODES EXCLUDED; Rahu owns no sign |
| 38 | B-VI Functional & role-based | Kendradhipati dosha; badhaka/badhakesh status; maraka lordship/associa… | F | F | F | n/a-not-in-db | kendradhipati/badhaka/maraka not stored per-graha for Rahu (no lordship) |
| 39 | B-VI Functional & role-based | Naisargika karaka portfolio; sthira karaka; chara karaka (AK/AmK/BK/MK… | T | T | T | reachable-surgical | karaka_chara_position(RAH — Rahu IS a chara karaka),karakamsa_position(RAH) |
| 40 | B-VI Functional & role-based | Arudha involvement: AL lord, arudhas of owned houses, graha arudha pos… | T | T | T | reachable-surgical | arudha_pada,bhava_arudha (chart-level; graha-arudha partial) |
| 41 | B-VI Functional & role-based | Yoga participation — EVERY catalog family: raja (house-lord), dhana, m… | T | T | T | reachable-surgical | yoga_label + kala_sarpa_per_varga (Rahu is the kala-sarpa axis constituent) |
| 42 | B-VI Functional & role-based | Dosha participation: mangal (from lagna/Moon/Venus), shrapit, pitru, g… | T | T | T | reachable-surgical | dosha_label (5 RAH-membership hits) |
| 43 | B-VI Functional & role-based | 22nd drekkana (khareshwara) and 64th navamsha lord status; sarpa/pasha… | F | F | F | n/a-not-in-db | no 22nd-drekkana(khareshwara)/64th-navamsha/sarpa-drekkana category — not computed |
| 44 | B-VII Temporal (the graha as | Vimshottari lordship now (MD/AD/PD/sookshma/prana) + next windows at e… | T | T | T | reachable-surgical | chart_dashas vimshottari MD/AD/PD — Rahu is a Vimshottari lord |
| 45 | B-VII Temporal (the graha as | Dasha-quality context: dignity/house of each running lord FROM this gr… | T | T | T | reachable-surgical | chart_dashas lord_natal_house_d1/dignity_d1/shadbala_total held |
| 46 | B-VII Temporal (the graha as | Other dasha systems: yogini role; chara/narayana rashi-dasha periods o… | T | T | T | reachable-surgical | chart_dashas system_id: ashtottari,yogini,kalachakra,chara,mudda,naisargika,vimshottari(+kp) |
| 47 | B-VII Temporal (the graha as | Transit now: sign/house from natal Moon and Lagna, gochara quality + v… | F | F | F | n/a-not-in-db | transit-now not stored as natal fact (bg_transit_engine is live/reference) |
| 48 | B-VII Temporal (the graha as | Sade-sati/dhaiya involvement (Saturn dossier; Moon dossier as receiver… | T | T | T | reachable-surgical | sade_sati_phase/modifier_overlay (RAH rows present) |
| 49 | B-VII Temporal (the graha as | Double-transit (Saturn+Jupiter) participation on natal points | F | F | F | n/a-not-in-db | double-transit (Sa+Ju) participation not stored (transit-time, by design) |
| 50 | B-VII Temporal (the graha as | Varshaphal role: year-lord candidacy, muntha relation, tajaka aspect s… | T | T | T | reachable-surgical | aspect_tajik,tajik_hadda_lord,tajik_triraashipathi + mudda dasha (varshaphal, partial) |
| 51 | B-VII Temporal (the graha as | Upcoming/recent eclipses and stations on its natal degree | T | T | T | reachable-surgical | eclipse_proximity_natal (recent/upcoming eclipse on nodal axis) |
| 52 | B-VII Temporal (the graha as | Structural×temporal convergence: which of its yogas/promises are tempo… | T | F | F | served-only-by-down-pipeline | kala_convergence/kala_activation (structural×temporal convergence, R-45 asset) — served-only-by-down-pipeline: no surgical MCP path |
| 53 | B-VIII Esoteric, remedial &  | KP significator ladder roles (house-wise); ruling-planet membership | T | T | T | reachable-surgical | kp_cuspal_significators,kp_ruling_planets_natal(RAH),graha_kp_lords |
| 54 | B-VIII Esoteric, remedial &  | Nadi roles (jeeva/karma pairs, bhrigu-bindu relation) where computed | T | T | T | reachable-surgical | bhrigu_nadi_point,esoteric_point_bhrigu_bindu |
| 55 | B-VIII Esoteric, remedial &  | Deity web: nakshatra deity, adhidevata/pratyadhidevata; ishta-devata i… | T | T | T | reachable-surgical | nakshatra deity via graha_nakshatra_join (adhidevata/ishta-devata partial) |
| 56 | B-VIII Esoteric, remedial &  | Remedial mapping: gemstone, beeja/vedic mantra, yantra, dana, vrata-va… | T | F | F | served-only-by-down-pipeline | bodha_rm_remedy_prescriptions (Rahu remedial mapping) — served-only-by-down-pipeline |
| 57 | B-VIII Esoteric, remedial &  | Medical: avayava/body-part, dhatu, vata-pitta-kapha, disease significa… | T | F | F | truly-unreachable | bg_medical_mappings (avayava/dhatu/dosha/disease per graha) — truly-unreachable reference table |
| 58 | B-VIII Esoteric, remedial &  | Sambandha table: varna, guna, tattva, gender, direction, season, taste… | T | T | T | reachable-surgical | graha_sign_attributes + reference_planets (varna/guna/tattva) |
| 59 | B-VIII Esoteric, remedial &  | Nodal axis relations (every graha): nodal dispositor, placement in nod… | T | T | T | reachable-surgical | graha_dispositor_chain,nakshatra_dispositor (nodal-axis agency — Rahu itself) |
| 60 | B-VIII Esoteric, remedial &  | Special-lagna relations (esp. for Lagna dossier): bhava/hora/ghati/var… | T | T | T | reachable-surgical | special_lagna (chart-level; Rahu house-from-each derivable) |
| 61 | DISC:Panchanga/Muhurta windo | Birth-day muhurta + kalam window catalog: abhijit, brahma, choghadiya,… | T | T | T | reachable-surgical | panchanga_* incl panchanga_rahu_kalam(RAH); 24 panchanga families |
| 62 | DISC:Lal Kitab remedial syst | Lal Kitab special-point system (lal_kitab_special_point) — a distinct … | F | F | F | n/a-not-in-db | lal_kitab_special_point: PAKKA_GHAR for 7 grahas, NO Rahu-specific point |
| 63 | DISC:Maharishi-specific poin | Maharishi-tradition-specific sensitive point (maharsi_specific_point) … | T | T | T | reachable-surgical | maharsi_specific_point (chart-level sphutas; Rahu conjunction derivable) |
| 64 | DISC:Chart-level analytic ov | Chart-level composite/rollup analytics: center-of-gravity, chart clust… | T | T | T | reachable-surgical | graha_centrality,composite_dispositor_strength(RAH),graha_in_house_composite_strength(RAH),graha_special_state_rollup(RAH) |
| 65 | DISC:Contradiction/convergen | Cross-signal contradiction-pair flags and convergence-count tallies (c… | T | T | T | reachable-surgical | contradiction_pair,convergence_count(RAH 145 hits) — chart_facts, surgical |
| 66 | DISC:Karaka-bhava concordanc | Karaka-bhava concordance, karaka/house-lord overlap flag, karakatva st… | T | T | T | reachable-surgical | karaka_bhava_concordance,karaka_house_lord_overlap_flag,karakatva_strength_per_significance |
| 67 | DISC:Western midpoint techni | Midpoint positions (midpoint) — a Western/Uranian technique not presen… | T | T | T | reachable-surgical | midpoint(RAH 20 rows) |
| 68 | DISC:Nakshatra co-gravity/co | Nakshatra co-gravity, co-tenancy, cross-ayanamsha comparison, and naks… | T | T | T | reachable-surgical | nakshatra_cross_ayanamsha(RAH),nakshatra_cogravity/co_tenancy/statistics |
| 69 | DISC:Swamsa position | Swamsa (own-navamsha-derived sensitive point) position (swamsa_positio… | T | T | T | reachable-surgical | swamsa_position (chart-level; Rahu-in-swamsa derivable) |
| 70 | DISC:Tajika hadda/triraaship | Tajika sub-lord system: hadda (term) lord, triraashipathi (triplicity … | T | T | T | reachable-surgical | tajik_hadda_lord,tajik_triraashipathi,tajik_vargottama_specific (sign-term keyed; Rahu hadda derivable) |
| 71 | DISC:Esoteric sensitive-poin | Sensitive/esoteric sphuta point web beyond Bhrigu Bindu: avayogi, brah… | T | T | T | reachable-surgical | esoteric_point_* (avayogi/brahma/mrityu/pranapada/shiva/vishnu/yogi... chart-level sphutas) |
| 72 | DISC:Pranic strength system | Pranic strength per graha (pranic_strength_per_graha) — a distinct vit… | T | T | T | reachable-surgical | pranic_strength_per_graha(RAH) |
| 73 | DISC:Tri-deva role strength  | Tri-deva (Brahma/Vishnu/Shiva) role and strength per graha, Jaimini sy… | T | T | T | reachable-surgical | graha_tri_deva_role_strength(RAH),jaimini_tri_deva_role_per_graha(RAH) |
| 74 | DISC:Shani special-period ca | Shani special-period catalog beyond sade-sati/dhaiya: anumukha, ardha-… | F | F | F | n/a-not-in-db | shani special-period catalog (anumukha/ashtama/janma/kantaka...) is Saturn-relative, not a Rahu-dossier fact |
| 75 | DISC:Saturn/Sun-derived spec | Saturn-derived special point and Sun-derived upagraha beyond the named… | T | T | T | reachable-surgical | saturn_derived_point,sun_derived_upagraha (chart-level points) |

## Dossier rollup

- facets_total: **75** (60 floor + 15 discovered). NOTE: dispatch said "150 facets"; the actual Rahu·f75a dossier holds 75 ledger rows (brief §3 = 60-75/dossier). Completeness computed against the real denominator 75.
- held_in_db (true): **56/75**
- wire_reachable (true): **53/75**
- reachable_in_2_calls (true): **53/75** (all wire-reachable facets are single-table surgical ≤2 calls)
- usable_form (true): **53/75**
- held_but_not_received (held ∧ ¬received): **3** (F52 convergence, F56 remedial, F57 medical)
- dossier_completeness_pct = usable/total = 53/75 = **70.7%**
- **dossier_verdict: PARTIAL** — the core Rahu dossier (position, dignity, avastha ×5, aspects/drishti, dispositor web, yoga/dosha membership incl. kala-sarpa, Vimshottari lordship, KP ladder, nodal-axis agency, eclipse/grahan) is composable and surgically wire-reachable; but material depth gaps prevent SYNTHESIZABLE: the ENTIRE strength battery is node-excluded (ishta/kashta, vimsopaka, ashtakavarga, saptavargaja, functional-class/yogakaraka), mrityu-bhaga is uncomputed (R-47), and the structural×temporal convergence (R-45), remedial mapping, and medical significations are held-but-not-received over the wire.

## Findings (held-but-not-received + nonexistence; root-caused to Charter §2 classes)

### F52 · Structural×temporal convergence UNREACHABLE (held-but-not-received)
- failure_class: **1** · severity: **high** · suspected layer: serving-query/MCP-contract (down-pipeline exposure)
- evidence: R-45 rediscovery. kala_convergence/kala_activation hold Rahu's temporally-ripe yogas/promises (recent past + near future) but the matrix channel is served-only-by-down-pipeline — no surgical MCP path exposes them to a consuming LLM. Verbatim facet: "Structural×temporal convergence: which of its yogas/promises are temporally ripe, recent past + near future (the R-45 asset)". A Rahu MD-lord dossier cannot state WHEN Rahu's promises activate.

### F17/F18/F21/F22 · Node-excluded strength battery (UNREACHABLE-by-nonexistence)
- failure_class: **1** · severity: **high** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: DB evidence: graha_ishta_phala/graha_kashta_phala/graha_vimsopaka_{shadvarga,saptavarga,dasavarga,shodasavarga}/vimsopaka_bala_per_graha/graha_saptavargaja_bala_component each return exactly the 7 non-nodal grahas (JUP,MAR,MER,MOON,SAT,SUN,VEN) — zero Rahu rows; ashtakavarga_bindu/pinda keyed 7-graha+lagna, no RAH. The entire vimsopaka/ishta-kashta/ashtakavarga/saptavargaja strength dossier for Rahu is absent from the data plane (note: graha_shadbala_* DOES include Rahu — an asymmetric node-handling inconsistency).

### F13 · Mrityu-bhaga not computed per graha (R-47 rediscovery)
- failure_class: **1** · severity: **medium** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: No mrityu_bhaga fact_category exists; verbatim facet "Mrityu bhaga (per-sign degree check); yogatara proximity" is uncomputed for every graha incl. Rahu — direct rediscovery of anchor R-47 ("currently computed nowhere per graha").

### F37 · Functional class / yogakaraka node-exclusion (UNREACHABLE-by-nonexistence)
- failure_class: **1** · severity: **medium** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: graha_functional_class_per_ascendant and graha_yoga_karaka_flag both return 7 non-nodal grahas only; Rahu has no functional-benefic/malefic classification stored, so its lagna-dependent role portfolio cannot be composed.

### F56 · Remedial mapping held-but-not-received
- failure_class: **6** · severity: **medium** · suspected layer: serving-query/MCP-contract (down-pipeline exposure)
- evidence: Rahu remedial prescriptions live in bodha_rm_remedy_prescriptions, matrix channel served-only-by-down-pipeline — reachable only through the downstream pipeline, not by a consuming LLM's surgical call. Facet also asks "whether served remedial priority reflects its actual afflictions" (a class-9 governance question) — unanswerable when the mapping itself is not on the wire.

### F57 · Medical significations truly-unreachable
- failure_class: **1** · severity: **medium** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: avayava/dhatu/dosha/disease significations sit in bg_medical_mappings, matrix channel truly-unreachable — no MCP tool serves the L0 medical catalog chart-scoped for Rahu.

### F6/F8 · Celestial coordinates uncomputed (UNREACHABLE-by-nonexistence)
- failure_class: **1** · severity: **low** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: graha_position(RAH_MEAN) holds only longitude_sidereal/sign/sign_lord/nakshatra/nakshatra_lord/pada/house_d1/retrograde_flag/combustion_state — no declination(kranti), celestial latitude(shara), rise/set(udaya/asta), oriental/occidental, ayana or gola fields.

### F11/F33/F35/F43 · Assorted classical facets uncomputed (UNREACHABLE-by-nonexistence)
- failure_class: **1** · severity: **low** · suspected layer: data plane (writer node-handling / uncomputed)
- evidence: No categories exist for: neecha-bhanga grounds enumeration (F11), papa/shubha kartari (F33), Sarvatobhadra-chakra/latta natal vedha (F35), 22nd-drekkana(khareshwara)/64th-navamsha/sarpa-pasha-nigala drekkana (F43). Each is a canon-vs-system delta (Charter §2.1) for the Rahu dossier.
