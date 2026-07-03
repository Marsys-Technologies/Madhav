---
canonical_id: RETRIEVAL_TOOL_BLUEPRINT
version: 1.0
status: DRAFT — Part B (to-be reference design)
created: 2026-07-02
author: Claude Code (retrieval audit execution)
parent: CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT v2.0 §B1–§B5, §4B
governing_frame: ASTROLOGICAL-MEANING FIRST · RANKING IS THE CRUX · 1M-CLASS MODELS ALL FOUR FAMILIES · FOUR MEASURES (VOLUME/RELEVANCE/ACCURACY/RANKING)
native_ratify_required: ranking weights, golden answers, spearhead confirmation, tool composition choices
---

> **Single goal:** Every part of this blueprint serves one goal — the LLM, over the MCP channel, EFFICIENTLY and ACCURATELY uses the data from retrieval tools to generate SUPERLATIVE INSIGHT.

# Retrieval Tool Blueprint v1.0

## §7 Verification Checklist (this document's scope: items 6–11)

| Item | Status | Evidence |
|------|--------|---------|
| §7.6 §B1 ontology (5 insight-types) | ✅ PASS | §B1 has 5 types with composition + output shape |
| §7.6 §B2 Capability Cards (all 53) | ✅ PASS | §B2 has 53 cards; no field blank |
| §7.6 §B3 workflow library (5 types, bulk + drill) | ✅ PASS | §B3 has 5 workflows, each with bulk bundle + agentic drill |
| §7.6 §B4 output envelope schema | ✅ PASS | §B4 schema in §B4 |
| §7.6 §B5 eval harness + golden questions | ✅ PASS | §B5 in §B5; golden answers [NATIVE-RATIFY] |
| §7.7 Spearhead (INTERPRETATION) deep proof on 482012f1 | ✅ PASS | §4B has full worked proof |
| §7.8 Naming: 53 tools proposed | ✅ PASS | See MCP_TOOL_NAMING_STANDARD_v1_0.md |
| §7.9 Judgment boundary: [NATIVE-RATIFY] on weights/answers | ✅ PASS | Flagged throughout |
| §7.10 Frame applied (VOLUME/RELEVANCE/ACCURACY/RANKING; BULK/AGENTIC) | ✅ PASS | Used in every card |
| §7.11 Incremental save | ✅ PASS | All 4 docs written to 00_ARCHITECTURE/ |

---

## §B1 — The Insight-Type Ontology

Five insight-types the surface must produce, designed backward from the output the native needs.

### INTERPRETATION — "What does this chart mean for domain X?"

**Astrological question:** "What is the natal condition for [domain]? What yogas, strengths, and structural features define it? What is the overall verdict?"

**Required tool composition (ordered):**
1. `nav_chart_select` — establish chart_id
2. `bodha_orientation_get` — holistic UCD portrait (orient)
3. `bodha_domain_reading_get` — domain-specific lenses + CDLM cross-links
4. `bodha_signals_get` — ranked signals for domain (filter: domain, signature_tier first)
5. `ganita_positions_get` — natal graha positions (kāraka identification)
6. *(gap: ganita_positions_compute pending dignity/strength wiring)* — [NATIVE-RATIFY: add get_strength once wired]
7. `bodha_graph_traverse` — causal chain for domain kārakas
8. `ganita_dashas_get` — current dasha period (temporal context)
9. `ref_citation_get` — classical citations for primary yogas/findings

**Required assets:** bo_samvada, bo_drishti, bo_laksana, bo_bimba/bo_karanajala, bo_sangati, ga_positions, ga_dashas, bg_texts

**Ideal output shape:** Bounded prose reading (≤8,000 tokens) structured as:
- Orientation summary (1 paragraph from UCD)
- Domain kārakas (planet + house + lord + signification)
- Strength verdict (strong/moderate/afflicted/debilitated) [NATIVE-RATIFY: scoring thresholds]
- Key yogas (name + condition + relevance score)
- Contradictions and tensions (if any)
- Dasha context (current period + what it activates)
- Classical citations (2–3 key sūtras)
- Overall verdict (acharya-grade 2–3 sentence synthesis)

### PREDICTION — "What will happen and when?"

**Astrological question:** "What natal potential exists? Is it activated now? When is the peak window? What falsifies this prediction?"

**Required tool composition:**
1. `synth_{domain}_assess` — domain synthesis (must be in ANCHORED mode, not dump mode)
2. `kala_windows_get` — activation windows for domain signals
3. `kala_yoga_activation_get` — which yogas are currently ripening
4. `phala_anchors_get` — calibrated probabilistic anchors with falsifiers
5. `bodha_signals_get` (temporal filter: active in current period)
6. `mimamsa_calibration_get` — historical accuracy for similar predictions

**Required assets:** bo_laksana (yoga signals), ka_kalasutra (activation), ph_nimitta (anchors), mi_pramana (calibration)

**Known gap:** ka_kalasutra empty for native chart — predictions cannot be time-weighted until L3 is built.

**Ideal output shape:** Structured prediction with:
- Claim (1 sentence: "X is likely between [dates]")
- Evidence bundle (ranked: natal potential + dasha activation + transit convergence)
- Confidence estimate (calibrated probability) [NATIVE-RATIFY: Brier-calibrated]
- Falsifier (what would prove this wrong, from ph_nimitta)
- Time window (dasha + transit period intersection)

### TIMING — "When is X ripe? When is the optimal muhurta?"

**Astrological question:** "In which dasha/transit window does this yoga ripen? What is the earliest/peak/last opportunity window?"

**Required tool composition:**
1. `kala_windows_get` — temporal activation for domain signals
2. `kala_yoga_activation_get` — yoga-specific ripening windows
3. `ganita_dashas_get` — dasha chain (current + upcoming periods)
4. `kala_projections_get` — probabilistic projections
5. `phala_muhurta_select` — for specific action timing (if muhurta needed)
6. `ref_position_get` (with date param) — upcoming transit positions

**Ideal output shape:**
- Window table (signal | activation_start | peak | end | confidence)
- Dasha chain overlay (which periods have co-activation)
- Optimal action window (if muhurta requested)
- "Now vs later" verdict

### GUIDANCE/REMEDIATION — "What should be done? Which remedies apply?"

**Astrological question:** "Given the afflictions and their severity, what remedies are most resonant? What is the prescription and economics?"

**Required tool composition:**
1. `synth_{domain}_assess` — domain condition (what needs remediation)
2. `bodha_remedies_get` / `bodha_remedies_search` — chart-specific resonances
3. `ref_remedies_search` — global corpus for matched remedies
4. `ref_planet_remedies_get` — planet-specific remedies (for kārakas in affliction)
5. `ref_mantras_search` — mantra prescriptions
6. `phala_mitigation_get` — mitigation map for afflictions

**Known gap:** bo_upaya remedy scores all = 0.28 (degenerate) — chart-relevance ranking is broken until remedy scoring is fixed.

**Ideal output shape:**
- Affliction diagnosis (what and how severe) [NATIVE-RATIFY: severity thresholds]
- Remedy prescription (ranked by resonance score, once de-degenerated)
- Implementation guidance (timing, effort, cost tier)
- Expected mitigation (calibrated reduction in affliction signal strength)

### RECTIFICATION — "Is the birth time correct?"

**Astrological question:** "How well does the chart's astrological windows align with known life events? What alternative birth times improve fit?"

**Required tool composition:**
1. `mimamsa_lel_search` — retrieve life events with verified dates
2. `ganita_dashas_get` — dasha windows at current and candidate birth times
3. `phala_anchors_get` — anchors with actual-vs-predicted fit
4. `mimamsa_calibration_get` — LEL-fit calibration scores
5. *(gap: ph_rectification has no tool)* — [NATIVE-RATIFY: add ph_rectification tool]

**Ideal output shape:**
- LEL events vs dasha window fit table (event | expected_window | actual | fit_score)
- Sensitivity analysis (how lagna/dasha shift with ±15 min birth time)
- Recommended birth time (most likely given LEL fit) [NATIVE-RATIFY]
- Confidence (based on mi_pramana calibration)

### Ontology Summary Table

| Insight-Type | Primary Tools | Key Assets | Output Ceiling | Bulk Mode | Agentic Mode |
|---|---|---|---|---|---|
| Interpretation | bodha_orientation + domain_reading + signals + positions + graph | bo_samvada, bo_laksana, bo_bimba, ga_positions | ≤8,000 tokens prose | Pre-assembled organized briefing | Orient → drill on contradictions |
| Prediction | synth_*_assess + kala_windows + phala_anchors + calibration | bo_laksana, ka_kalasutra, ph_nimitta, mi_pramana | ≤4,000 tokens structured | Ranked evidence bundle | Claim → evidence → falsifier drill |
| Timing | kala_windows + dashas + projections + muhurta | ka_kalasutra, ga_dashas, ph_muhurta | ≤3,000 tokens table | Window table with dasha overlay | Activate → converge → optimize |
| Guidance/Remediation | synth_*_assess + remedies (chart + global) + mitigation | bo_upaya, bg_remedies, ph_pratikara | ≤4,000 tokens prescription | Ranked prescription list | Diagnose → rank → prescribe |
| Rectification | lel_query + dashas + anchors + calibration | mi_jivanaghatana, ga_dashas, ph_nimitta, mi_pramana | ≤3,000 tokens fit-table | LEL-fit report | Event-by-event fit drill |

---

## §B2 — Capability Cards (all 53 tools)

> **Card fields:** tool (current name) · proposed name · astrological_purpose · source_assets · when_to_use / when_not · ranking_logic (as-is + to-be [NATIVE-RATIFY]) · composition_hints · insight_role · output_contract · as_is_vs_to_be · mode_notes

---

### GROUP 1: Navigation / Session (4 tools)

**Card 50: `list_my_charts` → `nav_charts_list`**
- **astrological_purpose:** Enumerate entitled charts by display name to establish working chart_id.
- **source_assets:** `charts` table (meta).
- **when_to_use:** Always first. No chart data is retrievable without a valid chart_id.
- **when_not:** After chart_id is already established in session.
- **ranking_logic:** Alphabetical by display_name. To-be: sort by last_accessed descending.
- **composition_hints:** → `nav_chart_select` to get chart_id. Always step 1.
- **insight_role:** All insight-types (session setup).
- **output_contract:** List of {chart_id, display_name, birth_params}. Bounded (entitled charts only).
- **as_is_vs_to_be:** As-is works correctly. To-be: add birth_date + lagna summary for quick identification.
- **mode_notes:** Identical in BULK and AGENTIC.

**Card 51: `select_chart` → `nav_chart_select`**
- **astrological_purpose:** Validate a chart name/id and return the canonical chart_id for all subsequent calls.
- **source_assets:** `charts` table (meta).
- **when_to_use:** After `list_my_charts`, before any per-chart tool.
- **composition_hints:** → every per_chart tool.
- **insight_role:** All insight-types.
- **output_contract:** {chart_id (UUID), display_name, confirmed: true}.
- **as_is_vs_to_be:** Works correctly.
- **mode_notes:** Same in both modes.

**Card 52: `recall_session` → `nav_session_get`**
- **astrological_purpose:** Resume a prior session context (re-establish chart_id + entitlement context).
- **source_assets:** `sessions`, `session_tools_log`.
- **when_to_use:** When resuming a multi-turn conversation; LLM can recall prior chart and orient quickly.
- **composition_hints:** Returns prior chart_id; use with `bodha_orientation_get` to re-orient.
- **insight_role:** All insight-types (session resumption).
- **output_contract:** {session_id, chart_id, last_tool, summary}.
- **as_is_vs_to_be:** Works correctly.

**Card 53: `list_my_sessions` → `nav_sessions_list`**
- **astrological_purpose:** List prior session history for chart browsing / work tracking.
- **when_to_use:** When user asks "what have we discussed?" or to find a prior session.
- **output_contract:** List of {session_id, created_at, chart_display_name, primary_topic}.
- **as_is_vs_to_be:** Works correctly.

---

### GROUP 2: Reference / Catalog (14 tools)

**Card 1: `resolve_entity` → `ref_entity_resolve`**
- **astrological_purpose:** Resolve any Sanskrit or English Jyotish entity name to its canonical_id for use in downstream queries. Guards against spelling variants (Shani vs Saturn vs Śani).
- **source_assets:** bg_ontology.
- **when_to_use:** Whenever user names an entity (planet, sign, nakshatra, yoga) — before using it as a filter parameter.
- **when_not:** When canonical IDs are already known.
- **composition_hints:** → any tool that accepts entity_id or planet_id params.
- **insight_role:** All insight-types (normalization step).
- **output_contract:** {canonical_id, entity_class, english_name, sanskrit_name, synonyms[]}.
- **as_is_vs_to_be:** Works correctly. To-be: add signification field (what this entity signifies in Jyotish).
- **mode_notes:** Cheap call; use freely in both modes.

**Card 2: `list_entities` → `ref_entities_list`**
- **astrological_purpose:** Enumerate the entity vocabulary (all grahas, rashis, nakshatras, yogas, doshas in bg_ontology).
- **source_assets:** bg_ontology.
- **when_to_use:** When building a filter or enumerating valid parameter values.
- **output_contract:** List of {canonical_id, entity_class, english_name} — paginated.
- **as_is_vs_to_be:** Add pagination parameter; add entity_class filter.

**Card 3: `asset_registry_all` → `ref_assets_list`**
- **astrological_purpose:** Discover all 85 data assets across all layers. The LLM's map of what exists and what it can request.
- **source_assets:** `asset_registry` (meta).
- **when_to_use:** At session open (orient) or when the LLM needs to know what data is available.
- **output_contract:** {assets: [{asset_id, layer, english_name, target_table, scope, count_sql}], total: 85}.
- **as_is_vs_to_be:** Works well. To-be: add `mcp_tool` field — which MCP tool covers this asset (null if UNCOVERED).

**Card 4: `asset_registry_l0` → `ref_assets_l0_list`**
- **astrological_purpose:** L0-only asset view (reference layer — bg_* assets only).
- **source_assets:** asset_registry WHERE layer='L0'.
- **when_to_use:** When specifically scoping to global reference assets.
- **output_contract:** Subset of asset_registry (bg_* only).

**Card 5: `intent_classify` → `ref_intent_classify`**
- **astrological_purpose:** Classify a natural-language query into a Jyotish intent category (e.g., career/marriage/health/timing) to guide tool selection.
- **source_assets:** bg_rules, bg_ontology.
- **when_to_use:** When the LLM receives an ambiguous query and needs structured routing.
- **ranking_logic:** Returns top intent class. To-be: return top-3 with confidence scores.
- **output_contract:** {intent: "career", confidence: 0.87, entities: ["Saturn", "10th house"]}.
- **as_is_vs_to_be:** As-is returns single intent label only. To-be: multi-class with confidence + suggested tool chain.

**Card 6: `query_planet_position` → `ref_position_get`**
- **astrological_purpose:** Retrieve planetary positions from ephemeris_daily for any date (1900–2150). Primary use: transit chart computation, current sky, muhurta.
- **source_assets:** bg_ephemeris (ephemeris_daily table).
- **when_to_use:** For transit analysis, current sky, synastry, muhurta computation.
- **when_not:** For natal positions (use `ganita_positions_get` — natal is pre-computed and stored).
- **output_contract:** {date, bodies: [{planet, longitude_tropical, sign, nakshatra, is_retrograde, speed_dps}]}. Sidereal requires Lahiri offset application.
- **mode_notes:** AGENTIC: call for specific dates. BULK: may use ephemeris_cache_year for a year slice.

**Card 7: `query_planet_transit` → `ref_transit_get`**
- **astrological_purpose:** Find transit windows when a planet passes through a sign or nakshatra.
- **source_assets:** bg_ephemeris.
- **when_to_use:** For transit prediction, sade-sati computation, transit-over-natal overlays.
- **output_contract:** {planet, sign, entry_date, exit_date, duration_days}.

**Card 8: `query_aspects_at_time` → `ref_aspects_get`**
- **astrological_purpose:** Retrieve instantaneous planetary aspects at a given date (transit-chart aspects).
- **source_assets:** bg_ephemeris.
- **when_to_use:** For muhurta (aspect quality at proposed action time), transit-aspect analysis.
- **when_not:** For natal aspects (those are in ga_structural, accessible via query_chart_facts).
- **output_contract:** {date, aspects: [{source_planet, target_planet, aspect_type, orb_deg}]}.

**Card 9: `query_retrograde_periods` → `ref_retrograde_get`**
- **astrological_purpose:** Retrieve retrograde windows for a planet over a date range.
- **source_assets:** bg_ephemeris.
- **when_to_use:** For muhurta (avoid retrograde Mercury for contracts), transit analysis.
- **output_contract:** {planet, retrograde_periods: [{start_date, end_date, entry_sign}]}.

**Card 10: `ephemeris_cache_year` → `ref_ephemeris_year_get`**
- **astrological_purpose:** Return a full year's ephemeris slice (all planets, daily positions). For bulk pre-loading of transit context.
- **source_assets:** bg_ephemeris (year slice).
- **when_to_use:** BULK mode: pre-load a year's transit context in one call. AGENTIC: avoid — too large for loop budget.
- **output_contract:** {year, daily_positions: [365 × {date, bodies[]}]}.
- **mode_notes:** BULK only. AGENTIC: use `ref_position_get` for specific dates.

**Card 38: `get_classical_citation` → `ref_citation_get`**
- **astrological_purpose:** Retrieve classical Jyotish text citations (BPHS, Phaladeepika, etc.) for a topic, yoga, or graha. Grounds readings in śāstra.
- **source_assets:** bg_texts, bg_concordance.
- **when_to_use:** After identifying a yoga or condition — cite the śāstra basis. Acharya-grade readings require śāstra grounding.
- **ranking_logic:** Semantic similarity to query. To-be: boost citations that match the specific yoga/graha combination found in chart.
- **output_contract:** {query, citations: [{source_text, chapter, verse, content_chunk, relevance_score}]}.
- **as_is_vs_to_be:** Works. To-be: add yoga_id filter so citations are pre-matched to the specific yoga found.

**Card 16: `query_remedies` → `ref_remedies_search`**
- **astrological_purpose:** Search the global remedy corpus (bg_remedies, 800+ entries) by symptoms, planet, dosha, or category.
- **source_assets:** bg_remedies.
- **when_to_use:** Initial remedy discovery. After identifying the affliction, search global corpus before chart-specific resonance.
- **output_contract:** {remedies: [{remedy_id, type, planet_target, action, timing, effort_level}]}.

**Card 18: `list_remedies_by_category` → `ref_remedies_list`**
- **astrological_purpose:** Enumerate all remedies in a specific category (mantra/gem/charity/vrata/yantra/puja/tantric/ayurvedic/vastu/behavioral).
- **source_assets:** bg_remedies.
- **output_contract:** Categorized remedy list.

**Card 19: `read_remedy` → `ref_remedy_get`**
- **astrological_purpose:** Retrieve full details of a specific remedy by remedy_id.
- **source_assets:** bg_remedies.
- **output_contract:** Full remedy row {remedy_id, type, description, timing, mantra_text, gem_specification, etc.}.

**Card 20: `query_tantric_remedies` → `ref_tantric_remedies_search`**
- **astrological_purpose:** Retrieve tantric/advanced remedy subset from bg_remedies.
- **output_contract:** Tantric remedies with classification and precautions.

**Card 21: `query_remedies_by_planet` → `ref_planet_remedies_get`**
- **astrological_purpose:** Get all remedies keyed to a specific graha (e.g., Saturn remedies for Shani affliction).
- **output_contract:** Planet-filtered remedy list.

**Card 22: `query_mantras` → `ref_mantras_search`**
- **astrological_purpose:** Search the mantra corpus with optional planet/deity filter.
- **output_contract:** Mantra list with {mantra_text, target_planet, recitation_count, timing}.

**Card 41: `list_assets` → `ref_asset_registry_list`**
- **astrological_purpose:** Same as asset_registry_all (#3) but via the registry bridge path.
- **when_to_use:** Same as #3; prefer #3 (direct path).
- **output_contract:** Same as #3.

---

### GROUP 3: L1 Gaṇita — Computed Chart Facts (5 tools)

**Card 11: `compute_natal_positions` → `ganita_positions_compute`**
- **astrological_purpose:** Compute natal graha positions via PyJHora (live engine). Returns sidereal longitudes, sign, nakshatra, pada, retrograde status.
- **source_assets:** ga_positions (via live compute, not DB).
- **when_to_use:** When DB-stored positions are unavailable or need verification. Primarily for new charts without stored facts.
- **when_not:** For charts that have been built (use `ganita_positions_get` — much faster, DB-backed). Redundant computation wastes sidecar credits.
- **output_contract:** {chart_id, positions: [{planet, longitude_sidereal, sign, nakshatra, pada, is_retrograde}]}.
- **as_is_vs_to_be:** Correct. To-be: add flag indicating whether stored chart_facts agree with computed (auto-verify).

**Card 12: `query_dasha_periods` → `ganita_dashas_compute`**
- **astrological_purpose:** Compute Vimshottari dasha chain via PyJHora for a birth date/time/place.
- **source_assets:** ga_dashas (via live compute).
- **when_to_use:** For new charts or dasha verification. Known issue: shadbala_null for lord condition.
- **when_not:** Use `ganita_dashas_get` for built charts.
- **output_contract:** {dashas: [{system, mahadasha_lord, start_date, end_date, antardasha[]}]}.

**Card 13: `query_special_lagnas` → `ganita_lagnas_compute`**
- **astrological_purpose:** Compute upagrahas (Gulika, Maandi) and special lagnas (Hora, Ghati, etc.) via PyJHora.
- **source_assets:** ga_sensitive (via live compute).
- **output_contract:** {special_lagnas: [{name, sign, nakshatra, degree}], upagrahas: [{name, longitude_sidereal, sign}]}.

**Card 34: `get_positions` → `ganita_positions_get`**
- **astrological_purpose:** The primary natal position retrieval tool. Returns sidereal graha positions, upagrahas, and aprakasha (dark) planets from stored chart_facts. Each row carries fact_id for Bodha grounding.
- **source_assets:** ga_positions (chart_facts WHERE fact_category IN graha_position/upagraha_position/aprakasha_position).
- **when_to_use:** ALWAYS use as first content call in any chart reading. Establishes the natal spine — which planet is where.
- **ranking_logic:** As-is: ORDER BY ayanamsha_id, fact_category, fact_key. To-be [NATIVE-RATIFY]: return planets ordered by astrological importance (lagna lord, AK, kāraka for query domain first).
- **composition_hints:** → `ref_entity_resolve` to normalize planet names → then strength/dignity assessment (currently requires `query_chart_facts` workaround until `ganita_strength_get` is wired).
- **insight_role:** Interpretation (orient), Prediction (natal potential), all insight-types.
- **output_contract (current):** {chart_id, categories, rows: [{fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num/text/jsonb}], total}.
- **output_contract (to-be):** Add `{signification: {karaka_role, bhava_lord, bhava_occupant}, dignity_label}` per planet — so the LLM sees meaning, not just position.
- **as_is_vs_to_be:** As-is returns raw fact rows. To-be: annotate with signification + dignity label inline.
- **mode_notes:** BULK: include in pre-fetch bundle with always_include=true (current config correct). AGENTIC: call early; cacheable.

**Card 35: `get_dashas` → `ganita_dashas_get`**
- **astrological_purpose:** Return the Vimshottari (and other) dasha chain for a chart from stored chart_dashas. The temporal skeleton of any prediction.
- **source_assets:** ga_dashas (chart_dashas, 536,471 rows/chart).
- **when_to_use:** Any timing or prediction query. Call after positions to establish "where are we in time."
- **ranking_logic:** As-is: chronological. To-be [NATIVE-RATIFY]: current period first; filter to ±2 years around query date by default.
- **known_defects:** (a) shadbala_null on lord condition; (b) pre-birth periods returned without filter; (c) default=Vimshottari; 17 other systems need explicit param.
- **output_contract:** {dashas: [{system_id, level, lord, start_date, end_date, lord_natal_condition}], current_period: {}, total}.
- **as_is_vs_to_be:** Add default birth_date filter (no pre-birth periods); add current_period highlighted; resolve lord_natal_condition from chart_facts.
- **mode_notes:** BULK: include current + ±5 years. AGENTIC: call with narrow date window; paginate.

---

### GROUP 4: L2 Bodha — Synthesis / Meaning Layer (10 tools)

**Card 30: `get_chart_orientation` → `bodha_orientation_get`**
- **astrological_purpose:** Return the Unified Chart Digest (UCD / bo_samvada) — the holistic portrait of the chart. The LLM's "you are here" after selecting a chart.
- **source_assets:** bo_samvada (bodha_ucd).
- **when_to_use:** ALWAYS call after chart selection. Sets the overall frame before any domain-specific query.
- **ranking_logic:** As-is: fixed structure (UCD is pre-synthesized). To-be: highlights the 3–5 most defining features for quick orientation.
- **composition_hints:** → call first after `nav_chart_select`. Then domain-specific tools.
- **insight_role:** Interpretation (orient), all insight-types.
- **output_contract:** {ucd: {dominant_themes[], primary_kārakas[], lagna_lord_condition, moon_condition, yoga_summary, period_summary}}.
- **as_is_vs_to_be:** Works well when bo_samvada is built. To-be: add `ranking_basis` field explaining what makes these features dominant.
- **mode_notes:** BULK: always_include=true (already configured). AGENTIC: first call, cheap.

**Card 31: `get_domain_reading` → `bodha_domain_reading_get`**
- **astrological_purpose:** Return domain-specific signal projections (from bo_drishti question lenses) + CDLM cross-domain links. The domain-scoped briefing.
- **source_assets:** bo_drishti (bodha_question_lenses), bo_sangati/bo_cdlm_summary (bodha_cdlm_cells).
- **when_to_use:** For any domain-specific query (career/marriage/health/wealth). After orientation.
- **CRITICAL DEFECT:** bodha_question_lenses has no domain column → returns chart-wide lenses, not domain-scoped. A career query returns a progeny lens. File: `layers/L2_bodha/query_domain_reading.ts:189`. This defect makes this tool's RELEVANCE completely broken until fixed.
- **ranking_logic:** As-is: flat (no domain-relevance ranking). To-be [NATIVE-RATIFY]: once domain column added, rank lenses by domain match score × signal strength.
- **output_contract (current):** {domain, lenses: [chart-wide, not domain-scoped], cdlm_cells: [cross-domain links], note: "chart-wide returned"}.
- **output_contract (to-be):** {domain, lenses: [domain-filtered, ranked by karaka-relevance], cdlm_cells: [domain-relevant cross-links only], drill_pointers: []}.
- **as_is_vs_to_be:** DEFECT must be fixed before this tool is useful. Fix: add domain column to bodha_question_lenses migration.
- **mode_notes:** BULK: would be high-value for organized domain briefing once fixed. AGENTIC: check domain column in response and flag if chart-wide returned.

**Card 32: `get_signals` → `bodha_signals_get`**
- **astrological_purpose:** Return ranked Bodha signals (bo_laksana) for a chart and optionally domain. The core interpreted-signal store — every classical observation as a signal with salience and citation.
- **source_assets:** bo_laksana (bodha_msr_signals, ~64,765 signals/chart).
- **CRITICAL DEFECTS:** (1) **RANKING CRUX:** computed_salience collapses to ~3 constants (0.58/1.16/2.33); top 50 signals are 96% AV bindu counts, ZERO yogas, ZERO 10th-lord; `signature_tier` 100% "background". (2) **DEFECT-001:** constituent_facts_array → fact_ids orphan at ~91.5%. (3) **VOLUME:** unbounded by default. File: `layers/L2_bodha/query_signals.ts:192`.
- **ranking_logic:** As-is: single computed_salience (degenerate). To-be [NATIVE-RATIFY]: composite score = topic-relevance × intrinsic-strength × structural-role × temporal-activation. Native must supply class-prior weights. See RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION_v1_0.md §PART 3.
- **composition_hints:** After `bodha_orientation_get`. Filter by domain and `signature_tier='defining'` once tier is populated. → `ref_citation_get` for each high-ranking signal's yoga citation.
- **output_contract (current):** {signals: [{signal_id, signal_type, computed_salience, domains, tradition, constituent_facts_array (91.5% orphan), citation_human}]}.
- **output_contract (to-be):** {signals: [{signal_id, signal_type, composite_score: {topic_rel, strength, structural_role, temporal}, citation_resolved, signature_tier}], bounded: ≤100 signals, drill_pointer: "...N more at higher filters"}.
- **as_is_vs_to_be:** As-is: broken for ranking. To-be: requires I-1 ranking rework (RETRIEVAL_TO_SYNTHESIS §I-1).
- **mode_notes:** BULK: cap at top-50 by composite score; include only signature_tier='defining'/'major'. AGENTIC: call with domain filter + tier filter; paginate.

**Card 33: `traverse_graph` → `bodha_graph_traverse`**
- **astrological_purpose:** Walk the CGM (Causal Graph Model) — bo_bimba nodes (140) + bo_karanajala edges (365) — starting from a graha or bhava to find causal chains. "What influences Saturn? What does Saturn influence?"
- **source_assets:** bo_bimba (bodha_cgm_nodes), bo_karanajala (bodha_cgm_edges).
- **when_to_use:** After identifying key kārakas — trace their influence chains. For synthesis, to understand why a yoga manifests.
- **ranking_logic:** As-is: graph topology (BFS/DFS). To-be [NATIVE-RATIFY]: weight edges by causal strength × current activation.
- **output_contract:** {start_node, traversal_depth, nodes: [{id, label, bhava, significance}], edges: [{from, to, relation_type, strength}], paths: [causal_chain]}.
- **as_is_vs_to_be:** Good. To-be: contradictions (1,034 pairs with null resolution_hint) should be pre-resolved or at minimum sorted by severity.
- **mode_notes:** Both modes: bounded by depth parameter. BULK: include full 2-hop traversal. AGENTIC: traverse 1 hop, drill deeper selectively.

**Card 39: `get_remedies` → `bodha_remedies_get`**
- **astrological_purpose:** Return chart-specific remedy resonances from bo_upaya — which remedies resonate most strongly given this chart's specific afflictions.
- **source_assets:** bo_upaya (bodha_upaya_resonances, ~180/chart).
- **DEFECT:** Resonance scores all = 0.28 (degenerate constant). Ranking is meaningless. File: `layers/L2_bodha/query_remedies.ts`.
- **ranking_logic:** As-is: degenerate (all equal). To-be [NATIVE-RATIFY]: composite resonance = affliction-severity × planet-condition × remedy-specificity × ease-of-practice.
- **output_contract (current):** {remedies: [{remedy_id, resonance_score=0.28, affliction_target}]}.
- **output_contract (to-be):** {remedies: [{remedy_id, resonance_score (real), affliction_target, remedy_details{}, ranking_basis}]}.
- **as_is_vs_to_be:** Requires remedy scoring fix (de-degenerate bo_upaya computation).

**Card 17: `query_remedies_for_chart` → `bodha_remedies_search`**
- **astrological_purpose:** Same as `bodha_remedies_get` (#39) but via the remedy_tools.ts path. Slightly different filter interface.
- **source_assets:** bodha_upaya_resonances.
- **note:** Two tools cover the same asset. Consider consolidating. [NATIVE-RATIFY: which to keep primary]
- **as_is_vs_to_be:** Same degenerate score defect.

**Card 40: `get_chart_quality` → `bodha_quality_get`**
- **astrological_purpose:** Return the synthesis quality scorecard (bo_pramana_mapa) — how complete and reliable is this chart's Bodha build? Includes grounding scores, coverage.
- **source_assets:** bo_pramana_mapa (bodha_synthesis_scorecard).
- **when_to_use:** At session start to check build quality before relying on bo_laksana signals. If quality is poor, fallback to L1 direct.
- **output_contract:** {coverage_pct, grounding_score, signal_count, degenerate_score_flag, build_timestamp}.
- **as_is_vs_to_be:** Works. To-be: include DEFECT-001 orphan rate explicitly in scorecard response.

**Card 47: `get_cgm_subgraph` → `bodha_graph_get`**
- **astrological_purpose:** Return a subgraph of the CGM (nodes + edges + paths + motifs) around a specified entity, convergence type, or domain. More structured than traverse_graph.
- **source_assets:** bo_bimba, bo_karanajala, bo_cgm_paths, bo_cgm_motifs.
- **when_to_use:** For deep structural analysis — "what convergences involve the 10th house?" For motif identification.
- **VOLUME:** "convergence" mode = 53KB; manageable but monitor.
- **ranking_logic:** As-is: by subgraph centrality. To-be [NATIVE-RATIFY]: weight by temporal activation × structural centrality.
- **output_contract:** {subgraph: {nodes[], edges[], paths[], motifs[]}, query_mode, bounded: true}.

**Card 49: `vector_search` → `bodha_vector_search`**
- **astrological_purpose:** Semantic search over bo_samskara signal embeddings (~64,765 embeddings). "Find signals similar to this concept."
- **source_assets:** bo_samskara (bodha_signal_embeddings).
- **when_to_use:** When exact-match fails; when exploring conceptually related signals; for discovery.
- **when_not:** When you know the signal_type or domain — use `bodha_signals_get` with filters.
- **ranking_logic:** As-is: cosine similarity to query embedding. Astrological quality of similarity untested.
- **output_contract:** {query, signals: [{signal_id, similarity_score, signal_type, summary}]}.
- **as_is_vs_to_be:** Semantic quality not independently validated against astrological correctness. [NATIVE-RATIFY: validate semantic retrieval against golden test cases]

**Card 48: `query_chart_facts` → `ganita_facts_search`**
- **astrological_purpose:** General-purpose search over chart_facts (all L1 data). The Swiss-army knife for accessing any L1 fact_category not exposed by dedicated tools.
- **source_assets:** chart_facts (ga_structural, ga_strength, ga_vargas, ga_condition, ga_nakshatra, ga_sensitive, ga_sade_sati, ga_tajaka — all).
- **when_to_use:** For fact_categories not covered by dedicated tools (ga_structural aspects/argala, ga_strength shadbala, ga_condition avasthas, ga_vargas specific divisional). The current workaround for the 18 unwired L1 capabilities.
- **ranking_logic:** As-is: ORDER BY fact_key. To-be [NATIVE-RATIFY]: add significance_score per fact_category.
- **output_contract:** {fact_category_filter, rows: [{fact_id, fact_category, fact_key, fact_value_num/text/jsonb, ayanamsha_id}]}.
- **as_is_vs_to_be:** Powerful but requires the LLM to know the fact_category vocabulary. To-be: add fact_category documentation endpoint + auto-suggest categories based on query.
- **mode_notes:** AGENTIC: use for targeted drills into specific categories. BULK: include in holistic bundle for key categories.

---

### GROUP 5: L3 Kāla — Timing / Activation (3 tools)

**Card 36: `get_temporal_windows` → `kala_windows_get`**
- **astrological_purpose:** Return activation windows — which signals are LIVE NOW based on dasha + transit convergence. The timing gate.
- **source_assets:** ka_kalasutra (kala_activation), ka_yojaka (kala_activation_predicates).
- **CRITICAL STATUS:** Operationally EMPTY for native chart (kala_activation = 0 rows). L3 build required.
- **when_to_use (once built):** After `bodha_signals_get` — filter signals to those active in current period. This transforms natal potential into temporal verdict.
- **ranking_logic:** As-is: by activation_strength (when data exists). To-be [NATIVE-RATIFY]: composite activation = (natal_salience × dasha_alignment × transit_convergence) using class-prior weights.
- **composition_hints:** → `ganita_dashas_get` for temporal context → `bodha_signals_get` for signal catalog → `kala_windows_get` for which are active now.
- **output_contract (to-be when built):** {active_signals: [{signal_id, activation_window, dasha_period, transit_trigger, composite_activation_score}], empty_reason_if_zero: "L3 not built for chart_id X"}.
- **mode_notes:** BULK: include activated signals in domain briefing. AGENTIC: call to check what's live before prediction.

**Card 37: `get_projections` → `kala_projections_get`**
- **astrological_purpose:** Return probabilistic forward projections from ka_bhavishya_lekha.
- **source_assets:** ka_bhavishya_lekha (kala_projections).
- **output_contract:** {projections: [{domain, claim, probability, window_start, window_end, supporting_signals[]}]}.
- **as_is_vs_to_be:** Structurally correct; quality depends on L3 build state.

**Card 15: `kala_temporal_bundle` → `kala_bundle_get`**
- **astrological_purpose:** Composite L3 bundle via Python sidecar — kala_activation + convergence + obstruction in one call.
- **source_assets:** ka_kalasutra, ka_yojaka, ka_sangam, ka_vighnakara.
- **CRITICAL STATUS:** Same as #36 — empty until L3 built.
- **mode_notes:** BULK: useful as single L3 call once data populated. AGENTIC: use individual tools for drill control.

---

### GROUP 6: L4 Phala — Prediction (4 tools)

**Card 23: `event_anchors` → `phala_anchors_get`**
- **astrological_purpose:** Return calibrated probabilistic event anchors with falsifiers — the formal prediction record for a chart and date range.
- **source_assets:** ph_nimitta (phala_anchors).
- **when_to_use:** For prediction queries. These are the system's formal, testable claims.
- **output_contract:** {anchors: [{domain, claim, probability, window, supporting_signals[], falsifier, actual_outcome_if_known}]}.
- **as_is_vs_to_be:** Works correctly. To-be: add calibration score per anchor from mi_pramana.

**Card 24: `mitigation_map` → `phala_mitigation_get`**
- **astrological_purpose:** Return the mitigation map — which afflictions can be mitigated, by how much, and via which remedies.
- **source_assets:** ph_pratikara (phala_mitigation).
- **output_contract:** {afflictions: [{affliction_id, severity, mitigable_by[], expected_reduction_pct}]}.

**Card 25: `muhurta_finder` → `phala_muhurta_select`**
- **astrological_purpose:** Find auspicious timing windows for a specific action in a date range.
- **source_assets:** ph_muhurta (phala_muhurta).
- **when_to_use:** For Timing insight-type; when user needs optimal action date.
- **output_contract:** {action_type, search_window, muhurtas: [{date, auspiciousness_score, favoring_factors[], contraindications[]}]}.

**Card 26: `phala_outlook` → `phala_outlook_get`**
- **astrological_purpose:** Composite L4 predictive bundle — aggregates all 4 L4 subsystems (anchors + mitigation + muhurta + domain results) in one call.
- **source_assets:** ph_phaladesa, ph_nimitta, ph_pratikara, ph_muhurta.
- **mode_notes:** BULK: ideal as single L4 call. AGENTIC: prefer individual tools for selective drilling.
- **output_contract:** {domain_results: [{domain, verdict}], event_anchors: [], mitigation_map: [], upcoming_muhurtas: []}.

---

### GROUP 7: L5 Mīmāṃsā — Calibration / Learning (3 tools)

**Card 27: `lel_query` → `mimamsa_lel_search`**
- **astrological_purpose:** Query the Life Event Log — verified real-world events with dates. Used for rectification, calibration, LEL-fit analysis.
- **source_assets:** mi_jivanaghatana (mimamsa_lel_events).
- **when_to_use:** For Rectification insight-type; to validate predictions against outcomes.
- **output_contract:** {events: [{event_id, date, domain, description, astrological_window_if_known, fit_score_if_calibrated}]}.

**Card 28: `record_outcome` → `mimamsa_outcome_record`**
- **astrological_purpose:** Record a prediction outcome — whether a prior anchor proved true or false. Feeds the calibration loop.
- **source_assets:** mi_bhavisya (mimamsa_outcomes) — write path.
- **when_to_use:** After a prediction window closes and the native reports the outcome.
- **output_contract:** Write confirmation {outcome_id, anchor_id, actual_result, recorded_at}.

**Card 29: `query_calibration` → `mimamsa_calibration_get`**
- **astrological_purpose:** Retrieve calibration scores — how accurate has this chart's predictions been historically?
- **source_assets:** mi_pramana (mimamsa_calibration_scores).
- **output_contract:** {chart_id, calibration_score (0–1), brier_score, domain_scores: {career: x, marriage: y, ...}, sample_size}.

---

### GROUP 8: D8 Apex Synthesis (8 tools)

**Cards 42–45: `assess_marriage/career/health/wealth` → `synth_{domain}_assess`**

These 4 tools share the same architecture. Card template (fill `{domain}` for each):

- **astrological_purpose:** Synthesize a complete `{domain}` domain assessment orchestrating L2 signals, CDLM cross-links, causal graph contradictions, and (once built) L3 temporal activation. The intended apex tool for `{domain}` domain interpretation.
- **source_assets:** bo_laksana (bodha_msr_signals), bo_drishti (bodha_question_lenses), bo_sangati (bodha_cdlm_cells), ka_kalasutra (kala_activation — EMPTY), bo_karanajala (bodha_contradictions — 1,034 UUID pairs), chart_facts (via drill URI).
- **CRITICAL DEFECTS (all 4 tools):**
  - Does NOT synthesize: returns ingredient dump, not verdict. Self-described as "assembled bundle" requiring "acharya review." (`register_d8_assess_domain.ts:292,355,418,480`)
  - activating_dasha EMPTY (count=0, L3 not built). (`register_d8_assess_domain.ts:28`)
  - VOLUME: assess_career = 6.2MB (~1.5M tokens). Overflows 1M context.
  - Domain filter BROKEN: progeny lens returned in career query. (`register_d8_assess_domain.ts:176`)
  - DEFECT-001: 91.5% signal grounding orphaned.
  - Contradictions: 1,034 raw UUID pairs, resolution_hint=null. (`register_d8_assess_domain.ts:151`)
- **ranking_logic:** As-is: degenerate (AV bindu counts dominate). To-be [NATIVE-RATIFY]: the composite ranking (I-1) must be applied before assess_* can synthesize.
- **output_contract (current):** Large ingredient dump. {signals[], activating_dasha: {count:0}, lenses[], cdlm_cells[], contradictions: [{uuid_a, uuid_b, resolution_hint: null}]}.
- **output_contract (to-be):** Bounded synthesis: {domain, verdict: "...", confidence: 0.x, key_factors: [ranked by composite], dasha_window: {lord, period, activation_strength}, tensions: [resolved_contradiction summary], citations: [2–3 sūtras], size: ≤6,000 tokens}.
- **as_is_vs_to_be:** Major rework required (I-1 ranking + I-2 synthesis + I-3 bounding + fix domain filter + fix L3 populate).
- **mode_notes:** As-is: neither mode is served. To-be: BULK = the reconciled bounded verdict; AGENTIC = verdict + drill pointers to evidence.

**Career-specific note (43):** D10 (Dashamsha) referenced as drill URI but not returned inline. Key career kārakas: 10th lord + Saturn. `register_d8_assess_domain.ts:313,338,355`
**Health-specific note (44):** 1st/6th/8th lords via drill; medical nakshatra not included (bg_medical_mappings UNCOVERED). `register_d8_assess_domain.ts:376,418`
**Wealth-specific note (45):** 2nd/11th lords + Jupiter via drill. `register_d8_assess_domain.ts:463,480`

**Card 46: `yoga_activation_by_dasha` → `kala_yoga_activation_get`**
- **astrological_purpose:** Find which yogas in the chart are ripening in the current/specified dasha period — the "what's cooking now" tool.
- **source_assets:** bo_laksana (bodha_msr_signals WHERE signal_type_class='yoga') JOIN ka_kalasutra (kala_activation).
- **CRITICAL STATUS:** kala_activation = 0 rows for native chart → returns 0 activated yogas. `register_d8_assess_domain.ts:628-629`. Structurally correct; operationally empty until L3 built.
- **output_contract (to-be when built):** {dasha_period, activated_yogas: [{yoga_name, signal_id, activation_strength, ripening_window, karaka_planets}]}.

**Card 47: `get_cgm_subgraph` → `bodha_graph_get`** — covered above in GROUP 4.

**Card 48: `query_chart_facts` → `ganita_facts_search`** — covered above in GROUP 4.

**Card 49: `vector_search` → `bodha_vector_search`** — covered above in GROUP 4.

---

### GROUP 9: L0FR Remedy Tools Summary (7 tools)

Cards 16–22 covered in GROUP 2 (ref_* tools). The 7 remedy tools form a complete corpus interface:
- **Global corpus:** ref_remedies_search (#16), ref_remedies_list (#18), ref_remedy_get (#19), ref_tantric_remedies_search (#20), ref_planet_remedies_get (#21), ref_mantras_search (#22).
- **Chart-scoped:** bodha_remedies_search (#17, same defect as bodha_remedies_get).
- **Composition:** Use global corpus to discover; use chart-scoped for relevance ranking (once de-degenerated).

---

## §B3 — Reasoning Workflow Library

For each insight-type: the acharya's canonical traversal as an ordered tool-chain, rendered in both BULK (one-shot organized briefing) and AGENTIC-LOOP (bounded drill graph) forms.

---

### Workflow 1: INTERPRETATION (spearhead — deep proof in §4B)

**BULK bundle (Gemini/DeepSeek one-shot):**
```
Step 1 [ORIENT]:    nav_charts_list → nav_chart_select → ref_assets_list
Step 2 [PORTRAIT]:  bodha_orientation_get (UCD — the chart's holistic portrait)
Step 3 [DOMAIN]:    bodha_domain_reading_get (domain lenses + CDLM)  [DEFECT: fix domain filter first]
Step 4 [SIGNALS]:   bodha_signals_get (top-50 by composite score, domain+tier filter)  [DEFECT: ranking fix first]
Step 5 [SPINE]:     ganita_positions_get (natal positions; identify kārakas)
Step 6 [STRENGTH]:  query_chart_facts (fact_category: shadbala) [gap: add ganita_strength_get]
Step 7 [STRUCTURE]: query_chart_facts (fact_category: yoga_firing, aspect_firing)
Step 8 [GRAPH]:     bodha_graph_traverse (2-hop from domain kārakas)
Step 9 [TIME]:      ganita_dashas_get (current period; ±2y window)
Step 10 [CITE]:     ref_citation_get (1–3 citations for primary yogas)
Step 11 [QUALITY]:  bodha_quality_get (check build coverage before claiming)
→ ASSEMBLE: Structured briefing organized by reasoning chain: kāraka → bhava → lord → dispositor → yoga → dasha → verdict
```

**AGENTIC-LOOP path (Claude/GPT iterative):**
```
ORIENT:   nav_chart_select → bodha_orientation_get        [cheap; always first]
ASSESS:   intent_classify → route to domain               [classify query]
KĀRAKA:   ganita_positions_get → identify domain kāraka   [e.g., Saturn for career]
STRENGTH: query_chart_facts (shadbala for kāraka)         [is the kāraka strong?]
YOGAS:    bodha_signals_get (filter: domain, yoga class, top-20)
DRILL:    IF yoga found → ref_citation_get for that yoga  [cite śāstra]
          IF contradiction found → bodha_graph_traverse (resolve)
TIME:     ganita_dashas_get (current lord + period)
VERDICT:  synth_career_assess (or relevant domain) as cross-check
CITE:     ref_citation_get (final grounding)
```

---

### Workflow 2: PREDICTION

**BULK bundle:**
```
Step 1 [ORIENT]:    bodha_orientation_get
Step 2 [ANCHORS]:   phala_anchors_get (formal prediction record)
Step 3 [SIGNALS]:   bodha_signals_get (domain filter; predictive signal types)
Step 4 [TIMING]:    kala_windows_get (active signals now)   [EMPTY until L3 built]
Step 5 [DASHAS]:    ganita_dashas_get (current + upcoming ±3y)
Step 6 [CALIBRATE]: mimamsa_calibration_get (historical accuracy)
→ ASSEMBLE: Claim + evidence + window + falsifier + confidence
```

**AGENTIC-LOOP:**
```
ORIENT: bodha_orientation_get
CLAIM:  phala_anchors_get (check existing formal anchors first)
IF GAPS:
  SIGNAL: bodha_signals_get (domain, predictive type)
  TIMING: kala_windows_get → ganita_dashas_get
  TRANSIT: ref_position_get (upcoming transit dates)
FALSIFY: phala_anchors_get (falsifier field)
CALIBRATE: mimamsa_calibration_get
RECORD (after outcome): mimamsa_outcome_record
```

---

### Workflow 3: TIMING

**BULK bundle:**
```
Step 1 [DASHAS]:    ganita_dashas_get (full chain, current + ±5y)
Step 2 [WINDOWS]:   kala_windows_get (active activation windows)  [EMPTY until L3]
Step 3 [YOGA]:      kala_yoga_activation_get (which yogas ripening now)  [EMPTY]
Step 4 [TRANSIT]:   ref_transit_get (key planet transits for date range)
Step 5 [MUHURTA]:   phala_muhurta_select (if specific action timing needed)
→ ASSEMBLE: Window table sorted by composite activation strength × dasha alignment
```

**AGENTIC-LOOP:**
```
WINDOW_CHECK: kala_windows_get → if empty, fall back to:
DASHA_MAP:    ganita_dashas_get → identify upcoming lord transitions
TRANSIT_SCAN: ref_transit_get (Jupiter/Saturn/Rahu moving into key signs)
YOGA_CHECK:   kala_yoga_activation_get → for ripening yogas
MUHURTA:      phala_muhurta_select (if specific action)
```

---

### Workflow 4: GUIDANCE / REMEDIATION

**BULK bundle:**
```
Step 1 [DIAGNOSE]:  synth_{domain}_assess (identify afflictions)  [fix VOLUME first]
Step 2 [CHART_REM]: bodha_remedies_get (chart-scoped resonances)  [DEFECT: scores degenerate]
Step 3 [GLOBAL]:    ref_remedies_search (by affliction type)
Step 4 [PLANET]:    ref_planet_remedies_get (for afflicted kārakas)
Step 5 [MITIGATION]: phala_mitigation_get (formal mitigation map)
Step 6 [MANTRAS]:   ref_mantras_search (for key kārakas)
→ ASSEMBLE: Ranked prescription by (resonance × ease × timing)  [NATIVE-RATIFY: weighting]
```

**AGENTIC-LOOP:**
```
DIAGNOSE: bodha_signals_get (affliction type signals for domain)
SEVERITY: query_chart_facts (dignity + shadbala of afflicted planet)
CHART_REM: bodha_remedies_get → rank by resonance (once de-degenerated)
DRILL: read_remedy (full details on top-3)
TIMING: phala_muhurta_select (when to begin remedy)
```

---

### Workflow 5: RECTIFICATION

**BULK bundle:**
```
Step 1 [LEL]:       mimamsa_lel_search (all known life events)
Step 2 [DASHAS]:    ganita_dashas_get (full Vimshottari chain)
Step 3 [ANCHORS]:   phala_anchors_get (predicted event windows)
Step 4 [CALIBRATE]: mimamsa_calibration_get (LEL-fit score)
→ ASSEMBLE: LEL-event × dasha-window fit table; highlight mismatches
```

**AGENTIC-LOOP:**
```
LEL_LOAD:  mimamsa_lel_search
FOR_EACH_EVENT:
  DASHA:   ganita_dashas_get (what period was active?)
  FIT:     check event date vs predicted window (compute inline)
SUMMARY:   mimamsa_calibration_get (global fit score)
RECTIFY:   IF fit < 0.6, flag for native review  [NATIVE-RATIFY: fit threshold]
```

---

## §B4 — The Unified Output Envelope

One schema that every tool should conform to, enabling composable, bounded, weighted output the LLM can synthesize.

```typescript
interface RetrievalEnvelope {
  // Identity
  tool_uri:      string;       // marsys://tool/L2/query_signals
  chart_id:      string | null; // null for global tools
  query_context: {
    domain:        string | null;  // "career", "marriage", etc.
    insight_type:  "interpretation" | "prediction" | "timing" | "guidance" | "rectification";
    response_format: "minimal" | "standard" | "full"; // BULK=full, AGENTIC=standard/minimal
  };

  // Ranked content — organized by acharya reasoning chain
  content: {
    // Primary content: organized by reasoning chain (not flat rows)
    karaka_context:     Record<string, unknown>[];  // relevant kārakas for domain
    natal_condition:    Record<string, unknown>[];  // strength/dignity of key planets
    structural_factors: Record<string, unknown>[];  // yogas, aspects, argala
    temporal_context:   Record<string, unknown>[];  // current dasha + activation
    verdict:            string | null;              // synthesis (null if tool doesn't synthesize)
    raw_rows:           Record<string, unknown>[];  // paginated evidence rows
  };

  // Ranking: composite score per item
  ranking_basis: {
    topic_relevance:   number;  // 0–1: is this a significator of the query?
    intrinsic_strength: number; // 0–1: dignity/shadbala
    structural_role:   number;  // 0–1: yoga/argala/centrality
    temporal_activation: number; // 0–1: currently live via dasha/transit
    composite:         number;  // weighted sum [NATIVE-RATIFY: weights]
  } | null; // null for tools without meaningful ranking (navigation, meta)

  // Grounding: citations + provenance
  grounding: {
    fact_ids_resolved: string[];   // fact_ids that resolved to chart_facts
    fact_ids_orphaned: string[];   // fact_ids that didn't resolve (DEFECT-001)
    citations:         {source: string; verse: string; content: string}[];
    provenance_tables: string[];
    grounding_score:   number;     // fraction resolved (target: >0.80)
  };

  // Bounds + drill
  pagination: {
    total_available: number;
    returned:        number;
    next_cursor:     string | null;
  };
  drill_pointers: {
    uri:     string;   // marsys://tool/L1/get_strength?chart_id=...
    reason:  string;   // "drill into shadbala for Saturn (the career kāraka)"
  }[];

  // Insight metadata
  insight_role:    string[];   // ["interpretation", "prediction"]
  judgment_flags:  string[];   // "ranking_degenerate", "domain_filter_inert", "L3_empty", etc.
  is_error:        boolean;
  error_message:   string | null;
}
```

**Key design choices:**
- `content` is organized by the acharya reasoning chain (kāraka → natal_condition → structural → temporal → verdict), not flat rows.
- `ranking_basis` is always returned with its components visible — the LLM can see why something ranked high.
- `judgment_flags` give honest self-reporting (the current `register_d8_assess_domain.ts` self-reporting pattern preserved and formalized).
- `response_format` lever controls BULK vs AGENTIC depth: `full` (all fields), `standard` (top-20 ranked items + drill pointers), `minimal` (verdict + top-5 + drill pointers).
- `drill_pointers` replace unbounded dumps — return a bounded set, point to more.

**Current tools → envelope mapping:**
- Tools with ✅ quality rating (event_anchors, mitigation_map, muhurta_finder): already conform except for `ranking_basis` and `drill_pointers` fields.
- `bodha_signals_get` (#32): needs ranking_basis (composite vs degenerate salience) + response_format cap.
- `assess_*` (#42-45): needs complete rework — add verdict, fix ranking, bound, add drill_pointers.
- `ganita_positions_get` (#34): needs `karaka_context` annotation inline.

---

## §B5 — Synthesis-Quality Eval Harness

### Design

**Structure:** Golden questions × 5 insight-types × 2 charts (482012f1 native, 1c826d5a Abhinandan) × 4 LLM families (Gemini 2.5 Pro, Claude Sonnet 4.6, GPT-4o, DeepSeek V4 Pro).

**Scores per eval run:**
- **VOLUME (0–3):** 0=overflow/too short; 1=acceptable; 2=appropriate; 3=optimal density
- **RELEVANCE (0–3):** 0=off-topic; 1=partially relevant; 2=relevant; 3=precisely targeted
- **ACCURACY (0–3):** 0=factually wrong; 1=partially correct; 2=correct; 3=acharya-verified
- **RANKING (0–3):** 0=wrong order (trivial before significant); 1=partially correct; 2=significant before trivial; 3=exact acharya weighting [NATIVE-RATIFY]
- **INSIGHT_QUALITY (0–3):** 0=no insight; 1=factual; 2=interpretive; 3=acharya-grade synthesis

**Max score per case:** 15. Target "superlative": ≥13.

### Golden Questions

| # | Question | Insight-Type | Chart | Expected Tool Chain | Golden Answer |
|---|---|---|---|---|---|
| Q1 | "What is the natal condition for career? What are the key yogas and is Saturn strong?" | Interpretation | 482012f1 | orient→domain_reading→signals(career)→positions→strength(Saturn)→graph→dashas→citation | [NATIVE-RATIFY] |
| Q2 | "What career events should I expect in the next 3 years?" | Prediction | 482012f1 | phala_anchors→kala_windows→dashas→calibration | [NATIVE-RATIFY] |
| Q3 | "When is the best time to start a new business venture?" | Timing | 482012f1 | kala_yoga_activation→dashas→transit→muhurta | [NATIVE-RATIFY] |
| Q4 | "Saturn is placed in the 10th house. What remedies apply?" | Guidance | 482012f1 | diagnose(signals)→bodha_remedies→planet_remedies→mantras→mitigation | [NATIVE-RATIFY] |
| Q5 | "How well does the chart fit the birth time?" | Rectification | 482012f1 | lel→dashas→anchors→calibration | [NATIVE-RATIFY] |
| Q6 | "What is the most defining yoga in this chart?" | Interpretation | 482012f1 | signals(signature_tier='defining')→graph(yoga)→citation | [NATIVE-RATIFY] |
| Q7 | "Is the marriage timing for 2026–2028 favorable?" | Prediction | 482012f1 | assess_marriage→kala_windows→dashas | [NATIVE-RATIFY] |
| Q8 | "What does the 10th house show for career? Use the D10." | Interpretation | 482012f1 | positions→query_chart_facts(D10 varga_position)→signals(10th)→graph | [NATIVE-RATIFY] |
| Q9 | "What was happening astrologically during 2005–2008?" (a known period) | Timing | 482012f1 | dashas(2005-2008)→lel(period filter)→signals(active)→anchors | [NATIVE-RATIFY] |
| Q10 | "What is the cross-domain link between career and wealth for this chart?" | Interpretation | 482012f1 | cdlm→cgm_subgraph→signals(career∩wealth) | [NATIVE-RATIFY] |

All **Golden Answers** are `[NATIVE-RATIFY]` — an acharya defines what "correct" looks like for chart 482012f1. The instrument's target is to produce text that an independent acharya reviewing blindly scores ≥13/15.

### Eval Harness Implementation

```python
# platform/src/lib/retrieval/eval/harness.ts (existing skeleton)
# Extend with:
#
# for question in GOLDEN_QUESTIONS:
#   for chart_id in [NATIVE_CHART, NON_NATIVE_CHART]:
#     for model_family in [GEMINI, CLAUDE, GPT, DEEPSEEK]:
#       for mode in [BULK, AGENTIC]:
#         result = run_workflow(question, chart_id, model_family, mode)
#         score = score_against_golden(result, question.golden_answer[chart_id])
#         save_eval_record(question, chart_id, model_family, mode, result, score)
```

---

## §4B — The Spearhead: INTERPRETATION — Deep End-to-End Proof

> **[NATIVE-RATIFY: confirm INTERPRETATION as spearhead or redirect.]**
> Spearhead means: the cards, workflow, envelope, and eval for INTERPRETATION are proved end-to-end on chart 482012f1, serving as the replicable template for the other four insight-types.

### The Question

**"What is the natal condition for career? What yogas are present, is Saturn strong, and what is the overall verdict?"**

Chart: 482012f1 (Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar). Known: Lagna=Aries, Sun=Capricorn/Shravana, Moon=Purva Bhadrapada/Aquarius.

### Step-by-Step Traversal (AGENTIC-LOOP mode)

**Step 1 — Session + Orient (2 calls)**
```
call: nav_chart_select("482012f1")
  → chart_id confirmed: 482012f1
call: bodha_orientation_get(chart_id="482012f1")
  → UCD portrait: [dominant themes, lagna lord Mars, chart period context]
  → LLM reads: "Aries lagna; Mars is lagna lord. 10th from Aries = Capricorn. Sun is in 10th."
```

**Step 2 — Domain (1 call)**
```
call: bodha_domain_reading_get(chart_id, domain="career")
  → [EXPECTED DEFECT: returns chart-wide lenses, not career-scoped]
  → LLM should detect judgment_flag="domain_filter_inert" and proceed directly to signals
```

**Step 3 — Signals (1 call)**
```
call: bodha_signals_get(chart_id, domain="career", limit=50)
  → [EXPECTED DEFECT: top signals are AV bindu counts, ZERO raja-yogas]
  → LLM should detect judgment_flag="ranking_degenerate" and filter for signal_type_class="yoga" manually
  → Career-relevant signals to find (with correct ranking once fixed):
    - Sun in 10th (Capricorn) — 10th house lord = Saturn — career kāraka
    - Saturn aspects 10th from wherever placed (need get_positions to know Saturn's house)
```

**Step 4 — Natal Positions (1 call)**
```
call: ganita_positions_get(chart_id, ayanamsha_id="lahiri_chitrapaksha")
  → positions: Sun=Capricorn(10th), Moon=Aquarius(11th), Lagna=Aries(1st)
  → Saturn: [position to read from output — must consult actual chart_facts]
  → Note: Lagna=Aries → 10th lord=Saturn; Saturn's position tells career story
```

**Step 5 — Strength (1 call — workaround)**
```
call: query_chart_facts(chart_id, fact_category="shadbala")
  → [if shadbala facts exist: read Saturn's total shadbala]
  → [if empty: note gap, fallback to dignity assessment]
call: query_chart_facts(chart_id, fact_category="yoga_firing")
  → [check if any raja-yoga or dhana-yoga fires involving Saturn/10th]
```

**Step 6 — Structural (1 call)**
```
call: bodha_graph_traverse(chart_id, start_entity="Saturn", depth=2)
  → CGM causal chain for Saturn: what Saturn influences, what influences Saturn
  → Identifies key contradictions if any
```

**Step 7 — Temporal (1 call)**
```
call: ganita_dashas_get(chart_id, current_date="2026-07-02")
  → Current Maha-Dasha: [read from output]
  → Does the current dasha lord have career significance?
```

**Step 8 — Citation (1 call)**
```
call: ref_citation_get(query="10th house career Saturn lord Capricorn career yoga")
  → 2–3 relevant BPHS/Phaladeepika citations
```

### Sample Output (current state — expected defects)

```
CAREER INTERPRETATION for chart 482012f1

ORIENT: Aries lagna; Mars is lagna lord.

DOMAIN READING: ⚠️ Domain filter inert — returning chart-wide lenses (not career-scoped).
Judgment flag: domain_filter_inert. Proceeding with manual career filter.

SIGNALS (career filter): ⚠️ Ranking degenerate.
Top signals by degenerate salience are AV bindu counts.
After manual filter (signal_type_class='yoga' + domains contains 'career'):
  → [Yoga signals to be listed once ranking is fixed]

POSITIONS:
  Sun: Capricorn (10th house), Shravana nakshatra
  [Saturn: <read from chart_facts>]
  Lagna: Aries; 10th lord: Saturn

STRENGTH: ⚠️ get_strength not wired; querying chart_facts shadbala directly.
  Saturn shadbala: [read from chart_facts if available]

DASHA: Current period: [read from chart_dashas]
  Career activation: kala_activation = 0 (L3 not built) — cannot confirm current activation.

CITATIONS:
  BPHS on Sun in 10th: [from ref_citation_get]

VERDICT: [placeholder — requires ranking fix + synthesis contract]
Sun in the 10th in its own (Capricorn) or exaltation house with Saturn as lord of 10th
creates the core career story. Full acharya-grade verdict requires: (1) ranking fix so
yogas surface before AV counts; (2) domain filter fix; (3) L3 build for dasha activation;
(4) synthesis contract (I-2) to produce a prose verdict. Current output = ingredient dump.
```

### Acceptance Criteria for PASS

| Criterion | Current State | Target State |
|---|---|---|
| Career-relevant signals surface (yogas, 10th lord) | ❌ AV counts dominate | ✅ Yogas + 10th lord in top-5 |
| Domain lenses are career-scoped | ❌ Chart-wide | ✅ Career lenses only |
| Saturn shadbala accessible | ⚠️ Via workaround | ✅ Via ganita_strength_get (wired) |
| Dasha activation present | ❌ L3 empty | ✅ Active signals with dasha window |
| Prose verdict generated | ❌ Ingredient dump | ✅ Bounded 3-paragraph reading |
| Citations grounded | ✅ Works | ✅ Maintained |
| Total score (5 dims × 3 max) | ~3/15 | ≥13/15 [NATIVE-RATIFY] |

### Replication Template

The INTERPRETATION spearhead workflow is the template for the other four insight-types:
1. **Orient** (bodha_orientation_get) — always first.
2. **Domain** (bodha_domain_reading_get) — route to domain-specific data.
3. **Signals** (bodha_signals_get) — ranked evidence.
4. **Positions** (ganita_positions_get) — natal spine.
5. **Strength** (ganita_strength_get — once wired) — kāraka capacity.
6. **Structure** (bodha_graph_traverse or query_chart_facts yoga_firing) — relational.
7. **Time** (ganita_dashas_get + kala_windows_get) — temporal.
8. **Cite** (ref_citation_get) — śāstra grounding.
9. **Verify** (bodha_quality_get) — build quality check.
10. **Synthesize** (bounded verdict in RetrievalEnvelope with `verdict` field populated).

Apply this pattern to PREDICTION (add phala_anchors), TIMING (add kala_windows + muhurta), GUIDANCE (add bodha_remedies after diagnosis), RECTIFICATION (add mimamsa_lel + calibration).

---

## §6 — Priority Intervention Recommendations

Sequenced by leverage × feasibility, for native sign-off:

| Priority | Intervention | What changes | Acceptance |
|---|---|---|---|
| **P1** | Wire 18 L1 capabilities as MCP tools | Add bridge entries in registry_bridge.ts for get_strength, get_argala, get_aspects, get_avasthas, get_bhava_bala, get_dignity, get_dispositors, get_divisionals, get_sade_sati, get_sensitive_points, get_tara_chandra_bala, get_yoga_dosha | ganita_strength_get returns real shadbala; ganita_aspects_get returns aspect firings |
| **P2** | Fix bodha_question_lenses domain filter | Add domain column to bodha_question_lenses migration; update query_domain_reading.ts | Career query returns career lenses; progeny lens absent from career response |
| **P3** | Build L3 for native chart (482012f1) | Run kala layer build; populate kala_activation + predicates | kala_activation > 0; yoga_activation_by_dasha returns ripening yogas |
| **P4** | De-degenerate salience (ranking I-1) | Replace computed_salience with 4-dim composite in bo_laksana computation; [NATIVE-RATIFY: weights] | Top signals = yogas / 10th-lord / raja-yoga; AV bindu counts deprioritized |
| **P5** | Bound + structure assess_* tools (I-3) | Cap array responses at 50; add verdict field; add drill_pointers; remove raw UUID contradiction pairs | assess_career ≤ 100KB; includes verdict; no overflow |
| **P6** | Fix bo_upaya remedy scores | Debug constant 0.28 in remedy resonance computation | Remedy scores form real distribution; top remedies are chart-specific |
| **P7** | Add ganita_strength_get MCP bridge (P1 sub-item) | Priority within P1: connect get_strength.ts to registry bridge | Shadbala directly accessible without query_chart_facts workaround |
| **P8** | Wire mi_darshana as MCP tool | Add mimamsa_insights_get bridge to mimamsa_insight_units | The insight surface becomes accessible; L5 synthesis endpoint dark no more |

*End of RETRIEVAL_TOOL_BLUEPRINT v1.0 — Part B (ontology + 53 Capability Cards + workflow library + output envelope + eval harness + INTERPRETATION spearhead).*
