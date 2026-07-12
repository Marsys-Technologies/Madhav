# LANE 9 — LLM Consumption Audit

<!-- RESUME: 9a complete — nodes_audited=42 of 42; 9b complete — fact_category_done=204 of 204 -->

## 9a — CGM graph leverage audit

**Lane:** LANE9a-structural
**nodes_total:** 42
**nodes_audited:** 42
**findings_count:** 108

### Three-axis rollup

**Axis 1 — Structural verdict spread (42 nodes):**

| verdict | count |
|---|---|
| COMPLETE | 0 |
| PARTIAL | 0 |
| THIN | 18 |
| ISOLATED | 24 |

**Axis 2 — Graph reach counts (across all audited nodes):**

| reaches | count |
|---|---|
| bhava_lordship | 0 |
| yoga | 0 |
| temporal | 0 |

**Axis 3 — Consumption / leverage verdicts:**

- **Consumption: FAIL** (per LCA-1) — no node reaches bhava-lordship, yoga, or temporal context.
- **Leverage: FAIL** (per LCA-2) — the graph provides zero incremental reach beyond graha↔graha and graha↔domain adjacency; every bhava node is isolated.

### Headline finding

**The CGM graph is graha-centric.** All relationship-bearing edges wire only graha↔graha (argala, aspect, dispositor) and a handful of graha↔domain (dosha_domain) edges. Consequently:

- **bhava-lordship reach = 0.** All 60 bhava nodes participate in ZERO edges (ISOLATED) versus graha 45/45 connected. No dispositor/lordship/occupant/aspect relationship to any house is reachable via graph walk. Census (chart 1c826d5a): edge endpoints = graha(1031) + domain(15), zero bhava. Chart 482012f1: 534 edges, endpoints = graha(1053) + domain(15), zero bhava.
- **yoga reach = 0.** Yogas are not first-class graph nodes — `bodha_cgm_nodes` node_types = graha/bhava/domain only, with no `node_type='yoga'` despite 140 signal_type_class=yoga MSR signals existing. Yoga membership is structurally unreachable by traversal.
- **temporal reach = 0.** `active_dasha_periods_jsonb` is never populated on any edge (0/N across every graha node); no temporal edge_type exists. Every bhava-centric or time-indexed question is unreachable via the CGM graph despite the underlying L1 facts existing.

Systemic pattern: 24 ISOLATED nodes (all bhava, both charts) + 18 THIN nodes (graha nodes that reach only graha, or graha+domain, neighbors). Not one node reaches a house-lord chain, a yoga, or a dasha hook.

### HIGH / CRITICAL findings (with verbatim evidence)

1. **[HIGH · failure_class 1]** `bhava:1:f75a` — Bhava-1 node exists in bodha_cgm_nodes but participates in ZERO edges; no dispositor/lordship/yoga/temporal relationship reachable via graph walk (ISOLATED). Systemic: all 60 bhava nodes have 0 edges vs graha 45/45 connected.
   - Evidence: `recipe edge_count=0 for node a3307634; census: node_type=bhava 60 nodes / 0 with edges; graha 45/45; domain 15/35`

2. **[HIGH · failure_class 1]** `bhava:2:f75a` — Bhava-2 node (c3726751) has ZERO edges; fully ISOLATED from the CGM edge graph — no reachable dispositor/lordship/yoga/temporal relationship. Systemic bhava-orphaning.
   - Evidence: `recipe edge_count=0 for c3726751; census bhava 60/0-with-edges vs graha 45/45`

3. **[HIGH · failure_class 1]** `bhava:3:f75a` — Bhava-3 node (ca4161e1) has ZERO edges; fully ISOLATED — systemic bhava-orphaning in the CGM graph.
   - Evidence: `recipe edge_count=0 for ca4161e1; census bhava 60/0 vs graha 45/45; domain 15/35`

4. **[HIGH · failure_class 1]** `bhava:10:f75a` — Bhava-10 node (311b304c) has ZERO edges; fully ISOLATED — no reachable dispositor/lordship/yoga/temporal. Systemic bhava-orphaning.
   - Evidence: `recipe edge_count=0 for 311b304c; census bhava 60/0 vs graha 45/45`

5. **[HIGH · failure_class 1]** `bhava:11:f75a` — Bhava-11 node (0ab37132) has ZERO edges; fully ISOLATED from the CGM edge graph. Systemic bhava-orphaning.
   - Evidence: `recipe edge_count=0 for 0ab37132; census bhava 60/0-with-edges vs graha 45/45`

6. **[HIGH · failure_class 1]** `bhava:12:f75a` — Bhava-12 node (7b290bb1) has ZERO edges; fully ISOLATED — systemic bhava-orphaning; no dispositor/lordship/yoga/temporal reachable.
   - Evidence: `recipe edge_count=0 for 7b290bb1; census bhava 60/0 vs graha 45/45; domain 15/35`

7. **[HIGH · failure_class 1]** `bhava:4:f75a` — Bhava-4 CGM node is ISOLATED (0 incident edges) — graph yields no dispositor, bhava-lord, occupant, aspect, or temporal-hook data for this node.
   - Evidence: `edge_count=0, edge_types=null, cited=null, msr_backed=null (verbatim recipe result); systemic cross-check: 0/60 bhava nodes have edges vs graha 45/45 = 1031 edges`

8. **[HIGH · failure_class 1]** `bhava:5:f75a` — Bhava-5 CGM node is ISOLATED (0 incident edges) — no dispositor/lord/occupant/aspect/temporal edge.
   - Evidence: `edge_count=0, edge_types=null (verbatim); systemic 0/60 bhava nodes edged`

9. **[HIGH · failure_class 1]** `bhava:6:f75a` — Bhava-6 CGM node is ISOLATED (0 incident edges) — no dispositor/lord/occupant/aspect/temporal edge.
   - Evidence: `edge_count=0, edge_types=null (verbatim); systemic 0/60 bhava nodes edged`

10. **[HIGH · failure_class 1]** `bhava:7:f75a` — Bhava-7 CGM node is ISOLATED (0 incident edges) — chart-defining marriage/partnership house with empty graph neighborhood; no dispositor/lord/occupant/aspect/temporal edge.
    - Evidence: `edge_count=0, edge_types=null (verbatim); systemic 0/60 bhava nodes edged vs graha 1031 edges`

11. **[HIGH · failure_class 1]** `bhava:8:f75a` — Bhava-8 CGM node is ISOLATED (0 incident edges) — longevity/upheaval house with empty graph neighborhood.
    - Evidence: `edge_count=0, edge_types=null (verbatim); systemic 0/60 bhava nodes edged`

12. **[HIGH · failure_class 1]** `bhava:9:f75a` — Bhava-9 CGM node is ISOLATED (0 incident edges) — dharma/fortune house with empty graph neighborhood.
    - Evidence: `edge_count=0, edge_types=null (verbatim); systemic 0/60 bhava nodes edged`

13. **[HIGH · failure_class 1]** `graha:Jupiter:f75a` — Jupiter node reaches no bhava node — bhava-lordship context structurally unreachable via graph traversal.
    - Evidence: `neighbor_types='graha' only over 26 edges (edge_types=argala,aspect,dispositor); zero bhava neighbors`

14. **[HIGH · failure_class 1]** `graha:Jupiter:f75a` — Yogas are not first-class graph nodes; Jupiter cannot reach any yoga.
    - Evidence: `0 yoga neighbors; bodha_cgm_nodes has no node_type='yoga'`

15. **[HIGH · failure_class 4]** `graha:Jupiter:f75a` — Temporal hooks absent — active_dasha_periods_jsonb never populated on Jupiter's edges.
    - Evidence: `temporal populated = 0/26; no temporal edge_type`

16. **[HIGH · failure_class 1]** `graha:Ketu:f75a` — Ketu node reaches no bhava node — bhava-lordship unreachable.
    - Evidence: `neighbor_types='graha' only over 19 edges; zero bhava neighbors`

17. **[HIGH · failure_class 1]** `graha:Ketu:f75a` — Ketu reaches no yoga; yogas not first-class nodes.
    - Evidence: `0 yoga neighbors; no node_type='yoga' in bodha_cgm_nodes`

18. **[HIGH · failure_class 4]** `graha:Ketu:f75a` — Temporal hooks absent on Ketu's edges.
    - Evidence: `temporal populated = 0/19; no temporal edge_type`

19. **[HIGH · failure_class 1]** `graha:Mars:f75a` — Mars node reaches no bhava node — bhava-lordship unreachable.
    - Evidence: `neighbor_types='graha' only over 24 edges; zero bhava neighbors`

20. **[HIGH · failure_class 1]** `graha:Mars:f75a` — Mars reaches no yoga; yogas not first-class nodes.
    - Evidence: `0 yoga neighbors; no node_type='yoga'`

21. **[HIGH · failure_class 4]** `graha:Mars:f75a` — Temporal hooks absent on Mars's edges.
    - Evidence: `temporal populated = 0/24; no temporal edge_type`

22. **[HIGH · failure_class 1]** `graha:Mercury:f75a` — Mercury node reaches no bhava node — directly fails the plan's own probe (Mercury reaches dispositor YES, bhava lords NO).
    - Evidence: `neighbor_types='graha' only over 23 edges; zero bhava neighbors`

23. **[HIGH · failure_class 1]** `graha:Mercury:f75a` — Mercury reaches no yoga; yogas not first-class nodes — fails plan probe (yogas NO).
    - Evidence: `0 yoga neighbors; no node_type='yoga'`

24. **[HIGH · failure_class 4]** `graha:Mercury:f75a` — Temporal hooks absent on Mercury's edges — fails plan probe (temporal hooks NO).
    - Evidence: `temporal populated = 0/23; no temporal edge_type`

25. **[HIGH · failure_class 1]** `graha:Moon:f75a` — Moon node reaches domain neighbor (dosha_domain edge) but no bhava node — bhava-lordship still unreachable.
    - Evidence: `neighbor_types='domain,graha' (edge_types include dosha_domain); no bhava neighbor`

26. **[HIGH · failure_class 1]** `graha:Moon:f75a` — Moon reaches no yoga; yogas not first-class nodes.
    - Evidence: `0 yoga neighbors; no node_type='yoga'`

27. **[HIGH · failure_class 4]** `graha:Moon:f75a` — Temporal hooks absent on Moon's edges.
    - Evidence: `temporal populated = 0/23; no temporal edge_type`

28. **[HIGH · failure_class 1]** `graha:Rahu:f75a` — Rahu node reaches no bhava node — bhava-lordship unreachable.
    - Evidence: `neighbor_types='graha' only over 23 edges; zero bhava neighbors`

29. **[HIGH · failure_class 1]** `graha:Rahu:f75a` — Rahu reaches no yoga; yogas not first-class nodes.
    - Evidence: `0 yoga neighbors; no node_type='yoga'`

30. **[HIGH · failure_class 4]** `graha:Rahu:f75a` — Temporal hooks absent on Rahu's edges.
    - Evidence: `temporal populated = 0/23; no temporal edge_type`

31. **[HIGH · failure_class 1]** `graha:Saturn:875a` — Saturn graha node reaches no bhava lordship — CGM graph never wires graha↔bhava edges (chart-wide 0 bhava endpoints).
    - Evidence: `24 edges, neighbor node_types = {graha} only; chart 1c826d5a edge endpoints = graha(1031)+domain(15), zero bhava`

32. **[HIGH · failure_class 1]** `graha:Saturn:875a` — Yoga membership structurally unreachable — 140 signal_type_class=yoga MSR signals exist but no node_type=yoga in bodha_cgm_nodes.
    - Evidence: `bodha_cgm_nodes node_types = graha/bhava/domain only; MSR yoga count=140`

33. **[HIGH · failure_class 1]** `graha:Sun:875a` — Sun graha node reaches no bhava lordship — no graha↔bhava edges chart-wide.
    - Evidence: `22 edges, neighbor node_types = {graha} only`

34. **[HIGH · failure_class 1]** `graha:Sun:875a` — Yoga membership structurally unreachable (yogas absent as graph nodes).
    - Evidence: `no node_type=yoga; 140 MSR yoga signals`

35. **[HIGH · failure_class 1]** `graha:Venus:875a` — Venus graha node reaches no bhava lordship — no graha↔bhava edges chart-wide.
    - Evidence: `23 edges, neighbor node_types = {graha} only`

36. **[HIGH · failure_class 1]** `graha:Venus:875a` — Yoga membership structurally unreachable (yogas absent as graph nodes).
    - Evidence: `no node_type=yoga; 140 MSR yoga signals`

37. **[HIGH · failure_class 4]** `bhava:1:71aa` — Lagna (1st) bhava node registered but participates in ZERO edges — occupants/lord/aspects/arudha structurally unreachable by traversal.
    - Evidence: `edge_count=0; node exists in bodha_cgm_nodes; chart 482012f1 has 534 edges but endpoints = graha(1053)+domain(15), zero bhava — all 60 bhava nodes isolated on both charts`

38. **[HIGH · failure_class 1]** `bhava:1:71aa` — Every bhava-centric question (bhava lord chain, occupancy, aspects) unreachable via CGM graph despite underlying L1 facts existing.
    - Evidence: `systemic bhava-isolation: graph wires only graha↔graha and graha↔domain`

39. **[HIGH · failure_class 4]** `bhava:10:71aa` — 10th bhava (career/karma, high-salience) node registered but wired into 0 edges — career-domain synthesis cannot pull 10th-house structure from the graph.
    - Evidence: `edge_count=0; systemic bhava-isolation (0 bhava endpoints across 534 chart edges)`

40. **[HIGH · failure_class 1]** `bhava:10:71aa` — 10th-house lord/occupant structure unreachable via graph despite L1 facts existing.
    - Evidence: `no graha↔bhava edges chart-wide`

41. **[HIGH · failure_class 4]** `bhava:11:71aa` — 11th bhava (gains/labha, wealth-relevant) node registered but wired into 0 edges — cannot surface in any graph-driven wealth read (KP-4 adjacent).
    - Evidence: `edge_count=0; systemic bhava-isolation (0 bhava endpoints across 534 chart edges)`

42. **[HIGH · failure_class 1]** `bhava:11:71aa` — Gains/income synthesis cannot traverse 11th-house structure in the graph despite L1 facts existing.
    - Evidence: `no graha↔bhava edges chart-wide`

## 9b — MSR ingestion coverage + fidelity audit

**Lane:** LANE9b
**fact_category_total:** 204
**fact_category_done:** 204
**findings_count:** 283
**verifier_coverage:** 29.4%
**sound_count:** 42

### NOT_CONSUMED categories (8)

- dosha_label
- graha_saptavargaja_bala_component
- nakshatra_co_tenancy
- nakshatra_dispositor_chain
- nakshatra_lord_relationship
- tara_bala
- vimsopaka_bala_per_graha
- yoga_label

### BROKEN categories (5)

- aspect_jaimini_per_varga
- aspect_parashari_per_varga
- graha_centrality
- saham_position
- significator_path

### WEAK categories (154)

- anumukha_shani_period
- ardha_ashtama_shani_period
- argala_natal_matrix
- ashtakavarga_bindu_per_varga
- ashtakavarga_pinda_bhinna
- ashtakavarga_pinda_sarva_per_varga
- ashtakavarga_pinda_sodhita
- ashtama_shani_period
- aspect_jaimini
- aspect_matrix_summary
- aspect_parashari_received
- aspect_received_by_special_point
- aspect_tajik
- bhava_arudha
- bhava_bala_aspectual
- bhava_bala_directional
- bhava_bala_lord
- bhava_bala_occupant
- bhava_bala_positional
- bhava_bala_temporal
- bhava_bala_total_extended
- bhava_significance_link
- bhrigu_nadi_point
- chandra_bala_natal_baseline
- chart_center_of_gravity
- chart_cluster
- combustion_per_varga
- combustion_relationship
- composite_dispositor_strength
- conjunction_per_varga
- conjunction_special_point
- contradiction_pair
- convergence_count
- cusp_kp_lords
- dispositor_chain_per_varga
- dispositor_tree
- esoteric_point_avayogi
- esoteric_point_bhrigu_bindu
- esoteric_point_brahma
- esoteric_point_mrityu
- esoteric_point_pranapada_sphuta
- esoteric_point_shiva
- esoteric_point_sphuta_fertility
- esoteric_point_sri_yantra_position
- esoteric_point_trikona_dasha_sphuta
- esoteric_point_vishnu
- esoteric_point_yogi
- esoteric_point_yogi_system
- graha_avastha_baladi
- graha_avastha_deepta
- graha_avastha_jagrad
- graha_avastha_lajjitadi_per_varga
- graha_avastha_lifetime_exposure_summary
- graha_cheshta_bala_per_varga
- graha_dignity_per_varga
- graha_dispositor_chain
- graha_drik_bala_per_varga
- graha_functional_class_per_ascendant
- graha_gandanta
- graha_in_house_composite_strength
- graha_ishta_phala
- graha_kala_bala_per_varga
- graha_kashta_phala
- graha_kp_lords
- graha_pada_join
- graha_shadbala_cheshta
- graha_shadbala_dig
- graha_shadbala_drik
- graha_shadbala_kala
- graha_shadbala_naisargika
- graha_shadbala_sthana
- graha_shadbala_total
- graha_special_state_rollup
- graha_sthana_bala_per_varga
- graha_tara_bala
- graha_tri_deva_role_strength
- graha_vimsopaka_dasavarga
- graha_vimsopaka_saptavarga
- graha_vimsopaka_shadvarga
- graha_vimsopaka_shodasavarga
- graha_yuddha_per_varga
- house_bhava_bala_subscore
- house_bhava_bala_total
- house_strength_classification_rollup
- kala_sarpa_per_varga
- karaka_bhava_concordance
- karaka_house_lord_overlap_flag
- karakatva_strength_per_significance
- karaka_web_per_varga
- kp_cuspal_significators
- kp_ruling_planets_natal
- lal_kitab_special_point
- lord_aspects_lord_per_varga
- lord_in_house_per_varga
- maharsi_specific_point
- midpoint
- nakshatra_cross_ayanamsha
- nakshatra_dispositor
- nakshatra_statistics
- net_argala_per_varga
- panchanga_calendrical
- panchanga_choghadiya_birth
- panchanga_disha_shul
- panchanga_durmuhurta
- panchanga_godhuli_muhurta
- panchanga_gulika_kalam
- panchanga_hora_birth
- panchanga_karana
- panchanga_krakaca
- panchanga_madhyahna_sandhya
- panchanga_nakshatra_shoonya_rashi
- panchanga_nishita_kala
- panchanga_panchaka_classification
- panchanga_pratah_sandhya
- panchanga_rahu_kalam
- panchanga_sashtighati
- panchanga_sayam_sandhya
- panchanga_solar_context
- panchanga_special_yoga_combinations
- panchanga_sun_moon_dynamics
- panchanga_tithi
- panchanga_tithi_shoonya_rashi
- panchanga_vara
- panchanga_varjyam
- panchanga_vijaya_muhurta
- panchanga_visha_ghati
- panchanga_yamaganda_kalam
- panchanga_yamakantaka
- panchanga_yoga
- parivartana_per_varga
- sade_sati_cycle
- sade_sati_modifier_overlay
- sade_sati_phase
- sade_sati_phase_quarter
- sade_sati_saturn_retrograde_subset
- sambandha_grade
- saturn_derived_point
- sensitive_point_gulika_mandi
- special_lagna
- sun_derived_upagraha
- swamsa_position
- tajik_hadda_lord
- tajik_triraashipathi
- tajik_vargottama_specific
- tara_bala_natal_baseline
- upagraha_position
- vargottama_per_varga
- virodha_argala_natal_matrix
- virupa_drishti

### HIGH / CRITICAL findings (with verbatim evidence)

1. **[HIGH · failure_class 7]** `ashtakavarga_bindu_per_varga` — ~200-280 per-varga ashtakavarga bindu signals at major tier despite niche low-decision-weight granular data — salience inflation / DROWNED
   - Evidence: `cell2 major=281 (Abhisek), major=207 (Abhinandan) of ~1150 signals; per-varga ashtakavarga is not a primary acharya weighting instrument`

2. **[HIGH · failure_class 7]** `ashtakavarga_pinda_sarva_per_varga` — ~165-219 per-varga sarva-pinda signals at major tier despite niche decision-weight — salience inflation / DROWNED; ~88% chart_facts pass-through
   - Evidence: `cell2 major=219 (Abhisek), major=165 (Abhinandan) of 490; per-varga SAV is not a primary weighting surface`

3. **[CRITICAL · failure_class 7]** `aspect_jaimini_per_varga` — A single fact_category floods MSR with 15,660 signals/chart, all identical in salience/type/domain — genuine signal un-findable under a 15.6k-row indistinguishable wall
   - Evidence: `cell1=15660; cell2=supporting=15660; cell5=composite_state=15660; cell4=career|relationship|spirituality (single value, all rows)`

4. **[HIGH · failure_class 8]** `aspect_jaimini_per_varga` — Indiscriminate 1:1 fact→signal ingestion with zero salience differentiation; the funnel floods instead of narrowing
   - Evidence: `15660 chart_facts → 15660 signals per chart, all supporting tier`

5. **[HIGH · failure_class 7]** `aspect_parashari_per_varga` — Per-varga (divisional) Parashari aspects promoted to major/chart_defining in the thousands, swamping the top salience tiers and burying genuine chart-defining findings
   - Evidence: `Abhisek cell2: chart_defining=229, major=1317 from one per-varga aspect category; an acharya would treat at most a handful of divisional aspects as chart-defining (CHARTER §7.4 rationale)`

6. **[HIGH · failure_class 7]** `bhava_significance_link` — single fact_category emits 5220 signals per chart ALL at identical supporting tier — a duplication/flood wall that can swamp any MSR-fed ranked surface; 5220 co-tied rows exceed acharya read tolerance (weighs a handful of significator links, not 5000 at one weight)
   - Evidence: `cell1=5220 both charts, cell2=supporting=5220 (single tier, no top-K discrimination)`

7. **[HIGH · failure_class 7]** `contradiction_pair` — 1740 contradiction_pair signals per chart all at identical supporting tier and character|career domain — zero ranking discrimination, an identical-score wall
   - Evidence: `cell1=1740/1740, cell2=supporting=1740 single tier, cell4=character|career uniform both charts`

8. **[HIGH · failure_class 2]** `cusp_kp_lords` — KP cusp-lord signals uniformly domain-mapped to character|relationship (no wealth domain), so KP wealth significators (2nd/11th cusps) can never surface under a wealth query — KP-4 anchor re-derived; only ~37% of 240 facts consumed
   - Evidence: `cell4=character|relationship on all 87/89 both charts; cell1 87-89 of 240 chart_facts consumed`

9. **[HIGH · failure_class 1]** `dosha_label` — dosha_label fact_category (110 facts/chart) entirely un-ingested by bo_laksana — 0 MSR signals resolve to it despite facts existing in chart_facts
   - Evidence: `5-cell recipe returned []; chart_facts count=110/110 both charts`

10. **[HIGH · failure_class 2]** `dosha_label` — All 220 signal_type_class=dosha signals cite only 10 distinct fact_ids (22x reuse), and 0/10 resolve to any chart_facts.fact_id — R-42 dosha attribution collapse plus referential-integrity break violating §N.5
    - Evidence: `distinct_fids=10, total_refs=220, refs_resolving_to_chart_facts=0; sample cited id e2b47b2c6d457725 absent from chart_facts`

11. **[HIGH · failure_class 2]** `esoteric_point_mrityu` — The mrityu (death/longevity) sphuta — an explicitly marana longevity point — domain-mapped exclusively to default character|relationship; a longevity/health query can NEVER retrieve the death point (sharpest instance of shard-wide default-collapse)
    - Evidence: `cell4_domains='character|relationship' both charts, 97 signals each; SQL recipe fact_category='esoteric_point_mrityu'`

12. **[HIGH · failure_class 2]** `esoteric_point_sphuta_fertility` — The fertility sphuta (santana/beeja progeny-timing point) domain-mapped exclusively to default character|relationship, NOT children/progeny; a children/fertility query can never retrieve it (egregious, alongside mrityu)
    - Evidence: `cell4_domains='character|relationship' both charts, 64/65 signals; SQL recipe fact_category='esoteric_point_sphuta_fertility'`

13. **[HIGH · failure_class 7]** `graha_centrality` — Extreme salience inflation + drowning: a single computed centrality metric emits ~1280 signals/chart, ~976 (Abhisek) at major-or-above incl. 83 chart_defining, saturating top tiers and diluting genuine chart-defining findings
    - Evidence: `cell1 1284 + cell2 Abhisek 'background=5, chart_defining=83, major=893, supporting=303'`

14. **[HIGH · failure_class 7]** `graha_dignity_per_varga` — Salience inflation: per-varga dignity of minor divisionals promoted to chart_defining/major tiers, forming a dignity wall
    - Evidence: `cell2 482: chart_defining=148, major=704 (852 of 1084 at top-two tiers); no acharya rates D-45/D-60 dignity as chart_defining alongside a Rajayoga`

15. **[HIGH · failure_class 2]** `graha_functional_class_per_ascendant` — Functional benefic/malefic class (domain-defining by construction) mono-mapped to character|career, defeating the fact's purpose
    - Evidence: `cell4 invariant character|career; a wealth/relationship/health query cannot retrieve whether that domain's house-lord is a functional benefic/malefic — the single most decision-relevant fact`

16. **[HIGH · failure_class 2]** `graha_kp_lords` — KP significators (nakshatra/sub/sub-sub lords) domain-mono-mapped to character|relationship only — KP-4 rediscovery; unreachable under wealth/career/health domain filters
    - Evidence: `cell4 both charts = 'character|relationship' over 131/132 signals; KP lords are the significator machinery for ALL house queries incl 2nd/11th wealth`

17. **[HIGH · failure_class 1]** `graha_saptavargaja_bala_component` — Saptavargaja bala (seven-varga positional strength) never ingested by MSR despite existing in chart_facts; singled out and dropped while all 7 sibling shadbala components ARE consumed
    - Evidence: `5-cell recipe returned [] for both charts; chart_facts baseline = 35 rows/chart exist`

18. **[HIGH · failure_class 2]** `graha_special_state_rollup` — Special-state signals uniformly domain-mapped to character|career; a combust/afflicted bhava-lord special state cannot surface under wealth/marriage/health domain filters
    - Evidence: `cell4_domains='character|career' for all 34/45 signals both charts`

19. **[HIGH · failure_class 7]** `graha_sthana_bala_per_varga` — DROWNED-by-volume: ~380 near-uniform signals from a single per-varga positional-strength decomposition, ~half at major tier, swamp the funnel and bury chart-defining findings
    - Evidence: `cell1=385; cell2 482: major=194, supporting=191 — largest signal population in shard from background-grade per-varga bala`

20. **[HIGH · failure_class 2]** `graha_tara_bala` — Domain mis-mapping (category error): all tara_bala signals tagged character|relationship, but tara bala is a nakshatra-based transit/prognostic-stre
    - Evidence: `[evidence truncated in source JSON]`
