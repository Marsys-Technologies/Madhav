---
artifact: MCP_TOOL_NAMING_STANDARD
canonical_id: MCP_TOOL_NAMING_STANDARD
version: 1.0
status: PROPOSAL — gated on native sign-off; NOT EXECUTED; existing tool names unchanged
created: 2026-07-02
author: Claude Code (retrieval audit execution)
parent: CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT v2.0 §5
---

> ⚠️ **PROPOSAL ONLY — NOT EXECUTED.** The rename table below is a design artifact. No code has been changed.
> Execution requires: (a) native sign-off, (b) alias/back-compat plan so existing connectors don't break,
> (c) coordinated deploy. Client-breaking rename without aliases destroys all existing MCP integrations.

# MCP Tool Naming Standard v1.0

## §7 Verification Checklist (this document)

| Item | Status | Evidence |
|------|--------|---------|
| §7.8 Naming: all 53 tools have proposed name | ✅ PASS | 53 rows in §3 table below |
| §7.8 Migration marked PROPOSAL/not executed | ✅ PASS | Header + §4 |
| §7.9 Judgment boundary honored | ✅ PASS | Rename logic is structural, no astrological judgment |

---

## §1 — The Convention

**Format:** `<layer>_<topic>_<type>` — snake_case, NO hyphens, ≤128 chars.

### Layer prefixes
| Prefix | Layer | Content |
|--------|-------|---------|
| `ref` | L0 Brahmagyan (global reference) | Entity catalog, ephemeris, classical texts, remedy corpus, reference tables |
| `ganita` | L1 Gaṇita (computed chart facts) | Positions, vargas, strength, dashas, structural relations, nakshatra |
| `bodha` | L2 Bodha (synthesis/meaning) | Signals, domain reading, graph, contradictions, quality, remediation |
| `kala` | L3 Kāla (timing) | Temporal windows, projections, activation, life arc |
| `phala` | L4 Phala (prediction) | Anchors, mitigation, muhurta, outlook |
| `mimamsa` | L5 Mīmāṃsā (calibration/learning) | LEL intake, outcome recording, calibration scores |
| `synth` | Cross-layer synthesis (apex) | Domain assessments that orchestrate all layers |
| `nav` | Session/navigation | Chart selection, session recall |

### Type suffixes
| Suffix | Meaning |
|--------|---------|
| `get` | Retrieve a specific or bounded set of structured data |
| `list` | Enumerate items (catalogs, charts, sessions) |
| `search` | Query/filter by criteria (semantic or structured) |
| `compute` | Trigger computation (PyJHora, ephemeris) |
| `select` | Choose from available options (chart selection) |
| `assess` | Synthesize a domain assessment (verdict + evidence) |
| `record` | Write/persist an event or outcome |
| `traverse` | Walk a graph structure |
| `bundle` | Retrieve a pre-assembled multi-asset composite |

### Topic segment
Short snake_case noun describing the astrological content. Examples: `positions`, `dashas`, `signals`,
`remedies`, `anchors`, `outlook`, `calibration`, `graph`, `facts`, `citation`, `entity`, `yogas`.

---

## §2 — Rationale

The current names are a historical hodgepodge: some tool-shaped (`assess_career`), some table-shaped (`query_chart_facts`), some method-shaped (`get_dashas`), some completely ambiguous (`get_remedies` vs `query_remedies` vs `query_remedies_for_chart`). An LLM choosing between 53 tools must parse intent from inconsistent vocabulary.

The `<layer>_<topic>_<type>` convention makes the tool name **self-describing** at selection time:
- The LLM reads `ganita` → "this is about computed chart facts (L1)".
- The LLM reads `_assess` → "this synthesizes; it won't return raw rows".
- The LLM reads `bodha_` → "this is interpretation-layer data (L2 Bodha)".
- Grouping by layer prefix makes tool families visible in sorted lists.

The convention removes the `get_` vs `query_` ambiguity entirely (both → `_get` or `_search` by whether filtering is by criteria vs direct key lookup).

---

## §3 — The 53-Tool Rename Table

| # | Current Name | Proposed Name | Layer | Topic | Type | Source File:Line | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `resolve_entity` | `ref_entity_resolve` | ref | entity | resolve* | `tools/l0_brahmagyan.ts:49` | *resolve = find canonical form; not a standard type — prefer `ref_entity_get` [NATIVE-RATIFY: type suffix] |
| 2 | `list_entities` | `ref_entities_list` | ref | entities | list | `tools/l0_brahmagyan.ts:99` | Note plural topic for list-type tools |
| 3 | `asset_registry_all` | `ref_assets_list` | ref | assets | list | `tools/l0_brahmagyan.ts:141` | Returns all 85 assets from asset_registry |
| 4 | `asset_registry_l0` | `ref_assets_l0_list` | ref | assets_l0 | list | `tools/l0_brahmagyan.ts:169` | L0-scoped asset registry |
| 5 | `intent_classify` | `ref_intent_classify` | ref | intent | classify* | `tools/l0_brahmagyan.ts:222` | *classify = new type suffix; or `ref_intent_get` [NATIVE-RATIFY] |
| 6 | `query_planet_position` | `ref_position_get` | ref | position | get | `tools/l0_ephemeris.ts:59` | Queries ephemeris_daily table |
| 7 | `query_planet_transit` | `ref_transit_get` | ref | transit | get | `tools/l0_ephemeris.ts:97` | Planet transit from ephemeris_daily |
| 8 | `query_aspects_at_time` | `ref_aspects_get` | ref | aspects | get | `tools/l0_ephemeris.ts:137` | Planetary aspects from ephemeris |
| 9 | `query_retrograde_periods` | `ref_retrograde_get` | ref | retrograde | get | `tools/l0_ephemeris.ts:177` | Retrograde windows from ephemeris_daily |
| 10 | `ephemeris_cache_year` | `ref_ephemeris_year_get` | ref | ephemeris_year | get | `tools/l0_ephemeris.ts:215` | Year-slice ephemeris cache |
| 11 | `compute_natal_positions` | `ganita_positions_compute` | ganita | positions | compute | `tools/retrieval/pyhora_natal.ts:69` | PyJHora natal computation (live compute) |
| 12 | `query_dasha_periods` | `ganita_dashas_compute` | ganita | dashas | compute | `tools/retrieval/pyhora_natal.ts:122` | PyJHora Vimshottari dasha computation |
| 13 | `query_special_lagnas` | `ganita_lagnas_compute` | ganita | lagnas | compute | `tools/retrieval/pyhora_natal.ts:178` | PyJHora upagrahas + special lagnas |
| 14 | `holistic_bundle_chart_facts` | `ganita_facts_bundle` | ganita | facts_bundle | bundle | `tools/retrieval/holistic_bundle.ts:51` | chart_facts bundle via registry; feeds L2 bodha |
| 15 | `kala_temporal_bundle` | `kala_bundle_get` | kala | bundle | get | `tools/retrieval/kala_temporal.ts:408` | L3 composite bundle (sidecar) |
| 16 | `query_remedies` | `ref_remedies_search` | ref | remedies | search | `tools/retrieval/remedy_tools.ts:28` | Global remedy catalog (bg_remedies) |
| 17 | `query_remedies_for_chart` | `bodha_remedies_search` | bodha | remedies | search | `tools/retrieval/remedy_tools.ts:55` | Chart-scoped remedy resonances (bo_upaya) |
| 18 | `list_remedies_by_category` | `ref_remedies_list` | ref | remedies | list | `tools/retrieval/remedy_tools.ts:80` | Enumerate remedy corpus by category |
| 19 | `read_remedy` | `ref_remedy_get` | ref | remedy | get | `tools/retrieval/remedy_tools.ts:107` | Fetch a single remedy by ID |
| 20 | `query_tantric_remedies` | `ref_tantric_remedies_search` | ref | tantric_remedies | search | `tools/retrieval/remedy_tools.ts:131` | Tantric/advanced remedy subset |
| 21 | `query_remedies_by_planet` | `ref_planet_remedies_get` | ref | planet_remedies | get | `tools/retrieval/remedy_tools.ts:156` | Remedies keyed to a specific graha |
| 22 | `query_mantras` | `ref_mantras_search` | ref | mantras | search | `tools/retrieval/remedy_tools.ts:181` | Mantra corpus query |
| 23 | `event_anchors` | `phala_anchors_get` | phala | anchors | get | `tools/phala_event_anchors.ts:234` | Calibrated probabilistic event anchors |
| 24 | `mitigation_map` | `phala_mitigation_get` | phala | mitigation | get | `tools/phala_mitigation_map.ts:240` | Mitigation map for afflictions |
| 25 | `muhurta_finder` | `phala_muhurta_select` | phala | muhurta | select | `tools/muhurta_finder.ts:301` | Auspicious window selection |
| 26 | `phala_outlook` | `phala_outlook_get` | phala | outlook | get | `tools/phala_outlook.ts:206` | Composite L4 predictive bundle |
| 27 | `lel_query` | `mimamsa_lel_search` | mimamsa | lel | search | `tools/mimamsa_lel_intake.ts:91` | Life Event Log query |
| 28 | `record_outcome` | `mimamsa_outcome_record` | mimamsa | outcome | record | `tools/mimamsa_outcome.ts:229` | Record a prediction outcome |
| 29 | `query_calibration` | `mimamsa_calibration_get` | mimamsa | calibration | get | `tools/mimamsa_outcome.ts:348` | Retrieve calibration scores |
| 30 | `get_chart_orientation` | `bodha_orientation_get` | bodha | orientation | get | `tools/registry_bridge.ts:252` | → marsys://tool/L2/query_ucd (UCD/bo_samvada) |
| 31 | `get_domain_reading` | `bodha_domain_reading_get` | bodha | domain_reading | get | `tools/registry_bridge.ts:306` | → marsys://tool/L2/query_domain_reading |
| 32 | `get_signals` | `bodha_signals_get` | bodha | signals | get | `tools/registry_bridge.ts:401` | → marsys://tool/L2/query_signals (bo_laksana) |
| 33 | `traverse_graph` | `bodha_graph_traverse` | bodha | graph | traverse | `tools/registry_bridge.ts:436` | → marsys://tool/L2/traverse_chart_graph (bo_bimba) |
| 34 | `get_positions` | `ganita_positions_get` | ganita | positions | get | `tools/registry_bridge.ts:467` | → marsys://tool/L1/get_positions (ga_positions+ga_vargas) |
| 35 | `get_dashas` | `ganita_dashas_get` | ganita | dashas | get | `tools/registry_bridge.ts:491` | → marsys://tool/L1/get_dashas (ga_dashas) |
| 36 | `get_temporal_windows` | `kala_windows_get` | kala | windows | get | `tools/registry_bridge.ts:530` | → marsys://tool/L3/query_temporal_activation |
| 37 | `get_projections` | `kala_projections_get` | kala | projections | get | `tools/registry_bridge.ts:559` | → marsys://tool/L3/query_projections |
| 38 | `get_classical_citation` | `ref_citation_get` | ref | citation | get | `tools/registry_bridge.ts:602` | → marsys://tool/L0/query_classical_texts (bg_texts) |
| 39 | `get_remedies` | `bodha_remedies_get` | bodha | remedies | get | `tools/registry_bridge.ts:625` | → marsys://tool/L2/query_remedies (bo_upaya); distinguishable from ref_remedies_search (#16) by layer prefix |
| 40 | `get_chart_quality` | `bodha_quality_get` | bodha | quality | get | `tools/registry_bridge.ts:651` | → marsys://tool/L2/query_quality_scorecard (bo_pramana_mapa) |
| 41 | `list_assets` | `ref_asset_registry_list` | ref | asset_registry | list | `tools/registry_bridge.ts:676` | → marsys://resource/asset-registry/all; distinguishes from asset_registry_all (#3) as bridge vs direct |
| 42 | `assess_marriage` | `synth_marriage_assess` | synth | marriage | assess | `tools/registry_bridge.ts:703` | D8 apex — orchestrates L2+L3+contradictions |
| 43 | `assess_career` | `synth_career_assess` | synth | career | assess | `tools/registry_bridge.ts:727` | D8 apex — career domain synthesis |
| 44 | `assess_health` | `synth_health_assess` | synth | health | assess | `tools/registry_bridge.ts:751` | D8 apex — health domain synthesis |
| 45 | `assess_wealth` | `synth_wealth_assess` | synth | wealth | assess | `tools/registry_bridge.ts:775` | D8 apex — wealth domain synthesis |
| 46 | `yoga_activation_by_dasha` | `kala_yoga_activation_get` | kala | yoga_activation | get | `tools/registry_bridge.ts:799` | Yoga ripening by dasha window |
| 47 | `get_cgm_subgraph` | `bodha_graph_get` | bodha | graph | get | `tools/registry_bridge.ts:839` | CGM subgraph (bo_bimba/bo_karanajala) |
| 48 | `query_chart_facts` | `ganita_facts_search` | ganita | facts | search | `tools/registry_bridge.ts:883` | chart_facts table search |
| 49 | `vector_search` | `bodha_vector_search` | bodha | vector | search | `tools/registry_bridge.ts:934` | Semantic search over bo_samskara embeddings |
| 50 | `list_my_charts` | `nav_charts_list` | nav | charts | list | `tools/chart_selection.ts:107` | Entitled chart list for current user |
| 51 | `select_chart` | `nav_chart_select` | nav | chart | select | `tools/chart_selection.ts:169` | Validate + return chart_id |
| 52 | `recall_session` | `nav_session_get` | nav | session | get | `tools/session_tools.ts:42` | Resume prior session with entitlement re-check |
| 53 | `list_my_sessions` | `nav_sessions_list` | nav | sessions | list | `tools/session_tools.ts:125` | Session history for current user |

**Count verification: 53 rows ✓**

### Naming conflicts resolved
- `get_dashas` (#35) ↔ `query_dasha_periods` (#12): distinguished as `ganita_dashas_get` (DB retrieval) vs `ganita_dashas_compute` (PyJHora live compute).
- `get_positions` (#34) ↔ `compute_natal_positions` (#11): distinguished as `ganita_positions_get` (DB) vs `ganita_positions_compute` (PyJHora).
- `get_remedies` (#39) ↔ `query_remedies` (#16) ↔ `query_remedies_for_chart` (#17): distinguished by layer (`bodha_` = chart-scoped bo_upaya, `ref_` = global corpus).
- `asset_registry_all` (#3) ↔ `list_assets` (#41): both expose same underlying data but via different paths; proposed names distinguish (`ref_assets_list` direct vs `ref_asset_registry_list` bridge).

---

## §4 — Migration Plan (PROPOSAL; NOT EXECUTED)

### Phase 1 — Alias layer (non-breaking)
Add alias registrations so both old and new names are live simultaneously. In `registry_bridge.ts` and each tool file, register the tool under **both** the old name and the new name. MCP clients still calling `assess_career` continue to work; new clients can use `synth_career_assess`.

```typescript
// Example alias pattern — NOT YET IMPLEMENTED
server.tool('synth_career_assess', DESCRIPTION, SCHEMA, HANDLER)  // new
server.tool('assess_career', DESCRIPTION, SCHEMA, HANDLER)         // old alias → same handler
```

### Phase 2 — Deprecation notices (6-month window)
After alias layer is live, add deprecation notices to old-name tool descriptions: "DEPRECATED: use synth_career_assess. This alias will be removed in v2."

### Phase 3 — Remove aliases (breaking; gate on native sign-off)
After 6 months (or when native confirms all connectors updated), remove the old-name registrations. Update REGISTERED_TOOL_COUNT comment in `server.ts`. Update health endpoint tool list.

### Gate checklist (before executing ANY rename)
- [ ] Native sign-off on this proposal
- [ ] All known MCP connectors identified (Cowork connector, test clients)
- [ ] Alias layer deployed and verified (both names respond identically)
- [ ] MCP_E2E_TEST_REPORT confirms all 53 tools pass under new names
- [ ] Deprecation window communicated

---

## §5 — Open questions [NATIVE-RATIFY]

1. **`resolve` and `classify` as type suffixes**: the convention uses the standard set (get/list/search/compute/select/assess/record/traverse/bundle). Should `resolve` and `classify` be added to the standard set, or should `resolve_entity` → `ref_entity_get` and `intent_classify` → `ref_intent_get`?
2. **`ref_assets_list` vs `ref_asset_registry_list` (#3 vs #41)**: these expose overlapping data. Should one be retired rather than renamed?
3. **`synth` layer for D8 apex tools**: this document proposes `synth` as a cross-layer layer prefix. Alternative is `phala` (prediction) since assess_* are in the L4 sphere. [NATIVE-RATIFY]
4. **Bundle suffix for #14 `ganita_facts_bundle`**: this is the chart_facts holistic bundle feeding L2 Bodha. Is the destination layer (`ganita`) correct, or should it be `bodha_facts_bundle` since it's a Bodha-domain entry point?

*End of MCP_TOOL_NAMING_STANDARD v1.0 — PROPOSAL, not executed.*
