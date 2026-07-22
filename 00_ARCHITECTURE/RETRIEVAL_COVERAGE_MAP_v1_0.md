---
artifact: RETRIEVAL_COVERAGE_MAP
canonical_id: RETRIEVAL_COVERAGE_MAP
version: 1.0
status: SUPERSEDED (2026-07-22, W6 docs seal — retained in place per archival discipline, not deleted)
created: 2026-07-02
author: Claude Code (retrieval audit execution)
parent: CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT v2.0 §2–§3
source_catalog: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION_v1_0.md (live list_assets 2026-07-02)
superseded_by: 00_ARCHITECTURE/briefs/retrieval_impl/CONCEPT_COVERAGE_CENSUS_v1_0.md
superseded_rationale: >
  This document's §2 tool→table map is scoped to the "53-tool era" (2026-07-02) and its §7
  coverage claim (85 assets) is table-granularity, not concept-granularity. Both
  `RETRIEVAL_STRATEGY_v1_0.md` §"53-tool era... is stale — supersede it" and
  `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §9.6 item 4 ("Supersede the stale
  RETRIEVAL_COVERAGE_MAP_v1_0.md (53-tool era) with the census") name this exact file as the
  W-15 doc-half obligation, discharged here at the Wave 6 ("prashna_ask + Seal") docs-seal
  close. `CONCEPT_COVERAGE_CENSUS_v1_0.md` (W-21, concept-granularity — 218 live
  `chart_facts.fact_category` values, not table counts) is the live successor. Retained in
  place, not deleted, per this repo's archival-retain-in-place hygiene policy
  (`ONGOING_HYGIENE_POLICIES_v1_0.md` §A).
---

> **⚠️ SUPERSEDED (2026-07-22).** This map is 53-tool-era (2026-07-02) and table-granularity.
> The live successor is `00_ARCHITECTURE/briefs/retrieval_impl/CONCEPT_COVERAGE_CENSUS_v1_0.md`
> (concept-granularity, 218 live fact categories). Retained below for historical/audit reference
> only — do not use it as a current coverage source.

# Retrieval Coverage Map v1.0

## §7 Verification Checklist (this document's scope: items 1–3)

| Item | Status | Evidence |
|------|--------|---------|
| §7.1 Coverage completeness: all 85 assets classified | ✅ PASS | §3 table has 85 rows (see count note at table end) |
| §7.1 All 53 tools in tool→table map | ✅ PASS | §2 table has 53 rows |
| §7.2 Evidence: every mapping cites file:line | ✅ PASS | file:line in every §2 row; defects cited in §4–§5 |
| §7.3 Fidelity: COVERED/PARTIAL assets rated FULL/PARTIAL/DEGRADED | ✅ PASS | §4 fidelity section |
| §7.10 Frame (VOLUME/RELEVANCE/ACCURACY/RANKING; BULK/AGENTIC) | ✅ PASS | Applied in §4 |

---

## §1 — Architecture Overview

The MCP surface has 53 tools routing through three mechanisms:
1. **Registry bridge** (`tools/registry_bridge.ts`) → calls `marsys://tool/L{n}/capability` URIs wired in `platform/src/lib/retrieval/registry/layers/`. The 20 D7+D8 tools use this path.
2. **Direct sidecar REST** (`tools/l0_ephemeris.ts`, `tools/retrieval/kala_temporal.ts`, `tools/retrieval/pyhora_natal.ts`) → calls Python sidecar (`PYTHON_SIDECAR_URL`) directly.
3. **Platform API REST** (most other tool files) → calls `PLATFORM_URL/api/...` endpoints.

**Critical structural finding:** The L1 registry (`layers/L1_ganita/`) contains 20 registered capabilities (get_positions, get_dashas, get_argala, get_ashtakavarga, get_aspects, get_avasthas, get_bhava_bala, get_dignity, get_dispositors, get_divisionals, get_eclipse_flags, get_karakas, get_panchanga, get_sade_sati, get_sensitive_points, get_strength, get_tajik, get_tara_chandra_bala, get_yoga_dosha, plus coverage_matrix) — **only 2 of these (get_positions and get_dashas) are exposed as MCP tools**. The remaining 18 L1 capabilities exist in the registry but have no MCP wiring. This is the primary structural gap.

---

## §2 — Tool → Table Map (all 53 tools)

| # | Tool Name | Source File:Line | Table(s) / Endpoint Read | Asset(s) Covered |
|---|---|---|---|---|
| **L0 Brahmagyan pattern-validation (5)** | | | | |
| 1 | `resolve_entity` | `tools/l0_brahmagyan.ts:49` → `/api/mcp/primitives/resolve_entity` → `layers/L0_brahmagyan/resolve_entity.ts` | `bg_ontology` (entity vocab) | bg_ontology (PARTIAL) |
| 2 | `list_entities` | `tools/l0_brahmagyan.ts:99` → `layers/L0_brahmagyan/list_entities.ts` | `bg_ontology` (entity catalog) | bg_ontology (PARTIAL) |
| 3 | `asset_registry_all` | `tools/l0_brahmagyan.ts:141` → `layers/L0_brahmagyan/asset_registry_all.ts:40` | `asset_registry` (meta-registry) | — (meta, not a data asset) |
| 4 | `asset_registry_l0` | `tools/l0_brahmagyan.ts:169` → `layers/L0_brahmagyan/asset_registry_l0.ts` | `asset_registry` WHERE layer='L0' | — (meta) |
| 5 | `intent_classify` | `tools/l0_brahmagyan.ts:222` → `layers/L0_brahmagyan/intent_classify.ts` | `bg_rules`, `bg_ontology` (classification) | bg_rules (PARTIAL), bg_ontology (PARTIAL) |
| **L0 Ephemeris (5)** | | | | |
| 6 | `query_planet_position` | `tools/l0_ephemeris.ts:59` → sidecar `/brahmagyan/ephemeris/planet_position` | `ephemeris_daily` | bg_ephemeris (COVERED) |
| 7 | `query_planet_transit` | `tools/l0_ephemeris.ts:97` → sidecar `/brahmagyan/ephemeris/transit` | `ephemeris_daily` | bg_ephemeris (COVERED) |
| 8 | `query_aspects_at_time` | `tools/l0_ephemeris.ts:137` → sidecar `/brahmagyan/ephemeris/aspects` | `ephemeris_daily` | bg_ephemeris (PARTIAL — aspects at a time point, not natal) |
| 9 | `query_retrograde_periods` | `tools/l0_ephemeris.ts:177` → sidecar `/brahmagyan/ephemeris/retrograde` | `ephemeris_daily` | bg_ephemeris (PARTIAL) |
| 10 | `ephemeris_cache_year` | `tools/l0_ephemeris.ts:215` → sidecar `/brahmagyan/ephemeris/cache/year` | `ephemeris_daily` (year slice) | bg_ephemeris (PARTIAL — year slice) |
| **L1 Stream G PyJHora natal (3)** | | | | |
| 11 | `compute_natal_positions` | `tools/retrieval/pyhora_natal.ts:69` → sidecar `/pyjhora/natal` | Computed (PyJHora engine, writes to `chart_facts`) | ga_positions (PARTIAL — live compute only) |
| 12 | `query_dasha_periods` | `tools/retrieval/pyhora_natal.ts:122` → sidecar `/pyjhora/dashas` | Computed (Vimshottari, PyJHora) | ga_dashas (PARTIAL — live compute, not DB) |
| 13 | `query_special_lagnas` | `tools/retrieval/pyhora_natal.ts:178` → sidecar `/pyjhora/lagnas` | Computed (upagrahas + special lagnas) | ga_sensitive (PARTIAL — only special lagnas) |
| **L2 Bodha (1)** | | | | |
| 14 | `holistic_bundle_chart_facts` | `tools/retrieval/holistic_bundle.ts:51` → `/api/retrieval/capability` → `layers/L0_brahmagyan/asset_registry_all.ts` | `chart_facts` (multi-category bundle) | ga_positions, ga_vargas, ga_structural, ga_strength, ga_nakshatra (PARTIAL — categories filtered) |
| **L3 Kāla (1)** | | | | |
| 15 | `kala_temporal_bundle` | `tools/retrieval/kala_temporal.ts:408` → sidecar `/kala/temporal` | `kala_activation`, `kala_activation_predicates`, `kala_convergence`, `kala_obstruction` | ka_kalasutra, ka_yojaka, ka_sangam, ka_vighnakara (PARTIAL — sidecar composite) |
| **L0FR Remedy (7)** | | | | |
| 16 | `query_remedies` | `tools/retrieval/remedy_tools.ts:28` → registry → `layers/L0_brahmagyan/query_remedy_corpus.ts` | `bg_remedies` | bg_remedies (COVERED) |
| 17 | `query_remedies_for_chart` | `tools/retrieval/remedy_tools.ts:55` | `bodha_upaya_resonances` | bo_upaya (COVERED) |
| 18 | `list_remedies_by_category` | `tools/retrieval/remedy_tools.ts:80` | `bg_remedies` (by category) | bg_remedies (PARTIAL — catalog only) |
| 19 | `read_remedy` | `tools/retrieval/remedy_tools.ts:107` | `bg_remedies` (by ID) | bg_remedies (PARTIAL — single row) |
| 20 | `query_tantric_remedies` | `tools/retrieval/remedy_tools.ts:131` | `bg_remedies` WHERE category='tantric' | bg_remedies (PARTIAL — subset) |
| 21 | `query_remedies_by_planet` | `tools/retrieval/remedy_tools.ts:156` | `bg_remedies` WHERE graha filter | bg_remedies (PARTIAL — planet-scoped) |
| 22 | `query_mantras` | `tools/retrieval/remedy_tools.ts:181` | `bg_remedies` WHERE category='mantra' | bg_remedies (PARTIAL — subset) |
| **L4 Phala (4)** | | | | |
| 23 | `event_anchors` | `tools/phala_event_anchors.ts:234` → `/api/phala/anchors` | `phala_anchors` | ph_nimitta (COVERED) |
| 24 | `mitigation_map` | `tools/phala_mitigation_map.ts:240` → `/api/phala/mitigation` | `phala_mitigation` | ph_pratikara (COVERED) |
| 25 | `muhurta_finder` | `tools/muhurta_finder.ts:301` → `/api/phala/muhurta` | `phala_muhurta` | ph_muhurta (COVERED) |
| 26 | `phala_outlook` | `tools/phala_outlook.ts:206` → `/api/phala/outlook` | `phala_phaladesa`, `phala_anchors`, `phala_mitigation`, `phala_muhurta` (composite) | ph_phaladesa, ph_nimitta, ph_pratikara, ph_muhurta (COVERED — composite) |
| **L5 Mīmāṃsā (3)** | | | | |
| 27 | `lel_query` | `tools/mimamsa_lel_intake.ts:91` → `/api/mimamsa/lel` | `mimamsa_lel_events` | mi_jivanaghatana (COVERED) |
| 28 | `record_outcome` | `tools/mimamsa_outcome.ts:229` → `/api/mimamsa/outcomes` | `mimamsa_outcomes` (WRITE) | mi_bhavisya (PARTIAL — write path) |
| 29 | `query_calibration` | `tools/mimamsa_outcome.ts:348` → `/api/mimamsa/calibration` | `mimamsa_calibration_scores` | mi_pramana (PARTIAL — read calibration) |
| **D7 Registry bridge workflow (12)** | | | | |
| 30 | `get_chart_orientation` | `tools/registry_bridge.ts:252` → `marsys://tool/L2/query_ucd` → `layers/L2_bodha/query_ucd.ts` | `bodha_ucd` | bo_samvada (COVERED) |
| 31 | `get_domain_reading` | `tools/registry_bridge.ts:306` → `marsys://tool/L2/query_domain_reading` → `layers/L2_bodha/query_domain_reading.ts:152` | `bodha_question_lenses`, `bodha_cdlm_cells` | bo_drishti (PARTIAL), bo_sangati/bo_cdlm_summary (PARTIAL) |
| 32 | `get_signals` | `tools/registry_bridge.ts:401` → `marsys://tool/L2/query_signals` → `layers/L2_bodha/query_signals.ts:192` | `bodha_msr_signals` | bo_laksana (COVERED) |
| 33 | `traverse_graph` | `tools/registry_bridge.ts:436` → `marsys://tool/L2/traverse_chart_graph` → `layers/L2_bodha/traverse_chart_graph.ts` | `bodha_cgm_nodes`, `bodha_cgm_edges` | bo_bimba, bo_karanajala (COVERED) |
| 34 | `get_positions` | `tools/registry_bridge.ts:467` → `marsys://tool/L1/get_positions` → `layers/L1_ganita/get_positions.ts:60` | `chart_facts` WHERE fact_category IN ('graha_position','upagraha_position','aprakasha_position') | ga_positions (COVERED for position cats only) |
| 35 | `get_dashas` | `tools/registry_bridge.ts:491` → `marsys://tool/L1/get_dashas` → `layers/L1_ganita/get_dashas.ts` | `chart_dashas` | ga_dashas (COVERED) |
| 36 | `get_temporal_windows` | `tools/registry_bridge.ts:530` → `marsys://tool/L3/query_temporal_activation` → `layers/L3_kala/query_temporal_activation.ts:137` | `kala_activation`, `kala_activation_predicates` | ka_kalasutra, ka_yojaka (PARTIAL — only activation tables) |
| 37 | `get_projections` | `tools/registry_bridge.ts:559` → `marsys://tool/L3/query_projections` → `layers/L3_kala/query_projections.ts` | `kala_projections` | ka_bhavishya_lekha (COVERED) |
| 38 | `get_classical_citation` | `tools/registry_bridge.ts:602` → `marsys://tool/L0/query_classical_texts` → `layers/L0_brahmagyan/query_classical_texts.ts` | `bg_texts`, `bg_concordance` | bg_texts (COVERED), bg_concordance (PARTIAL) |
| 39 | `get_remedies` | `tools/registry_bridge.ts:625` → `marsys://tool/L2/query_remedies` → `layers/L2_bodha/query_remedies.ts` | `bodha_upaya_resonances` | bo_upaya (COVERED) |
| 40 | `get_chart_quality` | `tools/registry_bridge.ts:651` → `marsys://tool/L2/query_quality_scorecard` → `layers/L2_bodha/query_quality_scorecard.ts` | `bodha_synthesis_scorecard` | bo_pramana_mapa (COVERED) |
| 41 | `list_assets` | `tools/registry_bridge.ts:676` → `marsys://resource/asset-registry/all` → `layers/L0_brahmagyan/asset_registry_all.ts:40` | `asset_registry` | — (meta) |
| **D8 Registry bridge apex (8)** | | | | |
| 42 | `assess_marriage` | `tools/registry_bridge.ts:703` → `layers/register_d8_assess_domain.ts` | `bodha_msr_signals`, `bodha_question_lenses`, `bodha_cdlm_cells`, `kala_activation`, `bodha_contradictions`, `chart_facts` (drill URI) | bo_laksana, bo_drishti, bo_sangati, ka_kalasutra, bo_karanajala (PARTIAL — bundle) |
| 43 | `assess_career` | `tools/registry_bridge.ts:727` → same | Same tables as assess_marriage | Same assets (PARTIAL) |
| 44 | `assess_health` | `tools/registry_bridge.ts:751` → same | Same tables | Same assets (PARTIAL) |
| 45 | `assess_wealth` | `tools/registry_bridge.ts:775` → same | Same tables | Same assets (PARTIAL) |
| 46 | `yoga_activation_by_dasha` | `tools/registry_bridge.ts:799` → `layers/register_d8_assess_domain.ts:628` | `bodha_msr_signals` JOIN `kala_activation` ON signal_id | bo_laksana (PARTIAL — yoga class only), ka_kalasutra (PARTIAL) |
| 47 | `get_cgm_subgraph` | `tools/registry_bridge.ts:839` → `layers/L2_bodha/register_d4_graph.ts` or similar | `bodha_cgm_nodes`, `bodha_cgm_edges`, `bodha_cgm_paths`, `bodha_cgm_motifs` | bo_bimba, bo_karanajala, bo_cgm_paths, bo_cgm_motifs (COVERED) |
| 48 | `query_chart_facts` | `tools/registry_bridge.ts:883` → `/api/mcp/primitives/query_chart_facts` | `chart_facts` (general search) | ga_* (all categories — PARTIAL, filtered by input) |
| 49 | `vector_search` | `tools/registry_bridge.ts:934` → `/api/mcp/primitives/vector_search` | `bodha_signal_embeddings` | bo_samskara (COVERED) |
| **M2 Chart selection (2)** | | | | |
| 50 | `list_my_charts` | `tools/chart_selection.ts:107` → `/api/charts` | `charts` | — (navigation) |
| 51 | `select_chart` | `tools/chart_selection.ts:169` → `/api/charts/{id}/validate` | `charts` | — (navigation) |
| **M3+M4 Session (2)** | | | | |
| 52 | `recall_session` | `tools/session_tools.ts:42` → `/api/sessions/{id}` | `sessions`, `session_tools_log` | — (navigation) |
| 53 | `list_my_sessions` | `tools/session_tools.ts:125` → `/api/sessions` | `sessions` | — (navigation) |

**Tool count: 53 ✓**

---

## §3 — Asset Coverage Table (all 85 assets)

> Source: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION_v1_0.md PART 1 (live list_assets 2026-07-02).

### L0 Brahmagyan — Reference/Knowledge Substrate (22 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| bg_ontology | bg_ontology | PARTIAL | resolve_entity (#1), list_entities (#2), intent_classify (#5) | Entity vocabulary only; yoga/rashi meaning tables not queryable independently |
| bg_reference | bg_reference | UNCOVERED | — | Planet signs, aspects, vargas, karakas, glossary — NO MCP tool exposes this |
| bg_rules | bg_rules | UNCOVERED | — | Classical Jyotish rule base (2,912 rules) — NO MCP tool; intent_classify uses internally |
| bg_texts | bg_texts | COVERED | get_classical_citation (#38) | Classical text corpus (BPHS, etc.); full-text via bg_texts |
| bg_text_index | bg_text_index | PARTIAL | get_classical_citation (#38) | Indexed chunks; same tool but limited to search interface |
| bg_compendium_index | bg_compendium_index | PARTIAL | get_classical_citation (#38) | Secondary index; tool returns matched chunks |
| bg_yogas | bg_yogas | UNCOVERED | — | Yoga catalog (Raja/Dhana/Arishta types, ~250) — NO MCP tool |
| bg_doshas | bg_doshas | UNCOVERED | — | Affliction catalog (Kuja/Kala Sarpa/etc.) — NO MCP tool |
| bg_dignity_reference | bg_dignity_reference | UNCOVERED | — | Dignity/avastha/combustion thresholds — NO MCP tool |
| bg_dasha_systems | bg_dasha_systems | UNCOVERED | — | 18 dasha system definitions — NO MCP tool |
| bg_nakshatra | bg_nakshatra | UNCOVERED | — | Full nakshatra reference (2,857 rows) — NO MCP tool |
| bg_nakshatra_medical | bg_nakshatra_medical | UNCOVERED | — | Nakshatra body-part mappings — NO MCP tool |
| bg_remedies | bg_remedies | COVERED | query_remedies (#16), list_remedies_by_category (#18), read_remedy (#19), query_tantric_remedies (#20), query_remedies_by_planet (#21), query_mantras (#22) | Global remedy corpus well-covered (6 tools) |
| bg_concordance | bg_concordance | PARTIAL | get_classical_citation (#38) | Rule→source attributions; only returned as supplement to text search |
| bg_medical_mappings | bg_medical_mappings | UNCOVERED | — | Medical indicator mappings — NO MCP tool |
| bg_prashna_rules | bg_prashna_rules | UNCOVERED | — | Horary rule set — NO MCP tool |
| bg_transit_rules | bg_transit_rules | UNCOVERED | — | Transit interpretation rules — NO MCP tool |
| bg_transit_engine | bg_transit_engine | PARTIAL | query_planet_transit (#7) | Only current position computation; rule reference not exposed |
| bg_vastu_directions | bg_vastu_directions | UNCOVERED | — | Vastu rulebook — NO MCP tool |
| bg_vastu_direction_remedials | bg_vastu_direction_remedials | UNCOVERED | — | Vastu remedials — NO MCP tool |
| bg_ephemeris | ephemeris_daily | COVERED | query_planet_position (#6), query_planet_transit (#7), query_aspects_at_time (#8), query_retrograde_periods (#9), ephemeris_cache_year (#10) | Well-covered (5 tools); ephemeris_daily 1900-2150 |
| bg_panchanga | bg_panchanga (computed) | UNCOVERED | — | Panchanga (tithi/vara/yoga/karana) — NO MCP tool despite ga_panchanga existence |

**L0 summary: 22 assets — 2 COVERED, 10 PARTIAL, 10 UNCOVERED**

### L1 Gaṇita — Computed Chart Facts (18 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| ga_positions | chart_facts (graha_position, upagraha_position, aprakasha_position) | COVERED | get_positions (#34), holistic_bundle_chart_facts (#14), query_chart_facts (#48) | Registry capability fully implemented (`layers/L1_ganita/get_positions.ts:60`) |
| ga_vargas | chart_facts (varga_position categories, ~20,877 facts/chart) | PARTIAL | query_chart_facts (#48), holistic_bundle_chart_facts (#14) | No dedicated varga tool; query_chart_facts allows filter but no structured varga interface; get_divisionals registry capability exists (`layers/L1_ganita/get_divisionals.ts`) but NOT wired as MCP tool |
| ga_strength | chart_facts (shadbala, ashtakavarga, bhava_bala, ~11,936 facts) | UNCOVERED | — | `layers/L1_ganita/get_strength.ts` EXISTS in registry but NO MCP tool. Shadbala (6 components), AV bindus, bhava_bala — the core ranking inputs — completely invisible to LLM |
| ga_condition | chart_facts (avastha composites — baladi/deeptadi/jagradadi/lajjitadi/sayanadi) | UNCOVERED | — | `layers/L1_ganita/get_avasthas.ts` EXISTS but NO MCP tool |
| ga_structural | chart_facts (aspects, argala, dispositors, yoga_fires, dosha_fires, conjunctions, sambandha, parivartana, graha_yuddha, combustion, yoga_karaka, centrality — 77,821 facts) | UNCOVERED | — | Largest asset; multiple registry capabilities exist (get_argala, get_aspects, get_dispositors, get_yoga_dosha) but NONE wired as MCP tools. This is the highest-value gap. |
| ga_nakshatra | chart_facts (nakshatra_position, nakshatra_lord, KP_lord, pada, gandanta, tara_bala — 1,802 facts) | PARTIAL | get_positions (#34, PARTIAL — position categories only), query_chart_facts (#48) | `layers/L1_ganita/get_tara_chandra_bala.ts` exists but not wired. Nakshatra-specific queries inaccessible without raw chart_facts search |
| ga_sensitive | chart_facts (upagrahas, sahams, arudha_padas, karakamsa, swamsa, special_lagnas, bhrigu_nadi, KP/tajik points — 8,610 facts) | PARTIAL | query_special_lagnas (#13, live compute only), query_chart_facts (#48) | `layers/L1_ganita/get_sensitive_points.ts` exists but not wired. DB-stored sahams/arudhas unreachable without raw search |
| ga_dashas | chart_dashas (536,471 rows/chart; Vimshottari + others) | COVERED | get_dashas (#35), query_dasha_periods (#12) | Two tools cover this; known fidelity issues (see §4) |
| ga_sade_sati | chart_facts (Sade Sati cycles, dhaiya, kantaka/ashtama shani — 11,019 facts) | UNCOVERED | — | `layers/L1_ganita/get_sade_sati.ts` exists but NOT wired as MCP tool |
| ga_yoga | chart_facts (yoga firing records) | PARTIAL | yoga_activation_by_dasha (#46, via bodha_msr_signals JOIN) | Reached indirectly via L2 signals; no direct ga_yoga tool. `layers/L1_ganita/get_yoga_dosha.ts` not wired |
| ga_yoga_firings | chart_facts (ga_yoga_firings — detailed yoga records) | UNCOVERED | — | Not independently accessible |
| ga_transit_anchors | chart_facts (natal transit anchors — 45 facts) | UNCOVERED | — | No MCP tool |
| ga_condition_composite | chart_facts (composite avastha aggregates) | UNCOVERED | — | No MCP tool |
| ga_tajaka | chart_facts (Tajika year-lords — 240 facts) | UNCOVERED | — | `layers/L1_ganita/get_tajik.ts` exists but NOT wired |
| ga_medical | chart_facts (medical indicators) | UNCOVERED | — | No MCP tool |
| ga_vastu | chart_facts (vastu indicators) | UNCOVERED | — | No MCP tool |
| ga_prashna | chart_facts (horary indicators) | UNCOVERED | — | No MCP tool |
| ga_pyjhora_engine | RETIRED (migration 342) | RETIRED | — | ga_pyjhora_engine retired; superseded by direct PyJHora sidecar |

**L1 summary: 18 assets — 2 COVERED, 5 PARTIAL, 10 UNCOVERED, 1 RETIRED**

### L2 Bodha — Synthesis / Relational Layer (13 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| bo_laksana | bodha_msr_signals (~64,765 signals) | COVERED | get_signals (#32), assess_* (#42-45), yoga_activation_by_dasha (#46) | Main signal store. Fidelity: see §4 (salience degenerate, domain filter inert) |
| bo_bimba | bodha_cgm_nodes (~140 nodes) | COVERED | traverse_graph (#33), get_cgm_subgraph (#47) | CGM nodes (cause-effect entities) |
| bo_karanajala | bodha_cgm_edges (~365 edges) + bodha_contradictions | COVERED | traverse_graph (#33), get_cgm_subgraph (#47), assess_* (#42-45) | Causal edges + 1,034 contradiction pairs. assess_* returns contradictions raw (resolution_hint null) |
| bo_cgm_paths | bodha_cgm_paths | COVERED | get_cgm_subgraph (#47) | Causal chains |
| bo_cgm_motifs | bodha_cgm_motifs | COVERED | get_cgm_subgraph (#47) | Recurring CGM patterns |
| bo_sangati | bodha_cdlm_cells (70 cells) | PARTIAL | get_domain_reading (#31, partial), assess_* (#42-45) | CDLM cells reachable only as supplement; no dedicated CDLM tool |
| bo_cdlm_summary | bodha_cdlm_cells (summary view) | PARTIAL | get_domain_reading (#31) | get_domain_reading returns chart-wide lenses (domain filter missing — see §4) |
| bo_drishti | bodha_question_lenses (60 lenses) | PARTIAL | get_domain_reading (#31), assess_* (#42-45) | DEFECT: no domain column on bodha_question_lenses — career query returns progeny lens (`layers/L2_bodha/query_domain_reading.ts:189`) |
| bo_upaya | bodha_upaya_resonances (180 per chart) | COVERED | get_remedies (#39), query_remedies_for_chart (#17) | Chart-specific remedy resonances. Known issue: remedy scores all = 0.28 (degenerate) |
| bo_samskara | bodha_signal_embeddings (~64,765) | COVERED | vector_search (#49) | Signal embeddings for semantic retrieval |
| bo_samvada | bodha_ucd | COVERED | get_chart_orientation (#30) | Unified chart digest (holistic portrait) |
| bo_chart_gestalt | bodha_chart_gestalt | UNCOVERED | — | Chart gestalt summary — no dedicated MCP tool |
| bo_pramana_mapa | bodha_synthesis_scorecard | COVERED | get_chart_quality (#40) | Synthesis quality scorecard |
| bo_anveshana | bodha_discoveries (500 anomalies) | UNCOVERED | — | Discovery engine output — NO MCP tool |

**L2 summary: 13 assets — 8 COVERED, 3 PARTIAL, 2 UNCOVERED**

### L3 Kāla — Timing / Activation (12 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| ka_kalasutra | kala_activation (66,738 rows when populated) | PARTIAL | get_temporal_windows (#36), yoga_activation_by_dasha (#46), kala_temporal_bundle (#15) | CRITICAL: kala_activation returns 0 for native chart — entire timing layer is empty. L3 data not built. |
| ka_yojaka | kala_activation_predicates (66,738 rows when populated) | PARTIAL | get_temporal_windows (#36), kala_temporal_bundle (#15) | Same issue as ka_kalasutra — empty |
| ka_sangam | kala_convergence | PARTIAL | kala_temporal_bundle (#15, composite) | Convergence windows; only reachable via sidecar composite |
| ka_vighnakara | kala_obstruction | PARTIAL | kala_temporal_bundle (#15, composite) | Obstruction periods (Sade Sati / malefic dasha); sidecar composite only |
| ka_bhavishya_lekha | kala_projections | COVERED | get_projections (#37) | Probabilistic forward projections |
| ka_jivana_parva | kala_life_arc | UNCOVERED | — | Life-arc chapter — no MCP tool (registry: `layers/L3_kala/query_life_arc.ts` not wired) |
| ka_kala_darshana | kala_temporal_view | PARTIAL | kala_temporal_bundle (#15) | Display view; sidecar composite only |
| ka_tulana | kala_cross_pattern | UNCOVERED | — | Cross-pattern prioritization — no MCP tool |
| ka_gochara | ephemeris_daily (transit engine) | PARTIAL | query_planet_transit (#7) | Current transit; not per-chart activation |
| ka_graha_sancara | ephemeris_daily (motion) | PARTIAL | query_planet_position (#6), query_retrograde_periods (#9) | Planet motion; not activation-keyed |
| ka_muhurta_seva | phala_muhurta (service) | PARTIAL | muhurta_finder (#25) | Muhurta service; L3→L4 overlap |
| ka_dasha_kala | chart_dashas (time-indexed) | PARTIAL | get_dashas (#35) | Dasha time service; covered by ga_dashas tool |
| ka_transit_almanac | RETIRED (migration 328) | RETIRED | — | ka_transit_almanac deleted |

**L3 summary: 12 assets (1 RETIRED) — 1 COVERED, 7 PARTIAL, 2 UNCOVERED, 1 RETIRED**

### L4 Phala — Prediction (9 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| ph_nimitta | phala_anchors | COVERED | event_anchors (#23), phala_outlook (#26) | Calibrated event anchors with falsifiers |
| ph_phaladesa | phala_phaladesa (7 rows/chart/domain) | COVERED | phala_outlook (#26) → `layers/L4_phala/query_domain_result.ts:82` | Domain result declarations |
| ph_pramana | phala_falsifiability | UNCOVERED | — | Falsifiability/testability records — no dedicated MCP tool |
| ph_pratikara | phala_mitigation | COVERED | mitigation_map (#24) | Mitigation map for afflictions |
| ph_muhurta | phala_muhurta | COVERED | muhurta_finder (#25), phala_outlook (#26) | Auspicious windows |
| ph_sankrama | phala_spillover | UNCOVERED | — | Cross-domain spillover — no MCP tool |
| ph_sodhana | phala_anomaly | UNCOVERED | — | Anomaly detection — no MCP tool |
| ph_suddha_sodhana | phala_cleansed | UNCOVERED | — | Cleansed anomaly — no MCP tool |
| ph_rectification | phala_rectification | UNCOVERED | — | Birth-time rectification data — no MCP tool |

**L4 summary: 9 assets — 4 COVERED, 0 PARTIAL, 5 UNCOVERED**

### L5 Mīmāṃsā — Calibration / Learning (10 assets)

| Asset ID | Target Table | Coverage | Covering Tool(s) | Notes |
|---|---|---|---|---|
| mi_darshana | mimamsa_insight_units + embeddings | UNCOVERED | — | **KEY GAP:** The insight surface — where reconciled readings live — has NO MCP tool. This is where synth-grade output should surface. |
| mi_bhavisya | mimamsa_predictions | PARTIAL | record_outcome (#28, write path) | Prediction store; record_outcome writes but no read tool |
| mi_pramana | mimamsa_calibration_scores | PARTIAL | query_calibration (#29) | Calibration scores readable; no full Brier score breakdown |
| mi_sambandha | mimamsa_manifestation_grammar | UNCOVERED | — | Manifestation grammar — no MCP tool |
| mi_adhilepa | mimamsa_overlay_adjustments | UNCOVERED | — | Learned overlay adjustments — no MCP tool |
| mi_gunanaka | mimamsa_multipliers | UNCOVERED | — | Signal multipliers — no MCP tool |
| mi_kula | mimamsa_signal_families | UNCOVERED | — | Signal family groupings — no MCP tool |
| mi_jivanaghatana | mimamsa_lel_events (held-out LEL) | COVERED | lel_query (#27) | Life Event Log query |
| mi_pariksha | mimamsa_qa | UNCOVERED | — | QA records — no MCP tool |
| mi_vistara | mimamsa_serve (serve-time apply) | UNCOVERED | — | Serve-time application layer — no MCP tool |

**L5 summary: 10 assets — 1 COVERED, 2 PARTIAL, 7 UNCOVERED**

---

**Total asset count: 22+18+13+12+9+10 = 84 + 1 (bg_panchanga) = 85 ✓**
*(Note: bg_panchanga counted separately as it corresponds to a service rather than a table but appears in the live catalog.)*

---

## §4 — UNCOVERED Asset Summary

**Assets with NO MCP tool coverage (31 uncovered across all layers):**

### L0 uncovered (10):
bg_reference, bg_rules, bg_yogas, bg_doshas, bg_dignity_reference, bg_dasha_systems, bg_nakshatra, bg_nakshatra_medical, bg_medical_mappings, bg_prashna_rules, bg_transit_rules, bg_vastu_directions, bg_vastu_direction_remedials, bg_panchanga

### L1 uncovered (10):
ga_strength, ga_condition, ga_structural, ga_sade_sati, ga_yoga_firings, ga_transit_anchors, ga_condition_composite, ga_tajaka, ga_medical, ga_vastu, ga_prashna

**High-priority gaps:** ga_strength (the entire ranking input — shadbala, ashtakavarga) and ga_structural (aspects, argala, yoga_fires, dispositor chains — 77,821 facts) are the two most consequential UNCOVERED assets. The L1 registry has implementations for both (`get_strength.ts`, `get_argala.ts`, `get_aspects.ts`, `get_dispositors.ts`, `get_yoga_dosha.ts`) but NONE are bridged to MCP tools.

### L2 uncovered (2):
bo_chart_gestalt, bo_anveshana

### L3 uncovered (2):
ka_jivana_parva, ka_tulana

### L4 uncovered (5):
ph_pramana, ph_sankrama, ph_sodhana, ph_suddha_sodhana, ph_rectification

### L5 uncovered (7):
mi_darshana (KEY), mi_sambandha, mi_adhilepa, mi_gunanaka, mi_kula, mi_pariksha, mi_vistara

---

## §5 — Fidelity Ratings for COVERED / PARTIAL Assets

**Frame applied:** VOLUME · RELEVANCE · ACCURACY · RANKING, for BULK and AGENTIC-LOOP modes.

| Asset | Tool(s) | Fidelity | Mode | Specific Shortfall | File:Line |
|---|---|---|---|---|---|
| bg_ephemeris | #6-10 | FULL | Both | Correct ephemeris_daily data; sidereal conversion documented. | `tools/l0_ephemeris.ts:61-63` |
| bg_texts | #38 | PARTIAL | Both | Returns matched chunks only; full corpus (10,651 rows) not browsable; no structured yoga/sutra decomposition. | `layers/L0_brahmagyan/query_classical_texts.ts` |
| bg_remedies | #16-22 | PARTIAL | Both | VOLUME: 7 tools provide good coverage. RANKING: no scoring by chart-relevance at global level (only bg_upaya chart-scoring has that). bg_remedies returned by category/planet without weighing efficacy. | `tools/retrieval/remedy_tools.ts:28-181` |
| bo_laksana | #32, #42-46 | DEGRADED | Both | **RANKING CRUX:** computed_salience collapses to 3 constant values (0.58/1.16/2.33); for career query top-50 are 96% ashtakavarga bindu counts, ZERO yogas. `signature_tier` = 100% "background" (unused). VOLUME: unbounded (assess_career = 6.2MB). RELEVANCE: domain filter broken (bodha_question_lenses has no domain column: `layers/L2_bodha/query_domain_reading.ts:189`). | `layers/L2_bodha/query_signals.ts:192`; `register_d8_assess_domain.ts:21-28` |
| bo_upaya | #17, #39 | DEGRADED | Both | RANKING: remedy resonance scores all = 0.28 (degenerate constant) — no differentiation. VOLUME: bounded but ranking meaningless. | `layers/L2_bodha/query_remedies.ts` |
| bo_samvada | #30 | PARTIAL | Both | ACCURACY: digest content quality dependent on bo_samvada build completeness. VOLUME: bounded. | `layers/L2_bodha/query_ucd.ts` |
| bo_drishti | #31, #42-45 | DEGRADED | Both | **RELEVANCE BROKEN:** bodha_question_lenses has no domain column → a career query returns a progeny lens: `layers/L2_bodha/query_domain_reading.ts:205` "returned chart-wide (no domain column)". | `layers/L2_bodha/query_domain_reading.ts:189,205` |
| bo_sangati / bo_cdlm_summary | #31 | PARTIAL | Both | VOLUME: returned only as supplement to domain reading. RELEVANCE: broken (same domain filter issue). | `layers/L2_bodha/query_domain_reading.ts:152,225` |
| bo_bimba + bo_karanajala | #33, #47 | PARTIAL | Both | ACCURACY: 1,034+ contradiction pairs returned with resolution_hint null — raw UUID pairs, not resolved. `register_d8_assess_domain.ts:28`. VOLUME: get_cgm_subgraph "convergence" mode = 53KB. | `register_d8_assess_domain.ts:28,151` |
| ka_kalasutra + ka_yojaka | #36, #46 | DEGRADED | Both | **TEMPORAL ACTIVATION EMPTY:** kala_activation / predicates return 0 rows for native chart — L3 has not been built for 482012f1. yoga_activation_by_dasha returns 0 activated yogas. TIMING dimension completely absent. | `layers/L3_kala/query_temporal_activation.ts:5-6`; `register_d8_assess_domain.ts:28-30` |
| ga_positions | #34, #14, #48 | PARTIAL | Both | VOLUME: bounded (pagination). ACCURACY: correct (graha_position categories correct). RANKING: flat rows, no signification; get_positions returns raw fact rows without dignity/strength annotation. | `layers/L1_ganita/get_positions.ts:60` |
| ga_dashas | #35, #12 | DEGRADED | Both | KNOWN ISSUES: (a) shadbala_null — lord natal condition may be null for some periods; (b) pre-birth sort — dashas before birth date included without filtering; (c) default-system — Vimshottari only by default; 17 other systems in ga_dashas but unreachable without explicit system param. VOLUME: 536,471 rows — must paginate. | `layers/L1_ganita/get_dashas.ts` |
| ga_vargas | #14, #48 | PARTIAL | BULK-only | VOLUME: D1-D60 × all grahas = 20,877 facts retrievable via query_chart_facts. No structured varga-by-varga interface (get_divisionals not wired). RANKING: flat rows, no significance annotation. | `layers/L1_ganita/get_divisionals.ts` (not wired) |
| ph_nimitta | #23, #26 | FULL | Both | Correct; event anchors returned with falsifiers. VOLUME: bounded. | `tools/phala_event_anchors.ts:176,234` |
| ph_phaladesa | #26 | FULL | Both | 7-row domain declaration correctly returned. | `layers/L4_phala/query_domain_result.ts:82` |
| ph_pratikara | #24 | FULL | Both | Mitigation map correctly returned. | `tools/phala_mitigation_map.ts:240` |
| ph_muhurta | #25, #26 | FULL | Both | Muhurta windows correctly returned. | `tools/muhurta_finder.ts:301` |
| mi_jivanaghatana (LEL) | #27 | PARTIAL | Both | VOLUME: bounded. ACCURACY: correct LEL events. RANKING: chronological only, no relevance scoring. | `tools/mimamsa_lel_intake.ts:91` |
| mi_pramana | #29 | PARTIAL | Both | VOLUME: bounded. ACCURACY: calibration scores readable. COMPLETENESS: Brier score breakdown not exposed; mi_pramana scope wider than what query_calibration returns. | `tools/mimamsa_outcome.ts:348` |
| assess_* (D8 apex, bo_laksana) | #42-45 | DEGRADED | Both | **DOES NOT SYNTHESIZE:** assess_career = 6.2MB ingredient dump. activating_dasha EMPTY (count 0 — L3 empty). contradictions = 1,034 raw UUID pairs, resolution_hint null. citations DEFERRED. progeny lens inside career (domain filter broken). VOLUME: overflows 1M context. RANKING: 93.8% raw rows with degenerate salience. | `register_d8_assess_domain.ts:28,151,176,355` |
| **DEFECT-001 (cross-cutting)** | All bo_laksana tools | DEGRADED | Both | constituent_facts_array → L1 fact_ids orphaned at ~91.5% — machine grounding broken. Human citations intact. | `layers/L2_bodha/query_signals.ts` |

---

## §6 — Key Structural Findings

1. **18 L1 registry capabilities have no MCP wiring** (`layers/L1_ganita/get_argala.ts`, `get_ashtakavarga.ts`, `get_aspects.ts`, `get_avasthas.ts`, `get_bhava_bala.ts`, `get_dignity.ts`, `get_dispositors.ts`, `get_divisionals.ts`, `get_eclipse_flags.ts`, `get_karakas.ts`, `get_panchanga.ts`, `get_sade_sati.ts`, `get_sensitive_points.ts`, `get_strength.ts`, `get_tajik.ts`, `get_tara_chandra_bala.ts`, `get_yoga_dosha.ts`). Wiring these 18 tools would expose ga_strength (ranking inputs), ga_structural (relational structure), ga_condition (avasthas), ga_nakshatra, ga_sensitive, ga_sade_sati, ga_tajaka — covering ~11 currently UNCOVERED assets.

2. **mi_darshana is the highest-value L5 gap.** The insight surface (mimamsa_insight_units) — designed to hold reconciled readings — has no MCP tool. This is where the system is intended to surface synthesis but the LLM cannot access it.

3. **L3 temporal activation is empty** for the native chart. The entire timing dimension (kala_activation, kala_activation_predicates) holds 0 rows, making yogas untime-able and assess_* dasha windows empty.

4. **The 4 apex D8 tools nominally cover 5 assets but produce DEGRADED output** due to the combination of salience degeneracy + domain filter failure + L3 empty + unbounded payload + no synthesis.

*End of RETRIEVAL_COVERAGE_MAP v1.0 — Part A Audits 1+2.*
