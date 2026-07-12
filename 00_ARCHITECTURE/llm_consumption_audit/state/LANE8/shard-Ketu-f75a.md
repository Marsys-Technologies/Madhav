# Lane 8 shard trace — Ketu dossier, chart 1c826d5a (last4 f75a)

- **entity:** Ketu
- **chart_id:** 1c826d5a-41cb-4450-b4dc-59d440e5f75a
- **facets in dossier (this chart):** 75 (60 Appendix-B floor + 15 discovered)
- **resume_after_row_id:** F01499 (all rows graded; shard done)
- **method:** SHAPER #3 — wire_reachable read from `CONCEPT_RETRIEVABILITY_MATRIX.jsonl` per backing table (NOT re-probed). held_in_db confirmed by read-only `mcp__postgres__query` spot-checks against `chart_facts` (fact_subject KET_MEAN / KETU / KET_MEAN_IN_HOUSE_* / D*_KET_MEAN / *-KET), `chart_dashas`, `kala_*`, `bodha_*`. usable_form graded per Charter §7.1 (RATIFIED v1.1).

## Channel map (from matrix — the wire_reachable authority)
- `chart_facts`, `chart_dashas`, `chart_divisionals` → **reachable-surgical** → wire_reachable=TRUE, ≤2 calls.
- `bodha_msr_signals` → **mixed** (32 surgical / 83 down-pipeline) — yoga/dosha family enumeration effectively drowned.
- `kala_*` (convergence, activation, bhavishya…), `phala_*`, `bodha_rm_*`, `bodha_convergence/cdlm/cgm` → **served-only-by-down-pipeline** → wire_reachable=FALSE.
- `bg_medical_mappings`, `bg_*` reference catalogs, `reference_planets`, `yoga_families` → **truly-unreachable** → wire_reachable=FALSE.

## Per-facet retrievability matrix (75 rows)

| row_id | # | facet_group | facet (short) | held | wire | ≤2 | usable | channel / note |
|---|---|---|---|---|---|---|---|---|
| F00019 | 1 | B-I | Sign, dms, bhoga | ✅ | ✅ | ✅ | ✅ | chart_facts graha_position · surgical |
| F00039 | 2 | B-I | House WS + bhava-chalit divergence | ✅ | ✅ | ✅ | ✅ | WS house held; chalit-divergence sub-facet not computed (partial) |
| F00059 | 3 | B-I | Bhava madhya / sandhi / cusp | ✅ | ✅ | ✅ | ✅ | boundary flags + in_house_composite · surgical |
| F00079 | 4 | B-I | Nakshatra/pada/lord + KP star/sub | ✅ | ✅ | ✅ | ✅ | nakshatra_join, pada_join, kp_lords · surgical |
| F00099 | 5 | B-I | Navatara from Moon AND Lagna | ✅ | ✅ | ✅ | ✅ | tara_bala; from-Lagna partial · surgical |
| F00119 | 6 | B-I | Declination/latitude/rise-set/oriental | ❌ | — | — | — | not computed (no kranti/shara category) — nonexistence |
| F00139 | 7 | B-I | Speed / retro phase geometry | ✅ | ✅ | ✅ | ✅ | graha_position motion · surgical (node always retro) |
| F00159 | 8 | B-I | Ayana / gola | ❌ | — | — | — | declination-based, not computed — nonexistence |
| F00179 | 9 | B-II | Exalt/debil deep-degree | ✅ | ✅ | ✅ | ✅ | dignity_per_varga + effective_dignity · surgical |
| F00199 | 10 | B-II | Mulatrikona/own/panchadha | ✅ | ✅ | ✅ | ✅ | dignity_per_varga + sign_attributes · surgical |
| F00219 | 11 | B-II | Neecha-bhanga enumeration | ❌ | — | — | — | no neecha/bhanga category — nonexistence |
| F00239 | 12 | B-II | Vargottama / pushkara | ✅ | ✅ | ✅ | ✅ | vargottama_per_varga + flag; pushkara partial · surgical |
| F00259 | 13 | B-II | Mrityu bhaga / yogatara | ❌ | — | — | — | **R-47** computed nowhere per graha — nonexistence |
| F00279 | 14 | B-II | Dagdha/tithi-shunya/mrityu rashi | ❌ | — | — | — | not computed per graha — nonexistence |
| F00299 | 15 | B-II | Sign-type flavor / tattva | ✅ | ✅ | ✅ | ✅ | graha_sign_attributes · surgical |
| F00319 | 16 | B-III | Shadbala complete tree | ✅ | ✅ | ✅ | ✅ | all shadbala_* present for Ketu; normative band partial · surgical |
| F00339 | 17 | B-III | Ishta/Kashta phala | ❌ | — | — | — | category exists but 0 rows for KETU (nodes excluded) |
| F00359 | 18 | B-III | Vimsopaka / vaiseshikamsha | ❌ | — | — | — | 0 rows for KETU |
| F00379 | 19 | B-III | Bhava bala owned/occupied | ✅ | ✅ | ✅ | ✅ | in_house_composite_strength (occupied); owns no house · surgical |
| F00399 | 20 | B-III | Pancha-vargiya (Tajaka) bala | ❌ | — | — | — | 0 rows for KETU (tajik) |
| F00419 | 21 | B-III | Ashtakavarga BAV/SAV/bindus | ❌ | — | — | — | nodes excluded from ashtakavarga — N/A |
| F00439 | 22 | B-III | Sapta-vargaja dignity tally | ✅ | ✅ | ✅ | ✅ | dignity_per_varga (145) · surgical |
| F00459 | 23 | B-IV | Combustion / graha yuddha | ❌ | — | — | — | nodes do not combust/war — N/A |
| F00479 | 24 | B-IV | Grahan yuti (eclipse assoc.) | ❌ | — | — | — | not computed as category (node-relevant) — nonexistence |
| F00499 | 25 | B-IV | Avastha ALL FIVE | ✅ | ✅ | ✅ | ✅ | baladi/jagrad/deepta/lajjita/sayana all present · surgical |
| F00519 | 26 | B-IV | Gandanta proximity | ✅ | ✅ | ✅ | ✅ | graha_gandanta · surgical |
| F00539 | 27 | B-IV | Upagraha contact | ✅ | ✅ | ✅ | ✅ | upagraha_position (35) · surgical |
| F00559 | 28 | B-IV | Saham contacts (Tajaka) | ❌ | — | — | — | saham↔Ketu contact not computed — nonexistence |
| F00579 | 29 | B-V | Conjunctions + parashari aspects sputa | ✅ | ✅ | ✅ | ✅ | conjunction + aspect_parashari + virupa_drishti · surgical |
| F00599 | 30 | B-V | Rashi drishti (Jaimini) | ❌ | — | — | — | no rashi_drishti/jaimini-drishti category — nonexistence |
| F00619 | 31 | B-V | Sambandha classification each graha | ✅ | ✅ | ✅ | ✅ | sambandha_grade (1160) · surgical |
| F00639 | 32 | B-V | Dispositor web full chain | ✅ | ✅ | ✅ | ✅ | dispositor_tree + chain_per_varga + nakshatra_dispositor_chain · surgical |
| F00659 | 33 | B-V | Papa/shubha kartari | ❌ | — | — | — | no kartari category — nonexistence |
| F00679 | 34 | B-V | Argala given/received | ✅ | ✅ | ✅ | ✅ | argala held (house-keyed); Ketu's house → argala in ≤2 calls · surgical |
| F00699 | 35 | B-V | Vedha (SBC / latta) | ❌ | — | — | — | not computed — nonexistence |
| F00719 | 36 | B-V | Tara bala from Moon | ✅ | ✅ | ✅ | ✅ | tara_bala + graha_tara_bala · surgical |
| F00739 | 37 | B-VI | Lordships/functional/yogakaraka | ✅ | ✅ | ✅ | ✅ | significator_path + sign_attributes (node owns no sign) · surgical |
| F00759 | 38 | B-VI | Kendradhipati/badhaka/maraka | ❌ | — | — | — | not computed as category — nonexistence |
| F00779 | 39 | B-VI | Naisargika + chara karaka | ✅ | ✅ | ✅ | ✅ | chara_karaka dasha system + karaka_role · surgical |
| F00799 | 40 | B-VI | Arudha involvement | ✅ | ✅ | ✅ | ✅ | arudhas held (house-keyed); graha arudha via ≤2 calls · surgical |
| F00819 | 41 | B-VI | **Yoga participation — every family** | ✅ | ✅ | ➖ | ❌ | msr_signals (mixed 32/83); **DROWNED** in 66,747 signals — family enumeration not findable → **FINDING class 7** |
| F00839 | 42 | B-VI | **Dosha participation (incl. kala-sarpa)** | ✅ | ✅ | ➖ | ❌ | Ketu core to kala-sarpa; msr mixed + brahma_dosha_catalog down-pipeline; **DROWNED** → **FINDING class 7** |
| F00859 | 43 | B-VI | 22nd drekkana / 64th navamsha lord | ❌ | — | — | — | no khareshwara/64th-navamsha category — nonexistence |
| F00879 | 44 | B-VII | Vimshottari lord now + windows | ✅ | ✅ | ✅ | ✅ | chart_dashas; Ketu is a lord (13,457 rows) · surgical |
| F00899 | 45 | B-VII | Dasha-quality context | ✅ | ✅ | ✅ | ✅ | chart_dashas lord_natal_house/dignity/shadbala cols · surgical |
| F00919 | 46 | B-VII | Other dasha systems | ✅ | ✅ | ✅ | ✅ | yogini/chara/ashtottari/kalachakra/mudda in chart_dashas · surgical |
| F00939 | 47 | B-VII | Transit now | ❌ | — | — | — | transit not stored (runtime); bg_transit_engine truly-unreachable |
| F00959 | 48 | B-VII | Sade-sati / dhaiya | ❌ | — | — | — | Saturn/Moon-specific — N/A for Ketu |
| F00979 | 49 | B-VII | Double-transit participation | ❌ | — | — | — | transit-based, not stored |
| F00999 | 50 | B-VII | Varshaphal year-lord/muntha/tajaka | ✅ | ✅ | ✅ | ✅ | mudda dasha + varsha_year_lord col; tajaka set partial · surgical |
| F01019 | 51 | B-VII | Eclipses/stations on natal degree | ❌ | — | — | — | runtime ephemeris, not stored |
| F01039 | 52 | B-VII | **Structural×temporal convergence (R-45)** | ✅ | ❌ | ❌ | ❌ | kala_convergence (2,959) + kala_activation HELD but **served-only-by-down-pipeline** → **FINDING class 1** (R-45 anchor) |
| F01059 | 53 | B-VIII | KP significator ladder / ruling planet | ✅ | ✅ | ✅ | ✅ | significator_path (80) + kp_lords · surgical |
| F01079 | 54 | B-VIII | Nadi roles / bhrigu-bindu | ❌ | — | — | — | not computed for Ketu subject — nonexistence |
| F01099 | 55 | B-VIII | Deity web (nakshatra deity/adhidevata) | ✅ | ✅ | ✅ | ✅ | nakshatra deity via graha_nakshatra_join; ishta-devata path partial · surgical |
| F01119 | 56 | B-VIII | **Remedial mapping + affliction-priority** | ✅ | ❌ | ❌ | ❌ | chart-specific priority in bodha_rm_* **served-only-by-down-pipeline** → **FINDING class 1** (generic corpus reachable; the afflictions-priority ask is not) |
| F01139 | 57 | B-VIII | **Medical (avayava/dhatu/dosha)** | ✅ | ❌ | ❌ | ❌ | bg_medical_mappings **truly-unreachable** → **FINDING class 1** |
| F01159 | 58 | B-VIII | **Sambandha table (varna/guna/metal…)** | ✅ | ❌ | ❌ | ❌ | graha-level attributes in reference_planets **truly-unreachable** → **FINDING class 1** (sign-tattva reachable; graha sambandha not) |
| F01179 | 59 | B-VIII | Nodal axis relations | ✅ | ✅ | ✅ | ✅ | dispositor_tree + node-star placement; agency-rule partial · surgical |
| F01199 | 60 | B-VIII | Special-lagna relations | ❌ | — | — | — | special-lagna categories exist chart-wide but 0 for KETU subject |
| F01219 | 61 | DISC panchanga | Panchanga/muhurta window catalog | ✅ | ✅ | ✅ | ✅ | panchanga_* in chart_facts (chart context) · surgical |
| F01239 | 62 | DISC lal-kitab | Lal Kitab special point | ❌ | — | — | — | chart-level point, 0 for KETU subject — not a Ketu attribute |
| F01259 | 63 | DISC maharsi | Maharishi-specific point | ❌ | — | — | — | chart-level, 0 for KETU subject |
| F01279 | 64 | DISC composite | Chart-level composite/rollup analytics | ✅ | ✅ | ✅ | ✅ | graha_centrality/composite_dispositor/in_house_composite/special_state_rollup for Ketu · surgical |
| F01299 | 65 | DISC meta | Contradiction / convergence-count meta | ✅ | ✅ | ✅ | ✅ | convergence_count (145) for Ketu · surgical; contradiction_pair (bodha_contradictions) unreachable — partial |
| F01319 | 66 | DISC karaka-concord | Karaka-bhava concordance/overlap | ❌ | — | — | — | 0 for KETU (computed for 7 grahas, not nodes) |
| F01339 | 67 | DISC midpoint | Midpoint positions | ✅ | ✅ | ✅ | ✅ | midpoint (200) for Ketu · surgical |
| F01359 | 68 | DISC nakshatra-stats | Nakshatra co-gravity/co-tenancy/cross-ayan | ✅ | ✅ | ✅ | ✅ | nakshatra_cross_ayanamsha (2) for Ketu; cogravity/stats chart-level — partial · surgical |
| F01379 | 69 | DISC swamsa | Swamsa position | ❌ | — | — | — | single chart point, 0 for KETU — not per-graha |
| F01399 | 70 | DISC tajik | Tajika hadda/triraashipathi/vargottama | ❌ | — | — | — | 0 for KETU subject |
| F01419 | 71 | DISC esoteric-sphuta | Esoteric sphuta web | ❌ | — | — | — | chart-level sensitive points, 0 for KETU subject |
| F01439 | 72 | DISC pranic | Pranic strength per graha | ✅ | ✅ | ✅ | ✅ | pranic_strength_per_graha (5) for Ketu · surgical |
| F01459 | 73 | DISC tri-deva | Tri-deva role strength (Jaimini) | ✅ | ✅ | ✅ | ✅ | graha_tri_deva_role_strength + jaimini_tri_deva for Ketu · surgical |
| F01479 | 74 | DISC shani-period | Shani special-period catalog | ❌ | — | — | — | Saturn-specific — N/A for Ketu |
| F01499 | 75 | DISC sat/sun-points | Saturn/Sun-derived special points | ❌ | — | — | — | not a Ketu attribute — N/A |

Legend: ✅=true · ❌=false · ➖=partial/no · —=N/A (facet not held, so downstream columns void)

## Dossier rollup

| metric | value |
|---|---|
| facets_total (this chart) | 75 |
| held_in_db | 44 |
| wire_reachable | 40 |
| reachable_in_2_calls | 40 |
| usable_form | 38 |
| held_but_not_received | 6 |
| not held (nonexistence / node-N/A) | 31 |
| dossier_completeness_pct (usable/75) | 50.7% |
| **dossier_verdict** | **PARTIAL** |

**Verdict rationale (PARTIAL).** Ketu's structural spine is fully composable at acharya depth over the wire: position, dignity-per-varga, complete shadbala, all five avastha sets, gandanta, upagraha contact, orb-aware conjunctions + parashari drishti, the full dispositor web, sambandha grades, Vimshottari + 7 other dasha systems with Ketu as time-lord, chara/naisargika karaka, KP significator ladder, and the composite/centrality/midpoint/pranic/tri-deva analytic overlays — every one reachable-surgical in ≤2 calls. But six MATERIAL depth facets are held-but-not-received, including the two most chart-defining for a node: **dosha participation (kala-sarpa — Ketu is a defining terminus)** and **yoga participation** are drowned in 66,747 msr signals, and **structural×temporal convergence (R-45)** is computed (2,959 rows) yet served only into a down-pipeline consumer, never on the wire. Because these gaps hit the parts of Ketu's dossier an acharya would weigh most heavily (which of Ketu's promises are temporally ripe; what afflictions its remedies must target), the dossier is composable but with material gaps — PARTIAL, not SYNTHESIZABLE. It is not UNCOMPOSABLE: the deterministic spine is intact and richly reachable.

Of the 31 not-held: most are node-inapplicable-or-uncomputed (ashtakavarga/ishta-kashta/vimsopaka/combustion/graha-yuddha exclude nodes; sade-sati/transit are Saturn/runtime), and a cluster are genuine UNREACHABLE-by-nonexistence data-plane gaps present in the classical canon: **mrityu-bhaga (R-47), neecha-bhanga enumeration, rashi-drishti (Jaimini), papa/shubha kartari, argala-as-category, vedha (SBC/latta), kendradhipati/badhaka/maraka, 22nd-drekkana/64th-navamsha, declination/ayana.** These are §2.1 UNREACHABLE-by-nonexistence findings for the concept-completeness register (not held-but-not-received; noted here, not double-counted as this shard's 6).

## Findings (held-but-not-received — Charter §3 schema; root-caused to §2 class)

All six are `held_in_db=true` with wire/usable failing. Suspected layer noted for the planner. Dedupe: R-45 and R-47 are anchor rows (R-45 re-discovered here as class 1; R-47 surfaced as nonexistence, not counted in the 6). The four remaining (yoga/dosha drowning, remedial-priority, medical, sambandha-table) are checked as candidate-new against R-37..R-48 — closest anchor is R-37 (discoveries top-K collapse) for the drowning pair; distinct enough to append as new rows keyed to the Ketu depth axis.

| # | facet (row_id) | class | severity | suspected layer | evidence |
|---|---|---|---|---|---|
| 1 | Dosha participation incl. kala-sarpa (F00839) | 7 DROWNED | high | ranking/form (msr serving) | `bodha_msr_signals` = 66,747 rows this chart; matrix channel mixed (32 surgical / 83 down-pipeline); no surgical path returns Ketu's dosha-family membership as a decisive top-K — the chart-defining kala-sarpa terminus is buried, not findable. |
| 2 | Yoga participation — every family (F00819) | 7 DROWNED | high | ranking/form (msr serving) | Same 66,747-signal surface; comprehensive per-family yoga enumeration for Ketu is not retrievable as a ranked, deduplicated set — surgical slice returns fragments only. |
| 3 | Structural×temporal convergence (F01039) | 1 UNREACHABLE | high | retrieval plane / MCP contract | `kala_convergence` (2,959 rows) + `kala_activation` HELD for chart; matrix channel = **served-only-by-down-pipeline** — no MCP tool serves Ketu's temporally-ripe promises to a consuming LLM. R-45 anchor re-discovered. |
| 4 | Remedial mapping + affliction-priority (F01119) | 1 UNREACHABLE | medium | retrieval plane | `bodha_rm_remedy_prescriptions/_dosha_remedy_bundles` = served-only-by-down-pipeline; the facet's specific ask (does served remedial priority reflect Ketu's actual afflictions) is not wire-reachable — only the generic `brahma_remedy_corpus` catalog is surgical. |
| 5 | Medical significations (F01139) | 1 UNREACHABLE | medium | data plane serving (L0 catalog) | `bg_medical_mappings` matrix channel = **truly-unreachable**; Ketu's avayava/dhatu/dosha/disease significations exist in the L0 catalog but no tool serves them. |
| 6 | Graha sambandha table varna/guna/metal (F01159) | 1 UNREACHABLE | low-med | data plane serving (L0 catalog) | Graha-level sambandha attributes live in `reference_planets` (matrix channel **truly-unreachable**); sign-tattva is reachable via `graha_sign_attributes` but Ketu's own varna/guna/metal/grain/color are not. |

## Coverage self-declaration
- Ketu dossier — chart 1c826d5a: **audited** (75/75 rows graded).
- Appendix B floor (60 groups): audited for Ketu.
- Discovered facets (15): audited; 8 held for Ketu-subject, 7 are chart-level points not keyed to Ketu (marked not-held, N/A).
