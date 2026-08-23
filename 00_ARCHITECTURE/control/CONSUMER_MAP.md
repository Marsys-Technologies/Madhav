# NIRMĀṆA M0-T6 — Asset → Serving-Surface Consumer Map

**Generated:** 2026-08-23T04:44:19.587467Z  
**Generator:** `00_ARCHITECTURE/control/consumer_map.py` (machine-readable output: `00_ARCHITECTURE/control/CONSUMER_MAP.json`)  
**Task:** M0-T6 (Nirmāṇa Phase 0.7 consumer map + 0.8c evidence)  
**Database access:** READ-ONLY (SELECT only, autocommit, statement_timeout 45s)  
**Status:** observations only. This document issues no verdict, proposes no disposition and certifies nothing (I16 / charter H7). Promote / retire / reclassify is ADHIKĀRIN's G1 power.

---

## 0 — What was scanned

| quantity | value |
|---|--:|
| registered assets | 128 |
| source files scanned (non-test) | 3585 |
| distinct tables/views indexed | 179 |
| API routes detected (`app/**/route.ts`) | 174 |
| UI pages detected (`app/**/page.tsx`) | 52 |
| MCP tool names detected (`server.tool(`/`registerTool(`) | 144 |
| MCP resource names detected (`server.resource(`) | 14 |
| FastAPI sidecar endpoints detected | 25 |
| retrieval capability URIs detected (`marsys://…`) | 186 |
| python writers detected (`@register(...)`) | 123 |
| resolved import edges | 7563 |
| import-walk depth cap | 3 |
| hub modules excluded from traversal (fan-in ≥ 30) | 19 |

## 1 — Method

The map is built from code, not from what the registry claims about itself. In outline:

1. Each asset contributes its `target_table` (**primary**) plus any table names parsed out of its `count_sql` and `clear_tables` (**derived**). Every view, materialized view and SQL function whose definition names one of those tables is resolved from `pg_views` / `pg_matviews` / `pg_proc`, and the view name is scanned too (**via_db_view**).
2. Every non-test file in the four corpora (`platform-mcp/src`, `platform/src`, `platform/scripts`, the python sidecar) is scanned for whole-word occurrences of those names. Each hit is graded `sql_read` (immediately preceded by `FROM`/`JOIN`/`USING`), `sql_write` (`INTO`/`UPDATE`/`DELETE FROM`/`TRUNCATE`/`TABLE`) or `weak` (anything else — a comment, a description string, an identifier). **`weak` hits are never treated as evidence of a consumer.**
3. A statement is attributed to a consumer by one of four relations, never by an unbounded transitive import walk:

   | tier | relation |
   |---|---|
   | `direct` | the statement is inside the surface file itself (a `route.ts`, a `page.tsx`, a file calling `server.tool()`, a FastAPI router) |
   | `capability` | the statement is inside a retrieval `CapabilityDescriptor` module. The capability's own `marsys://` URI **is** the served surface — `POST /api/retrieval/capability` dispatches it — and the MCP tool bound to that URI is named from platform-mcp's generated surface profile (an exact binding, not an import walk) |
   | `traced` | the statement is in a library module forward-reachable from a route/page/router within 3 import hops, not crossing a hub module |
   | `writer` | the statement is in a python module reachable from a `@register()`-ed writer — this is an **input** consumer, reported separately from serving consumers and never merged with them |

4. Anything else the scan found is kept, per asset, in a non-serving bucket (`own_writer` / `registry_declaration` / `ops_script` / `prompt_text`) or as an `unattributed_read`, rather than being dropped.
5. For an asset whose interface is code rather than rows (`asset_kind = service`, or a registry row with `provides_apis` and no `target_table`), a second, separate detector runs: who imports the module(s) that own the asset, and whether the symbols named in `provides_apis` appear anywhere in the corpus.

## 2 — What this method cannot show

This is the part M0-T1 flagged as still open. It is not closed by this document; it is *scoped*.

- STATIC ONLY. A textual reference is not proof a caller can reach the surface at runtime; nothing here executes code, exercises a route, or reads server logs.
- Table names are matched as whole-word tokens. Each hit is graded `sql_read` (immediately preceded by FROM/JOIN/USING), `sql_write` (INTO/UPDATE/DELETE FROM/TRUNCATE/TABLE) or `weak` (everything else). ONLY sql_read and sql_write hits are counted as statements; `weak` hits are counted in reference_sites but are never treated as evidence of a consumer.
- A sql-graded hit is still only a textual statement: it does not distinguish a live code path from dead code, a commented-out query, or a stub that never runs.
- INVISIBLE TO THIS METHOD: dynamic SQL, table names built by concatenation or template interpolation, ORM/query-builder indirection, a table read only from inside a PL/pgSQL function body invoked by a surface, and any surface registered by a pattern not matched by the surface regexes below. (Views and matviews ARE followed — see the DB-side indirection note.)
- Surface detection is regex-based: app/**/route.ts (API), app/**/page.tsx (UI), `server.tool(`/`registerTool(` (MCP), FastAPI decorators (sidecar), and `uri: 'marsys://...'` (retrieval capability).
- MCP tool attribution for capability modules uses the EXACT uri binding from platform-mcp's generated surface profile and mcp_capability_bridge.ts — not an import walk. A capability with no bound tool name is still a served surface via POST /api/retrieval/capability; it is reported with an empty mcp_tools list.
- `traced` attribution walks imports forward from a surface at most 3 hops and never continues through a hub module (fan-in >= 30). A real consumer further away, or only reachable through a hub, is therefore NOT reported — this trades recall for precision deliberately.
- app/api/retrieval/capability/route.ts is excluded from `traced` attribution into the retrieval subtree, because it is a generic dispatcher that can reach every capability; attributing every capability read to that one route would be true but useless. Those reads appear under their own `capability:` key instead.
- ATTRIBUTION SCOPE. Several platform-mcp files register many tools in one module. A read INSIDE such a file is scoped to the nearest preceding server.tool() registration (attribution_scope='exact_nearest_registration') — a good heuristic, not a parse of the closure. A read in a module IMPORTED by such a file cannot be scoped at all and is attributed to every tool the file registers (attribution_scope='file_scope_multi_tool_registrar'); those entries over-report WHICH tool reads the asset while still correctly answering WHETHER something does.
- Test, eval, mock and fixture paths are excluded from evidence. A surface that exists only under test is invisible here by design.
- DB-side indirection IS followed one step: every view, materialized view and SQL function whose definition names an asset table is resolved from pg_views / pg_matviews / pg_proc, and the view name is scanned as an additional table for that asset (table_role = via_db_view). Function bodies are reported but not scanned as surfaces. Nested views are resolved to two levels only.
- The asset -> table mapping is only as good as the registry: 14 assets declare no target_table, and for those the scan can only use tables parsed out of count_sql. An asset with no table at all is reported UNKNOWN, not zero-consumer.
- A THIRD, weaker detector records where the asset_id itself is named inside a surface file or a CapabilityDescriptor module (asset_id_mentions). A name-mention is a pointer, not a read — it is reported separately and never counted as a serving consumer — but it is the only signal that finds a serving path re-implemented in TypeScript against a different table than the asset writes (ka_tulana is the live example).
- For an asset whose interface is CODE rather than rows (asset_kind=service, or a registry row with provides_apis and no target_table), a second detector is used: who imports the module(s) that own the asset, and whether the symbols named in provides_apis appear anywhere in the corpus. This detector answers a different question from the table scan and its result is reported separately, never merged.
- Co-written tables (5 of them, census §5) mean a consumer of the TABLE is not necessarily a consumer of THIS asset's rows. Attribution is table-level, not partition-level.

## 3 — Headline counts

| evidence class | assets |
|---|--:|
| serving consumer detected | 105 |
| writer consumers only | 13 |
| no consumer — statements only in its own writer / seed / ops scripts | 3 |
| UNKNOWN — asset declares no table and no reachable code interface | 3 |
| writer consumers only (code-module interface) | 3 |
| UNKNOWN — reads exist that this method could not attribute | 1 |
| **total** | **128** |

- **≥1 serving consumer detected: 105**
- **only writer (input) consumers: 16**
- **no consumer of any kind detected: 3** — `bg_concordance`, `bg_vidhi_floors`, `bg_vidhi_primitives`
- **UNKNOWN-only evidence: 4** — `bg_ephemeris_engine`, `bg_panchanga`, `bg_sky_calendar`, `ka_tulana`

The zero-serving set is therefore **23 assets**, not the 13 the plan states (§1 / v3.0 §0.8c). See `ZERO_CONSUMER_EVIDENCE_v1_0.md` for the per-asset packets and for the reconciliation of the two figures.

## 4 — Full map

`serve` = distinct serving surfaces detected · `wr` = distinct writer (input) consumers · `rd`/`wt` = SQL-context read/write statements found · `?` = unattributed reads present.

| asset_id | layer | status | kind | target_table | serve | wr | rd | wt | ? | evidence class | detected serving consumers (first 6) |
|---|---|---|---|---|--:|--:|--:|--:|:--:|---|---|
| `bg_class_lifetime_counts` | brahmagyan | CURRENT | data | `brahma_class_priors` | 1 | 13 | 11 | 3 | · | serving consumer detected | `capability:marsys://tool/L0/query_class_priors` |
| `bg_class_priors` | brahmagyan | CURRENT | data | `brahma_class_priors` | 1 | 12 | 11 | 3 | Y | serving consumer detected | `capability:marsys://tool/L0/query_class_priors` |
| `bg_cohort` | brahmagyan | CURRENT | data | `bg_synthetic_cohort` | 0 | 1 | 8 | 1 | · | writer consumers only | — |
| `bg_compendium_index` | brahmagyan | CURRENT | data | `brahma_compendium_index` | 1 | 0 | 5 | 2 | · | serving consumer detected | `capability:marsys://tool/L0/query_compendium_index` |
| `bg_concordance` | brahmagyan | CURRENT | data | `classical_attributions` | 0 | 0 | 5 | 3 | · | no consumer — statements only in its own writer / seed / ops scripts | — |
| `bg_dasha_systems` | brahmagyan | CURRENT | data | `brahma_dasha_systems` | 1 | 1 | 3 | 0 | · | serving consumer detected | `capability:marsys://tool/L0/query_dasha_systems → ref_dasha_systems_get` |
| `bg_dignity_reference` | brahmagyan | CURRENT | data | `bg_dignity_reference` | 31 | 4 | 22 | 4 | · | serving consumer detected | `capability:marsys://tool/L0/query_avastha_schemes`<br>`capability:marsys://tool/L0/query_combustion_orbs`<br>`capability:marsys://tool/L0/query_graha_naisargika_friendship`<br>`capability:marsys://tool/L0/query_motion_state_thresholds`<br>`mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>…+25 |
| `bg_doshas` | brahmagyan | CURRENT | data | `brahma_dosha_catalog` | 2 | 3 | 5 | 2 | Y | serving consumer detected | `capability:marsys://tool/L0/query_dosha_catalog → query_dosha_catalog,ref_doshas_get`<br>`capability:marsys://tool/L0/query_parihara_graph` |
| `bg_ephemeris` | brahmagyan | CURRENT | data | `ephemeris_daily` | 37 | 7 | 37 | 4 | Y | serving consumer detected | `capability:marsys://tool/L0/query_aspects_at_time → query_aspects_at_time`<br>`capability:marsys://tool/L0/query_planet_transit → query_planet_transit`<br>`capability:marsys://tool/L1/get_graha_yuddha → get_graha_yuddha`<br>`mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>…+31 |
| `bg_ephemeris_engine` | brahmagyan | CURRENT | data | — | 0 | 0 | 0 | 0 | · | UNKNOWN — asset declares no table and no reachable code interface | — |
| `bg_formula_constants` | brahmagyan | CURRENT | data | `brahma_formula_constants` | 2 | 5 | 19 | 2 | Y | serving consumer detected | `api_route:/api/mcp/writes/[action]`<br>`capability:marsys://tool/L0/query_formula_constants` |
| `bg_ghatana` | brahmagyan | CURRENT | data | `brahma_event_ontology` | 36 | 14 | 60 | 3 | Y | serving consumer detected | `api_route:/api/mcp/writes/[action]`<br>`capability:marsys://tool/L4/query_prospective_ledger`<br>`capability:marsys://tool/L5/lel_intake_checklist`<br>`capability:marsys://tool/L5/prediction_lifecycle_sweep`<br>`mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>…+30 |
| `bg_gochara_arcs` | brahmagyan | CURRENT | data | `bg_gochara_arcs` | 0 | 1 | 2 | 0 | · | writer consumers only | — |
| `bg_gochara_citation_resolution` | brahmagyan | CURRENT | data | `bg_gochara_citation_resolution` | 29 | 0 | 2 | 0 | · | serving consumer detected | `mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>`mcp_tool:chart_snapshot`<br>`mcp_tool:get_cgm_subgraph`<br>…+23 |
| `bg_kota_chakra_rings` | brahmagyan | CURRENT | data | `bg_kota_chakra_rings` | 0 | 1 | 5 | 2 | Y | writer consumers only | — |
| `bg_kp_sublord_division` | brahmagyan | CURRENT | data | `bg_kp_sublord_division` | 0 | 2 | 3 | 1 | · | writer consumers only | — |
| `bg_medical_mappings` | brahmagyan | CURRENT | data | `bg_medical_mappings` | 1 | 1 | 5 | 0 | · | serving consumer detected | `capability:marsys://tool/L0/query_medical_mappings` |
| `bg_muhurta_lattice` | brahmagyan | CURRENT | data | `bg_muhurta_lattice` | 1 | 0 | 3 | 0 | · | serving consumer detected | `capability:marsys://tool/L0/query_muhurta_lattice` |
| `bg_nakshatra` | brahmagyan | CURRENT | data | `reference_nakshatra` | 1 | 6 | 15 | 3 | Y | serving consumer detected | `mcp_tool:ref_nakshatra_get` |
| `bg_nakshatra_medical` | brahmagyan | CURRENT | data | `bg_nakshatra_medical` | 1 | 1 | 6 | 0 | · | serving consumer detected | `capability:marsys://tool/L0/query_nakshatra_medical` |
| `bg_ontology` | brahmagyan | CURRENT | data | `brahma_ontology` | 2 | 4 | 14 | 4 | Y | serving consumer detected | `capability:marsys://tool/L0/list_entities → list_entities`<br>`capability:marsys://tool/L0/resolve_entity → resolve_entity` |
| `bg_panchanga` | brahmagyan | CURRENT | data | — | 0 | 0 | 0 | 0 | · | UNKNOWN — asset declares no table and no reachable code interface | — |
| `bg_parihara_rules` | brahmagyan | CURRENT | data | `bg_parihara_rules` | 1 | 0 | 6 | 2 | · | serving consumer detected | `capability:marsys://tool/L0/query_parihara_graph` |
| `bg_phaladeepika_latta` | brahmagyan | CURRENT | data | `bg_phaladeepika_latta` | 0 | 2 | 2 | 1 | · | writer consumers only | — |
| `bg_prashna_rules` | brahmagyan | CURRENT | data | — | 7 | 1 | 12 | 5 | Y | serving consumer detected | `capability:marsys://tool/L0/query_prashna_fructification_rules`<br>`capability:marsys://tool/L0/query_prashna_lagna_methods`<br>`capability:marsys://tool/L0/query_prashna_significators`<br>`capability:marsys://tool/L0/query_prashna_special_techniques`<br>`capability:marsys://tool/L0/query_prashna_tajik_yogas`<br>`sidecar_endpoint:GET /health`<br>…+1 |
| `bg_reference` | brahmagyan | CURRENT | data | `reference_nakshatras` | 0 | 14 | 38 | 15 | Y | writer consumers only | — |
| `bg_remedies` | brahmagyan | CURRENT | data | `brahma_remedy_corpus` | 51 | 1 | 29 | 4 | Y | serving consumer detected | `api_route:/api/cockpit/plan`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L0/find_verses_about → find_verses_about`<br>`capability:marsys://tool/L0/list_classical_texts → list_classical_texts`<br>`capability:marsys://tool/L0/list_remedies_by_category → ref_remedies_by_category_list`<br>`capability:marsys://tool/L0/list_sutravali_rules_by_text`<br>…+45 |
| `bg_rules` | brahmagyan | CURRENT | data | `sutravali_rules` | 9 | 3 | 7 | 4 | Y | serving consumer detected | `mcp_resource:sutravali-by-house`<br>`mcp_resource:sutravali-by-planet`<br>`sidecar_endpoint:GET /health`<br>`sidecar_endpoint:GET /sutravali/by_house/{house_num}`<br>`sidecar_endpoint:GET /sutravali/by_planet/{planet}`<br>`sidecar_endpoint:GET /sutravali/list_rules_by_text/{text_id}`<br>…+3 |
| `bg_sarvatobhadra_grid` | brahmagyan | CURRENT | data | `bg_sarvatobhadra_grid` | 0 | 1 | 2 | 0 | · | writer consumers only | — |
| `bg_sign_medical` | brahmagyan | CURRENT | data | `bg_sign_medical` | 1 | 2 | 2 | 1 | · | serving consumer detected | `capability:marsys://tool/L0/query_sign_medical → ref_sign_medical_get` |
| `bg_sky_calendar` | brahmagyan | CURRENT | data | `bg_sky_events` | 0 | 0 | 3 | 1 | Y | UNKNOWN — reads exist that this method could not attribute | — |
| `bg_text_index` | brahmagyan | CURRENT | data | `classical_text_chunks` | 2 | 8 | 71 | 16 | Y | serving consumer detected | `capability:marsys://tool/L0/query_classical_texts → get_classical_citation,query_classical_texts`<br>`capability:marsys://tool/L0/query_compendium_index` |
| `bg_texts` | brahmagyan | CURRENT | data | `classical_text_chunks` | 3 | 9 | 84 | 25 | Y | serving consumer detected | `api_route:/api/classical-texts/[text_key]/summary`<br>`capability:marsys://tool/L0/query_classical_texts → get_classical_citation,query_classical_texts`<br>`capability:marsys://tool/L0/query_compendium_index` |
| `bg_transit_engine` | brahmagyan | CURRENT | data | `bg_transit_engine` | 1 | 1 | 2 | 1 | · | serving consumer detected | `capability:marsys://tool/L0/query_transit_engine` |
| `bg_transit_rules` | brahmagyan | CURRENT | data | `bg_transit_rules` | 7 | 7 | 19 | 0 | Y | serving consumer detected | `capability:marsys://tool/L3/query_vedha_gochara`<br>`mcp_tool:ref_transit_rules_get`<br>`sidecar_endpoint:GET /health`<br>`sidecar_endpoint:POST /activation`<br>`sidecar_endpoint:POST /curve`<br>`sidecar_endpoint:POST /permission_curve`<br>…+1 |
| `bg_vastu_directions` | brahmagyan | CURRENT | data | `bg_vastu_directions` | 2 | 0 | 4 | 2 | Y | serving consumer detected | `capability:marsys://tool/L0/query_vastu_direction_remedials`<br>`capability:marsys://tool/L0/query_vastu_directions` |
| `bg_vedha_malefic_scale` | brahmagyan | CURRENT | data | `bg_vedha_malefic_scale` | 0 | 3 | 5 | 1 | · | writer consumers only | — |
| `bg_vidhi_floors` | brahmagyan | DRAFT | data | `vidhi_floor_items` | 0 | 0 | 2 | 1 | · | no consumer — statements only in its own writer / seed / ops scripts | — |
| `bg_vidhi_primitives` | brahmagyan | DRAFT | data | `vidhi_primitives` | 0 | 0 | 1 | 1 | · | no consumer — statements only in its own writer / seed / ops scripts | — |
| `bg_yogas` | brahmagyan | CURRENT | data | `brahma_yoga_catalog` | 3 | 11 | 27 | 6 | Y | serving consumer detected | `capability:marsys://tool/L0/list_entities → list_entities`<br>`capability:marsys://tool/L0/query_yoga_catalog → query_yoga_catalog,ref_yogas_get`<br>`capability:marsys://tool/L0/resolve_entity → resolve_entity` |
| `bo_anveshana` | bodha | CURRENT | data | `bodha_discoveries` | 9 | 2 | 20 | 2 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L2/query_contradictions → query_contradictions`<br>`capability:marsys://tool/L2/query_discoveries → bodha_discoveries_get`<br>`mcp_tool:mcp_server_info`<br>…+3 |
| `bo_arudha` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_bimba` | bodha | CURRENT | data | `bodha_cgm_nodes` | 76 | 19 | 31 | 6 | · | serving consumer detected | `capability:marsys://tool/L2/traverse_chart_graph → bodha_graph_subgraph_get,traverse_graph`<br>`mcp_tool:bodha_chart_digest_get`<br>`mcp_tool:bodha_discoveries_get`<br>`mcp_tool:bodha_graph_subgraph_get`<br>`mcp_tool:bodha_graph_traverse_get`<br>`mcp_tool:bodha_mechanisms_get`<br>…+70 |
| `bo_cdlm_summary` | bodha | DRAFT | data | — | 0 | 13 | 4 | 2 | · | writer consumers only | — |
| `bo_cgm_motifs` | bodha | CURRENT | data | `bodha_cgm_motifs` | 1 | 14 | 9 | 1 | · | serving consumer detected | `capability:marsys://tool/L2/query_cgm_motifs` |
| `bo_cgm_paths` | bodha | CURRENT | data | `bodha_cgm_paths` | 1 | 15 | 11 | 1 | · | serving consumer detected | `capability:marsys://tool/L2/query_cgm_paths` |
| `bo_chart_gestalt` | bodha | DRAFT | data | — | 1 | 0 | 7 | 2 | · | serving consumer detected | `capability:marsys://tool/L2/query_chart_gestalt` |
| `bo_drishti` | bodha | CURRENT | data | `bodha_question_lenses` | 2 | 0 | 8 | 1 | · | serving consumer detected | `capability:marsys://tool/L2/query_domain_reading → get_domain_reading,query_domain_reading`<br>`capability:marsys://tool/L2/query_question_lenses` |
| `bo_karanajala` | bodha | CURRENT | data | `bodha_cgm_edges` | 7 | 18 | 26 | 1 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L2/traverse_chart_graph → bodha_graph_subgraph_get,traverse_graph`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>…+1 |
| `bo_laksana` | bodha | CURRENT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_laksana_rerank` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_nakshatra_semantic` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_pramana_mapa` | bodha | CURRENT | data | `synthesis_quality_scorecard` | 6 | 13 | 9 | 1 | · | serving consumer detected | `api_route:/api/admin/trace/[query_id]`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L2/query_quality_scorecard → bodha_quality_get,get_chart_quality`<br>`capability:marsys://tool/L2/query_ucd → bodha_chart_digest_get,get_chart_orientation`<br>`ui_page:/admin/trace/[query_id]` |
| `bo_pratijna` | bodha | CURRENT | data | `bodha_pratijna` | 5 | 6 | 20 | 2 | · | serving consumer detected | `capability:marsys://tool/L2/query_pratijna → bodha_pratijna_get`<br>`mcp_tool:bodha_pratijna_get`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>`mcp_tool:prashna_status` |
| `bo_samskara` | bodha | CURRENT | data | `bodha_signal_embeddings` | 0 | 14 | 9 | 4 | Y | writer consumers only | — |
| `bo_samvada` | bodha | CURRENT | data | `vw_chart_digest` | 3 | 0 | 4 | 0 | · | serving consumer detected | `api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L2/query_ucd → bodha_chart_digest_get,get_chart_orientation` |
| `bo_sangati` | bodha | CURRENT | data | `bodha_cdlm_cells` | 5 | 16 | 20 | 2 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L2/query_domain_reading → get_domain_reading,query_domain_reading`<br>`capability:marsys://tool/L2/query_remedies → bodha_remedies_get,get_remedies` |
| `bo_special_lagna` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_sudarshana` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_upaya` | bodha | CURRENT | data | `bodha_rm_resonances` | 11 | 14 | 26 | 5 | · | serving consumer detected | `api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L2/query_remedies → bodha_remedies_get,get_remedies`<br>…+5 |
| `bo_vargottama_dhana` | bodha | DRAFT | data | `bodha_msr_signals` | 27 | 26 | 90 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L-DOMAIN/assess_career → assess_career`<br>`capability:marsys://tool/L-DOMAIN/assess_health → assess_health`<br>…+21 |
| `bo_yantra_mechanism` | bodha | DRAFT | data | `bodha_mechanisms` | 10 | 0 | 12 | 1 | Y | serving consumer detected | `capability:marsys://tool/L-JUDGMENT/judgment_query → judgment_query`<br>`capability:marsys://tool/L2/query_mechanisms → bodha_mechanisms_get`<br>`mcp_tool:bodha_mechanisms_get`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>`mcp_tool:prashna_status`<br>…+4 |
| `ga_ayurdaya` | ganita | CURRENT | data | `chart_facts` | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_condition` | ganita | CURRENT | data | `ga_condition_composite` | 71 | 50 | 312 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+65 |
| `ga_dashas` | ganita | CURRENT | data | `chart_dashas` | 45 | 33 | 65 | 3 | Y | serving consumer detected | `api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/mcp/prashna_ask`<br>`api_route:/api/pariprashna`<br>`capability:marsys://tool/L1/get_dasha_lord_capability → ganita_dasha_lord_capability_get`<br>`capability:marsys://tool/L3/call_dasha_eligibility`<br>…+39 |
| `ga_medical` | ganita | CURRENT | data | `ga_medical` | 1 | 0 | 5 | 1 | Y | serving consumer detected | `capability:marsys://tool/L1/get_medical_indications` |
| `ga_nakshatra` | ganita | CURRENT | data | `chart_facts` | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_panchanga` | ganita | CURRENT | data | `chart_facts` | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_positions` | ganita | CURRENT | data | `chart_facts` | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_prashna` | ganita | CURRENT | data | `ga_prashna_judgment` | 4 | 0 | 7 | 2 | · | serving consumer detected | `capability:marsys://tool/L1/get_prashna_lagna`<br>`mcp_tool:prashna_undertaking_get`<br>`sidecar_endpoint:GET /health`<br>`sidecar_endpoint:POST /cast` |
| `ga_sade_sati` | ganita | CURRENT | data | — | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_sensitive` | ganita | CURRENT | data | — | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_sensitive_degree` | ganita | CURRENT | data | `chart_facts` | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_strength` | ganita | CURRENT | data | — | 70 | 50 | 294 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_structural` | ganita | CURRENT | data | — | 70 | 50 | 296 | 55 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/assets/[chart_id]/[asset_key]`<br>`api_route:/api/build/school-consensus`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>…+64 |
| `ga_tajaka` | ganita | CURRENT | data | `l1_tajik_varsha_year_lords` | 36 | 15 | 12 | 1 | Y | serving consumer detected | `api_route:/api/build/school-consensus`<br>`capability:marsys://tool/L1/get_tajik → ganita_tajaka_get`<br>`mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>…+30 |
| `ga_transit_anchors` | ganita | CURRENT | data | `ga_transit_anchors` | 1 | 0 | 3 | 0 | · | serving consumer detected | `capability:marsys://tool/L1/get_transit_anchors → ganita_transit_anchors_get` |
| `ga_vargas` | ganita | CURRENT | data | `chart_divisionals` | 120 | 17 | 41 | 5 | Y | serving consumer detected | `api_route:/api/chat/consult`<br>`capability:marsys://tool/L0/find_verses_about → find_verses_about`<br>`capability:marsys://tool/L0/list_classical_texts → list_classical_texts`<br>`capability:marsys://tool/L0/list_remedies_by_category → ref_remedies_by_category_list`<br>`capability:marsys://tool/L0/list_sutravali_rules_by_text`<br>`capability:marsys://tool/L0/query_mantras → ref_mantras_get`<br>…+114 |
| `ga_vastu` | ganita | CURRENT | data | `ga_vastu_planet_direction_map` | 4 | 0 | 5 | 1 | Y | serving consumer detected | `capability:marsys://tool/L1/get_vastu_directions → ganita_vastu_get`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>`mcp_tool:prashna_status` |
| `ga_vichara` | ganita | DRAFT | data | `chart_vichara` | 11 | 14 | 26 | 1 | Y | serving consumer detected | `capability:marsys://tool/L-JUDGMENT/judgment_query → judgment_query`<br>`capability:marsys://tool/L1/get_dasha_lord_capability → ganita_dasha_lord_capability_get`<br>`capability:marsys://tool/L1/get_vichara`<br>`capability:marsys://tool/L2/query_remedies → bodha_remedies_get,get_remedies`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>…+5 |
| `ga_yoga` | ganita | CURRENT | data | `ga_yoga_firings` | 3 | 8 | 15 | 3 | · | serving consumer detected | `capability:marsys://tool/L-JUDGMENT/judgment_query → judgment_query`<br>`capability:marsys://tool/L1/get_yoga_dosha`<br>`capability:marsys://tool/L1/get_yoga_firings` |
| `ka_avadhi` | kala | CURRENT | data | `kala_avadhi` | 1 | 0 | 5 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_dasha_dossier` |
| `ka_bhavishya_lekha` | kala | DRAFT | artifact | `kala_bhavishya` | 32 | 1 | 9 | 1 | · | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`capability:marsys://tool/L3/query_projections → get_projections,kala_projections_get`<br>`capability:marsys://tool/L3/query_temporal_activation → get_temporal_windows,kala_windows_get`<br>`mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>…+26 |
| `ka_dasha_kala` | kala | DRAFT | service | — | 0 | 0 | 0 | 0 | · | writer consumers only (code-module interface) | — |
| `ka_gochara` | kala | CURRENT | data | `kala_gochara_windows` | 29 | 2 | 27 | 0 | Y | serving consumer detected | `mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>`mcp_tool:chart_snapshot`<br>`mcp_tool:get_cgm_subgraph`<br>…+23 |
| `ka_gochara_resonance` | kala | CURRENT | data | `gochara_resonance_map` | 31 | 7 | 16 | 2 | · | serving consumer detected | `mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>`mcp_tool:chart_snapshot`<br>`mcp_tool:get_cgm_subgraph`<br>…+25 |
| `ka_gochara_sweep` | kala | RETIRED | data | `kala_gochara_windows` | 29 | 1 | 27 | 0 | Y | serving consumer detected | `mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>`mcp_tool:chart_snapshot`<br>`mcp_tool:get_cgm_subgraph`<br>…+23 |
| `ka_gochara_v3_century_materialize` | kala | CURRENT | data | `kala_gochara_windows_v2` | 0 | 2 | 6 | 5 | · | writer consumers only | — |
| `ka_graha_sancara` | kala | DRAFT | service | — | 0 | 0 | 0 | 0 | · | writer consumers only (code-module interface) | — |
| `ka_jivana_parva` | kala | DRAFT | artifact | `kala_jivana_parva` | 4 | 0 | 6 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_life_arc → kala_life_arc_get,query_life_arc`<br>`mcp_tool:mcp_server_info`<br>`mcp_tool:prashna_ask`<br>`mcp_tool:prashna_status` |
| `ka_kala_darshana` | kala | DRAFT | artifact | `kala_darshana` | 1 | 3 | 8 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_temporal_view` |
| `ka_kalasutra` | kala | DRAFT | artifact | `kala_activation` | 7 | 0 | 4 | 1 | · | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`capability:marsys://tool/L3/call_dasha_eligibility`<br>`capability:marsys://tool/L3/call_ephemeris_at_t`<br>`capability:marsys://tool/L3/call_muhurta_score`<br>`capability:marsys://tool/L3/call_priority_ranking`<br>`capability:marsys://tool/L3/call_transit_search`<br>…+1 |
| `ka_kota_chakra` | kala | CURRENT | data | `kala_kota_chakra` | 1 | 0 | 6 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_kota_chakra` |
| `ka_kshetra` | kala | CURRENT | data | `kala_field` | 0 | 1 | 8 | 1 | · | writer consumers only | — |
| `ka_moorti_nirnaya` | kala | CURRENT | data | `kala_moorti_nirnaya` | 1 | 0 | 6 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_moorti_nirnaya` |
| `ka_muhurta_seva` | kala | DRAFT | service | — | 0 | 0 | 0 | 0 | · | writer consumers only (code-module interface) | — |
| `ka_sangam` | kala | DRAFT | artifact | `kala_convergence` | 1 | 14 | 29 | 5 | Y | serving consumer detected | `capability:marsys://tool/L3/query_convergence_windows → query_convergence_windows` |
| `ka_sudarshana_varsha` | kala | CURRENT | data | `kala_sudarshana_varsha` | 1 | 0 | 6 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_sudarshana_varsha` |
| `ka_taranga` | kala | CURRENT | data | `kala_taranga` | 5 | 0 | 7 | 2 | · | serving consumer detected | `capability:marsys://tool/L3/query_activation_waveform`<br>`sidecar_endpoint:GET /health`<br>`sidecar_endpoint:POST /activation`<br>`sidecar_endpoint:POST /curve`<br>`sidecar_endpoint:POST /record_evidence` |
| `ka_tithi_pravesha` | kala | CURRENT | data | `kala_tithi_pravesha` | 1 | 0 | 6 | 1 | Y | serving consumer detected | `capability:marsys://tool/L3/query_tithi_pravesha` |
| `ka_tulana` | kala | DRAFT | service | — | 0 | 0 | 0 | 0 | · | UNKNOWN — asset declares no table and no reachable code interface | — |
| `ka_vedha_gochara` | kala | CURRENT | data | `kala_vedha_gochara` | 1 | 1 | 8 | 1 | · | serving consumer detected | `capability:marsys://tool/L3/query_vedha_gochara` |
| `ka_vighnakara` | kala | DRAFT | artifact | `kala_obstruction` | 1 | 3 | 9 | 4 | Y | serving consumer detected | `capability:marsys://tool/L3/query_obstruction_periods` |
| `ka_yojaka` | kala | DRAFT | artifact | `kala_activation_predicates` | 2 | 5 | 8 | 1 | · | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`capability:marsys://tool/L3/query_temporal_activation → get_temporal_windows,kala_windows_get` |
| `lel_events` | mimamsa | DRAFT | data | — | 8 | 6 | 22 | 8 | Y | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`api_route:/api/mcp/writes/[action]`<br>`capability:marsys://tool/L5/lel_query → lel_query`<br>`capability:marsys://tool/L5/mechanism_retrodiction_get → mechanism_retrodiction_get`<br>…+2 |
| `mi_abhilekha` | mimamsa | DRAFT | service | `mimamsa_journal` | 4 | 0 | 6 | 0 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_journal` |
| `mi_adhilepa` | mimamsa | DRAFT | data | `mimamsa_load_bearing` | 4 | 1 | 10 | 1 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_load_bearing` |
| `mi_bhara` | mimamsa | DRAFT | data | `kala_field_weight_versions` | 31 | 1 | 5 | 3 | Y | serving consumer detected | `mcp_tool:assess_career`<br>`mcp_tool:assess_health`<br>`mcp_tool:assess_marriage`<br>`mcp_tool:assess_wealth`<br>`mcp_tool:chart_snapshot`<br>`mcp_tool:get_cgm_subgraph`<br>…+25 |
| `mi_bhavisya` | mimamsa | DRAFT | data | `mimamsa_predictions` | 10 | 5 | 20 | 6 | · | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/chat/consult`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`api_route:/api/mcp/prashna_ask`<br>…+4 |
| `mi_darshana` | mimamsa | DRAFT | data | `mimamsa_insight_units` | 6 | 0 | 12 | 3 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_insight_embeddings`<br>`capability:marsys://tool/L5/query_insights → mimamsa_insight_get`<br>`mcp_tool:synth_chart_brief_get` |
| `mi_gunanaka` | mimamsa | DRAFT | data | `mimamsa_multipliers` | 3 | 2 | 11 | 5 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/clients/[id]/learning`<br>`capability:marsys://tool/L5/query_calibration → mimamsa_calibration_get` |
| `mi_jivanaghatana` | mimamsa | DRAFT | data | `mimamsa_event_provenance` | 0 | 2 | 5 | 1 | · | writer consumers only | — |
| `mi_kula` | mimamsa | DRAFT | data | `mimamsa_signal_families` | 4 | 2 | 12 | 2 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_signal_families` |
| `mi_pariksha` | mimamsa | DRAFT | data | `mimamsa_qa_eval` | 8 | 1 | 20 | 10 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_attribution`<br>`capability:marsys://tool/L5/query_calibration → mimamsa_calibration_get`<br>…+2 |
| `mi_pramana` | mimamsa | DRAFT | data | `mimamsa_calibration` | 9 | 5 | 18 | 6 | Y | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/clients/[id]/learning`<br>`api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L5/query_calibration → mimamsa_calibration_get`<br>…+3 |
| `mi_sambandha` | mimamsa | DRAFT | data | `mimamsa_manifestation_grammar` | 2 | 1 | 6 | 1 | · | serving consumer detected | `capability:marsys://tool/L5/query_manifestation_grammar`<br>`capability:marsys://tool/L5/query_manifestation_sets` |
| `mi_sankalpa` | mimamsa | DRAFT | data | `mimamsa_intervention_ledger` | 1 | 0 | 8 | 2 | Y | serving consumer detected | `api_route:/api/mcp/writes/[action]` |
| `mi_seva` | mimamsa | DRAFT | service | `mimamsa_preferences` | 3 | 0 | 2 | 0 | · | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs` |
| `mi_vistara` | mimamsa | DRAFT | data | `mimamsa_export_log` | 3 | 0 | 6 | 1 | Y | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs` |
| `ph_muhurta` | phala | DRAFT | artifact | `phala_muhurta` | 9 | 1 | 7 | 2 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+3 |
| `ph_nimitta` | phala | DRAFT | artifact | `phala_anchors` | 16 | 10 | 30 | 1 | · | serving consumer detected | `api_route:/api/admin/internal/spine-bundle-refresh`<br>`api_route:/api/clients/[id]/learning`<br>`capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>…+10 |
| `ph_phaladesa` | phala | DRAFT | artifact | `phala_phaladesa` | 1 | 0 | 4 | 1 | · | serving consumer detected | `capability:marsys://tool/L4/query_domain_result` |
| `ph_pramana` | phala | DRAFT | artifact | `phala_pramana` | 7 | 1 | 5 | 2 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+1 |
| `ph_pratikara` | phala | DRAFT | artifact | `phala_mitigation` | 8 | 1 | 6 | 3 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+2 |
| `ph_rectification` | phala | DRAFT | artifact | `phala_rectification` | 30 | 1 | 14 | 5 | Y | serving consumer detected | `api_route:/api/cockpit/clear`<br>`api_route:/api/cockpit/clear/execute`<br>`api_route:/api/cockpit/runs`<br>`capability:marsys://tool/L0/find_verses_about → find_verses_about`<br>`capability:marsys://tool/L0/list_classical_texts → list_classical_texts`<br>`capability:marsys://tool/L0/list_remedies_by_category → ref_remedies_by_category_list`<br>…+24 |
| `ph_sankrama` | phala | DRAFT | artifact | `phala_sankrama` | 7 | 1 | 5 | 2 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+1 |
| `ph_sodhana` | phala | DRAFT | artifact | `phala_sodhana` | 7 | 1 | 6 | 2 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+1 |
| `ph_suddha_sodhana` | phala | DRAFT | artifact | `phala_suddha_sodhana` | 7 | 1 | 5 | 2 | · | serving consumer detected | `capability:marsys://tool/L4/query_anomaly_flags`<br>`capability:marsys://tool/L4/query_auspicious_windows`<br>`capability:marsys://tool/L4/query_cleansed_anchors`<br>`capability:marsys://tool/L4/query_falsifiers`<br>`capability:marsys://tool/L4/query_rectification → phala_rectification_get`<br>`capability:marsys://tool/L4/query_remedy_program`<br>…+1 |

## 5 — Co-written tables: attribution is table-level, not partition-level

Where two or more assets declare the same `target_table` (census §5), a consumer of the table is not necessarily a consumer of *this* asset's rows. The affected assets are listed so the over-attribution is visible rather than silently absorbed:

| target_table | assets sharing it |
|---|---|
| `bodha_msr_signals` | `bo_arudha`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` |
| `brahma_class_priors` | `bg_class_lifetime_counts`, `bg_class_priors` |
| `chart_facts` | `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive_degree` |
| `classical_text_chunks` | `bg_text_index`, `bg_texts` |
| `kala_gochara_windows` | `ka_gochara`, `ka_gochara_sweep` |

## 6 — What this document does NOT establish

- It does not prove any surface is reachable by a real caller at runtime, nor that a detected read executes on any code path a user can trigger.
- It does not prove an asset with no detected consumer is unused — only that this method, with the limits in §2, found none.
- It does not evaluate whether any asset's rows are correct, complete or current.
- It proposes no disposition and takes none. Promote / retire / reclassify is ADHIKĀRIN's G1 power, on this evidence (charter §1).
- It certifies nothing. Verification belongs to PARĪKṢAKA (I16).

