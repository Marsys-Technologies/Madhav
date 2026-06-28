---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT
version: 1.1
status: RESOLVED — all §0 parameters filled; ready for D5 execution
created: 2026-06-27
resolved: 2026-06-28
author: Cowork (planning) — detail-pass by Claude Code (D5-DETAIL-PASS agent)
classification: CLAUDECODE_BRIEF — D5 per-asset / per-layer retrieval-surface fan-out
session_type: implementation — apply the topology framework to all 81 assets (layer-sub-waved)
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (wave D5); RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY (the rules)
depends_on: D1 (contract), D3 (grounding), D4 (graph)
detail_pass_sources:
  - RETRIEVAL_GROUNDTRUTH_RUNTIME_FINDINGS_v1_0.md (V1–V15; data-plane reality)
  - RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX_v1_0.md (8 archetypes, per-asset comprehension)
  - RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL_v1_0.md (6 traversal levels, classical hierarchy)
  - platform/src/lib/retrieval/registry/types.ts (D1 frozen contract)
  - platform/src/lib/retrieval/registry/layers/ (existing L0/L1/L2 capabilities + L3–L5 gaps)
  - platform/scripts/seed/asset_registry_seed.ts (81 assets, authoritative source)
hard_constraints:
  - chart-agnostic (#14) on every tool; F1 dedup + completeness + retrievability by construction
  - apply the topology decision rules R1–R6 per asset — do not invent shapes ad hoc
  - DEFECT-001 (constituent_facts_array 91.5% orphan rate) is OPEN; D5 tools that surface L1
    provenance MUST note this and gracefully handle empty constituent_facts lookups
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D5: PER-ASSET FAN-OUT (v1.1 — RESOLVED)

> Apply the tool-topology framework to every one of the 81 assets, layer by layer, producing the
> full tool roster. The decision rules are settled (R1–R6); this v1.1 fills all parameterized
> markers with specific per-layer, per-asset data from runtime validation and the frozen D1 contract.

---

## §0 — Resolved parameters (detail-pass log)

### §0.1 — [resolved from D1] — Frozen RetrievalSurface contract

Source: `platform/src/lib/retrieval/registry/types.ts` (freeze declaration at top of file,
amendment_version: 1, initial freeze 2026-06-28).

Every tool `CapabilityDescriptor` MUST carry these fields:

| Field | Type | Notes |
|---|---|---|
| `uri` | `CapabilityUri` | format: `marsys://tool\|resource\|prompt/LAYER/name` |
| `type` | `'tool'\|'resource'\|'prompt'` | |
| `layer` | `'L0'…'L5'` | |
| `name` | string | short human-readable |
| `description` | string | LLM-facing; MUST NOT contain literal chart_id `482012f1-…` or native name |
| `scope` | `'per_chart'\|'global'` | |
| `archetype` | `RetrievalArchetype` | one of 8 (see §0.1a) |
| `traversal_level` | `TraversalLevel` | one of 5 (see §0.1b) |
| `tool_role` | `ToolRole` | one of 7 (see §0.1c) |
| `emits_references` | boolean | true if tool returns signal_id/fact_id refs (not restated data) |
| `lel_capable` | boolean | true if tool may surface lel_origin=true signals |
| `required_inputs` | string[] | per_chart MUST include `'chart_id'` |
| `handler` | `CapabilityHandler` | `(args, ctx?) => Promise<ToolResult>` |
| `drill_children?` | `CapabilityUri[]` | umbrella/drill tools only |
| `grounds_to?` | `{l1_fact_ids?, l0_citation_ids?}` | F3 layer-resolution-DOWN |

**Per-chart enforcement:** if `scope === 'per_chart'`, `required_inputs` MUST include `'chart_id'`
and the handler MUST error if chart_id is absent. The CI gate `chart_agnostic_gate.ts` enforces this
at build time.

#### §0.1a — The 8 RetrievalArchetypes (from types.ts)

```
flat_fact         — exact keyed lookup (L1 positions, dignity, strength, etc.)
prose_citation    — hybrid BM25+dense retrieval over verse/rule corpora (L0 texts)
rich_relational   — multi-vantage reconciled surface (L2 signals, domain framing)
graph_traversal   — CGM/CDLM graph traversal (bo_bimba, bo_karanajala)
cross_domain      — contradiction/convergence across domains (bo_sangati, CDLM)
temporal          — time-keyed (dashas, transits, L3 kala)
orientation_digest — whole-chart gestalt entry (bo_samvada UCD, asset catalogs)
calibration       — quality/trust metadata (bo_pramana_mapa, L5 mimamsa)
```

#### §0.1b — The 5 TraversalLevels (from types.ts)

```
L-ORIENT   — Whole-chart orientation — first call of nearly every reading
L-OVERVIEW — Layer or domain overview (asset catalog, list operations)
L-DOMAIN   — Life-domain framing (career, health, relationship, etc.)
L-SIGNAL   — Individual signal / factor drill (specific graha, yoga, dosha)
L-SOURCE   — Classical citation / classical grounding (verse, rule, sutra)
```

#### §0.1c — The 7 ToolRoles (from types.ts)

```
umbrella          — broad entry tool returning surface + drill pointers
drill             — intermediate drill (narrows domain; returns finer pointers)
leaf              — terminal fact lookup (returns data, not pointers)
graph             — graph traversal (neighbors / paths / clusters)
hybrid_retrieval  — BM25+dense+rerank prose retrieval
temporal          — time-keyed tool family
quality           — calibration/trust surface
```

---

### §0.2 — [resolved from runtime brief] — Which assets have DATA populated per chart

Source: `RETRIEVAL_GROUNDTRUTH_RUNTIME_FINDINGS_v1_0.md` (V1–V6 + §A summary).
Native chart_id: `482012f1-710e-4a25-994a-93821f5871aa`.
Secondary chart (Abhinandan): `1c826d5a-41cb-4450-b4dc-59d440e5f75a` — 58,674 signals, clean isolation.

**CRITICAL DATA NOTE:** chart_facts live count = **142,416** (not 27,554 stated in CLAUDE.md §B — that was
the old closure count). Use 142,416 as the live canonical L1 reference in all D5 tool descriptions.

**DEFECT-001 (OPEN, HALT-WORTHY):** 61,161 / 66,832 constituent_facts_array references in
bodha_msr_signals (91.5%) are unresolvable orphan fact_ids. Root cause: L2 Bodha structural writer used
an old L1 fact_id scheme; L1 was rebuilt with new SHA hashes. Any D5 tool path that attempts to surface
L1 provenance for Bodha signals MUST handle empty joins gracefully (see §1.3 below).

#### Per-layer data population verdict

| Layer | Status | Key counts (native chart) | D5 tool stance |
|---|---|---|---|
| **L0 Brahmagyan** | BUILT (global) | bg_texts: 10,651 chunks (100% embedded); bg_rules: 2,912; bg_reference: 1,485 rows (15 tables); bg_ontology: 623; bg_nakshatra: 2,857; bg_concordance: 800; bg_compendium_index: 9,538 | LIVE — serve fully |
| **L1 Gaṇita** | BUILT | chart_facts: 142,416; chart_dashas: 536,424; chart_divisionals: 21,635; ga_yoga_firings: 5; ga_condition_composite: 45 + 2,835 per-varga; ga_transit_anchors: 45; ga_medical: 45; ga_vastu_planet_direction_map: 40; l1_tajik_varsha_year_lords: 240 | LIVE — serve fully |
| **L2 Bodha** | BUILT | bodha_msr_signals: 66,738; bodha_signal_embeddings: 66,738 (100%); bodha_cgm_nodes: 140; bodha_cgm_edges: 360; bodha_cdlm_cells: 70; bodha_convergence: 19,482 (in L3); bodha_rm_resonances: 45; bodha_rm_remedy_prescriptions: 135; bodha_question_lenses: 60; bodha_discoveries: 1,505; bodha_anomalies: 4,265; synthesis_quality_scorecard: 2; vw_chart_digest: 5 rows | LIVE — serve fully; note DEFECT-001 on constituent_facts provenance |
| **L3 Kāla** | PARTIAL | kala_activation: 66,738; kala_activation_predicates: 66,738; kala_convergence: 19,482; kala_jivana_parva: 739; kala_bhavishya: 50; **kala_obstruction: 0 (EMPTY)**; **kala_darshana: 0 (EMPTY)** | PARTIAL — ka_vighnakara and ka_kala_darshana tools STUBBED-PENDING-DATA |
| **L4 Phala** | BUILT (sparse) | phala_anchors: 150; phala_sodhana: 200; phala_muhurta: 100; phala_pramana: 150; phala_sankrama: 73; phala_phaladesa: 7 | LIVE (sparse) — serve with sparse-row note |
| **L5 Mīmāṃsā** | PARTIAL (minimal) | mimamsa_predictions: 50; mimamsa_insight_units: 10; mimamsa_qa_eval: 5; **mimamsa_calibration: 0 (EMPTY)** | PARTIAL — mi_pramana tool STUBBED-PENDING-DATA |

**vw_chart_digest sample output (native, Lahiri):** msr_signal_count=66738, top_convergence_domains=
[career(12,334 signals, score 9,068), relationship(7,357), character(6,580), spirituality(3,527),
wealth(2,512), health(903)], contradiction_count=0, weakest_graha=Sun, top_priority_class=medium.

**Degenerate distribution notes (from V12):**
- `signature_tier`: 100% of 66,738 signals are 'background' — zero foreground/primary/apex. D5 tools
  that rank by signature_tier get no discrimination. Use `computed_salience` as the sole ranking column.
- `relationship_basis` on bodha_cgm_edges: 100% NULL. CGM traversal tools can traverse the graph but
  cannot filter by relationship type.
- `lel_origin=true`: 0 signals currently. LEL toggle is safe to expose but returns 0 rows until LEL
  signals are ingested (future build step).

---

### §0.3 — [resolved from D0.5 manifest reconciliation] — Authoritative asset list

Source: `platform/scripts/seed/asset_registry_seed.ts` (81 assets, AUTHORITATIVE operational catalog).
Runtime confirmation: `asset_registry` table has exactly 81 rows, bg=22 / ga=16 / bo=10 / ka=12 / ph=9 / mi=12.
All 81 non-null `target_table` references resolve to actual pg_tables or pg_views (0 dangling references).

**Two-catalog rule (MUST NOT confuse):**
- `asset_registry` seed (81 assets, `asset_id` = `bg_*`/`ga_*`/…) — the queryable/buildable OPERATIONAL source
- `CAPABILITY_MANIFEST.json` (112 entries as of 2026-06-27T18:27Z) — the docs/capability/retrieval-tool catalog

D5 tools are grounded in the **seed** for queryable surface (count_sql/scope/target_table); the manifest
for docs/expose_to_chat catalog registration. They are NOT interchangeable.

**Per-layer asset_id roster (from seed, authoritative):**

L0 Brahmagyan (22): bg_ephemeris, bg_reference, bg_texts, bg_ontology, bg_text_index, bg_rules,
bg_remedies, bg_concordance, bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index,
bg_panchanga (service), bg_ephemeris_engine (service), bg_nakshatra, bg_prashna_rules,
bg_vastu_directions, bg_transit_engine, bg_transit_rules, bg_medical_mappings, bg_nakshatra_medical,
bg_dignity_reference.

L1 Gaṇita (16): ga_positions, ga_vargas, ga_dashas, ga_strength, ga_sensitive, ga_panchanga,
ga_sade_sati, ga_tajaka, ga_structural, ga_nakshatra, ga_condition, ga_yoga, ga_vastu, ga_medical,
ga_prashna, ga_transit_anchors.

L2 Bodha (10): bo_laksana, bo_karanajala, bo_bimba, bo_samskara, bo_sangati, bo_upaya, bo_samvada,
bo_pramana_mapa, bo_drishti, bo_anveshana.

L3 Kāla (12): ka_gochara (service), ka_graha_sancara (service), ka_dasha_kala (service),
ka_muhurta_seva (service), ka_kalasutra, ka_sangam, ka_vighnakara (EMPTY), ka_yojaka,
ka_kala_darshana (EMPTY), ka_jivana_parva, ka_bhavishya_lekha, ka_tulana (service).

L4 Phala (9): ph_nimitta, ph_muhurta, ph_sodhana, ph_pratikara, ph_suddha_sodhana, ph_sankrama,
ph_pramana, ph_phaladesa, ph_rectification.
NOTE: seed lists ph_pratikara (target_table: phala_mitigation) and ph_suddha_sodhana
(target_table: phala_suddha_sodhana) — not seen in runtime V3 which only checked: phala_anchors,
phala_phaladesa, phala_sodhana, phala_muhurta, phala_pramana, phala_sankrama. ph_pratikara /
ph_suddha_sodhana / ph_rectification runtime counts unknown — treat as sparse.

L5 Mīmāṃsā (12): mi_jivanaghatana (global), mi_kula (global), mi_bhavisya, mi_pramana (EMPTY),
mi_gunanaka, mi_adhilepa, mi_pariksha, mi_sambandha, mi_darshana (pgvector), mi_vistara (global),
mi_seva (service), mi_abhilekha (service).

---

### §0.4 — [resolved from acharya validation] — Traversal-model ordering

Source: `RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL_v1_0.md` (status: DRAFT — research-grounded,
acharya validation pending; never freeze as final).

The classical reading sequence (BPHS / Phaladeepika / Jataka Parijata, as documented) maps to:

```
L-ORIENT  → bo_samvada (UCD) + bo_laksana chart-defining signatures
L-DOMAIN  → bo_drishti (question lenses) + bo_sangati (CDLM domain cells)
L-FACTOR  → ga_positions, ga_condition, ga_strength, ga_structural; bo_laksana signals
L-DERIVATION (maps to L-SIGNAL in D1 types.ts) → bo_bimba/bo_karanajala (CGM), bodha_contradictions, bo_anveshana
L-TIMING  → ga_dashas, ga_tajaka, ga_sade_sati; L3 Kāla (ka_*)
L-SOURCE  → bg_texts, bg_rules, bg_yogas; classical_sources_jsonb on each signal
```

**Multi-vantage mandate:** every domain matter must be read from house + kāraka + varga. The domain
umbrella tools MUST return a reconciled multi-vantage view (one entry, perspectives attached — F1).

**Anchor-to-D1-and-Moon mandate:** every divisional/temporal view is read alongside D1 and the Moon,
never free-floating. D5 tools serving L3/L4 MUST accept ayanamsha_id as a filter.

---

## §1 — Layer sub-waves: per-asset topology decisions

For each asset: R1 (classify archetype) → R2 (traversal level) → R3 (map to tool shape) →
R4 (consolidate siblings) → R5 (umbrella owns multi-vantage reconciliation) → R6 (drill-by-reference).

### §1.0 — Existing capabilities (already implemented — DO NOT re-implement)

**L0 Brahmagyan** (`layers/L0_brahmagyan/`): 15 capabilities registered:
- `resolve_entity` — entity resolution over bg_ontology (global, flat_fact, L-OVERVIEW, leaf)
- `list_entities` — catalog list (global, orientation_digest, L-OVERVIEW, umbrella)
- `query_classical_texts` — hybrid BM25+dense over bg_texts (global, prose_citation, L-SOURCE, hybrid_retrieval)
- `query_yoga_catalog` — bg_yogas lookup (global, flat_fact, L-SOURCE, leaf)
- `query_dosha_catalog` — bg_doshas lookup (global, flat_fact, L-SOURCE, leaf)
- `query_remedy_corpus` — bg_remedies retrieval (global, prose_citation, L-SOURCE, hybrid_retrieval)
- `query_planet_transit` — transit event search via ka_gochara (global, temporal, L-SIGNAL, temporal)
- `query_planet_position` — positions at arbitrary time (global, flat_fact, L-SIGNAL, leaf)
- `query_aspects_at_time` — aspects at arbitrary time (global, flat_fact, L-SIGNAL, leaf)
- `query_retrograde_periods` — retrograde windows (global, temporal, L-SIGNAL, temporal)
- `ephemeris_cache_year` — yearly ephemeris bundle (global, flat_fact, L-OVERVIEW, leaf)
- `ephemeris_cache_native_lifetime` — lifetime ephemeris (global, flat_fact, L-OVERVIEW, leaf)
- `intent_classify` — route user intent to tool (global, orientation_digest, L-ORIENT, umbrella)
- `asset_registry_all` — full asset catalog (global, orientation_digest, L-OVERVIEW, umbrella)
- `asset_registry_l0` — L0-only catalog (global, orientation_digest, L-OVERVIEW, umbrella)

**L1 Gaṇita** (`layers/L1_ganita/`): 19 capabilities registered:
- `get_positions` — ga_positions (chart_facts graha_position/graha_sign_attributes)
- `get_strength` — ga_strength (shadbala, vimsopaka, bhava_bala families)
- `get_ashtakavarga` — ga_strength ashtakavarga family
- `get_bhava_bala` — ga_strength bhava_bala family
- `get_aspects` — ga_structural aspect_* facts
- `get_yoga_dosha` — ga_yoga (ga_yoga_firings) + ga_structural yoga_fires/dosha_fires
- `get_argala` — ga_structural argala_natal_matrix/net_argala
- `get_dispositors` — ga_structural graha_dispositor_*/dispositor_tree/nakshatra_dispositor_chain
- `get_sade_sati` — ga_sade_sati (chart_facts sade_sati_* family)
- `get_panchanga` — ga_panchanga (chart_facts panchanga_* family)
- `get_sensitive_points` — ga_sensitive (upagraha, saham, arudha, KP, tajik families)
- `get_karakas` — ga_structural karaka_* / jaimini_tri_deva_role_per_graha
- `get_dignity` — ga_structural graha_composite_state_classification + bg_dignity_reference
- `get_avasthas` — ga_condition graha_avastha_* families
- `get_tajik` — ga_tajaka (l1_tajik_varsha_year_lords)
- `get_tara_chandra_bala` — ga_structural chandra_bala/tara_bala_natal_baseline
- `get_eclipse_flags` — ga_structural eclipse_proximity_natal
- `get_dashas` — ga_dashas (chart_dashas)
- `get_divisionals` — ga_vargas (chart_divisionals)

**L2 Bodha** (`layers/L2_bodha/`): 1 capability registered:
- `query_ucd` — bo_samvada (vw_chart_digest + bodha_msr_signals + bodha_convergence),
  archetype=orientation_digest, traversal_level=L-ORIENT, tool_role=umbrella,
  drill_children=[query_domain_reading, query_signals, traverse_chart_graph]

**L5 Mīmāṃsā** (`layers/L5_mimamsa/`): 2 capabilities registered:
- `query_insights` — mi_darshana (mimamsa_insight_units, pgvector)
- `query_calibration` — mi_pramana (mimamsa_calibration) — **STUBBED-PENDING-DATA** (0 rows)

---

### §1.1 — D5.2 L2 Bodha: gaps to fill

The L2 layer has 10 assets but only `query_ucd` is implemented. The drill children declared in
`query_ucd.drill_children` do not yet exist. D5 must implement:

**Tool: `query_domain_reading`** (per_chart, rich_relational, L-DOMAIN, drill)
- Assets: bo_drishti (bodha_question_lenses, 60 rows), bo_sangati (bodha_cdlm_cells, 70 rows)
- Input: chart_id, domain (career|wealth|relationship|health|character|spirituality|other), ayanamsha_id
- Returns: domain lens from bodha_question_lenses + CDLM cell for that domain pair
- emits_references: true (signal_id refs back to bo_laksana)
- lel_capable: false (no lel_origin data in domain lenses)
- drill_children: ['marsys://tool/L2/query_signals']
- grounds_to: {l1_fact_ids: true}
- **Graceful-empty:** if no domain lens for requested domain, return available domains list

**Tool: `query_signals`** (per_chart, rich_relational, L-SIGNAL, drill)
- Assets: bo_laksana (bodha_msr_signals, 66,738), bo_samskara (bodha_signal_embeddings, 66,738)
- Input: chart_id, ayanamsha_id, filters: [domain, source_subsystem, min_salience, semantic_query]
- Returns: ranked signals with signal_id, signal_summary_text, computed_salience, source_subsystem,
  domains_affected_array, constituent_facts_array (WARNING: 91.5% of refs are orphan — handle empty join)
- emits_references: true (returns signal_id; constituent_facts_array as reference list)
- lel_capable: true (lel_origin filter; currently returns 0 rows when lel_enabled=true)
- grounds_to: {l1_fact_ids: true, l0_citation_ids: true}
- Ranking: ORDER BY computed_salience DESC (signature_tier is fully degenerate — do NOT rank by tier)

**Tool: `traverse_chart_graph`** (per_chart, graph_traversal, L-SIGNAL, graph)
- Assets: bo_bimba (bodha_cgm_nodes, 140), bo_karanajala (bodha_cgm_edges, 360)
- Input: chart_id, ayanamsha_id, seed_signal_ids (array), depth (1-3), mode (neighbors|paths|cluster)
- Returns: node subgraph (signal_id, centrality scores) + edges (valenced; relationship_basis=NULL on all
  360 current edges — note this in output, do not error)
- emits_references: true
- grounds_to: {l1_fact_ids: true}
- NOTE: relationship_basis is 100% NULL on all edges (V12b finding). Tool MUST NOT filter by
  relationship_basis — return all edges and annotate null basis

**Tool: `query_contradictions`** (per_chart, cross_domain, L-SIGNAL, leaf)
- Assets: bo_sangati (bodha_contradictions, currently 0 rows), bo_anveshana (bodha_discoveries, 1,505)
- Input: chart_id, ayanamsha_id
- Returns: contradictions from bodha_contradictions (graceful-empty — 0 rows expected) +
  discoveries from bodha_discoveries ranked by novelty_score
- emits_references: true
- lel_capable: false
- **Graceful-empty:** bodha_contradictions = 0 is expected current state; return empty array, not error

**Tool: `query_remedies`** (per_chart, rich_relational, L-DOMAIN, drill)
- Assets: bo_upaya (bodha_rm_resonances: 45 + bodha_rm_remedy_prescriptions: 135)
- Input: chart_id, ayanamsha_id, tradition (mantra|gemstone|charity|vrata|yantra|ayurvedic), domain
- Returns: resonance targets + prescriptions filtered by tradition/domain
- emits_references: true (signal_id references from resonances)
- lel_capable: false

**Tool: `query_quality_scorecard`** (per_chart, calibration, L-OVERVIEW, quality)
- Assets: bo_pramana_mapa (synthesis_quality_scorecard, 2 rows)
- Input: chart_id
- Returns: most recent scorecard row; note that unresolved_constituent_facts_count=0 is a FALSE PASS
  per DEFECT-001 (actual orphan count is 61,161)
- emits_references: false
- lel_capable: false

---

### §1.2 — D5.3 L3 Kāla: full tool roster

L3 has 12 assets: 4 services + 4 data artifacts (populated) + 2 data artifacts (EMPTY) + 1 data
artifact (kala_jivana_parva) + 1 service (ka_tulana).

**Tool: `query_temporal_activation`** (per_chart, temporal, L-TIMING, umbrella)
- Assets: ka_kalasutra (kala_activation, 66,738), ka_yojaka (kala_activation_predicates, 66,738)
- Input: chart_id, ayanamsha_id, date_from, date_to, signal_ids (optional filter)
- Returns: activation windows from kala_activation + predicates from kala_activation_predicates
- emits_references: true (signal_id back to bo_laksana)
- drill_children: ['marsys://tool/L3/query_convergence_windows', 'marsys://tool/L3/query_life_arc']
- lel_capable: false

**Tool: `query_convergence_windows`** (per_chart, temporal, L-TIMING, drill)
- Assets: ka_sangam (kala_convergence, 19,482 rows)
- Input: chart_id, ayanamsha_id, date_from, date_to, min_convergence_score, domain
- Returns: scored convergence windows with convergence_score, rarity_years, confidence_score,
  independent_current_count
- emits_references: true
- lel_capable: false

**Tool: `query_obstruction_periods`** (per_chart, temporal, L-TIMING, leaf) — STUBBED-PENDING-DATA
- Asset: ka_vighnakara (kala_obstruction) — **EMPTY: 0 rows**
- Returns: {stubbed: true, reason: "kala_obstruction table contains 0 rows for this chart",
  data: []}
- emits_references: false
- NOTE: DO NOT omit this tool — stub it so the topology is complete and it becomes live when data
  is built

**Tool: `query_temporal_view`** (per_chart, temporal, L-TIMING, leaf) — STUBBED-PENDING-DATA
- Asset: ka_kala_darshana (kala_darshana) — **EMPTY: 0 rows**
- Returns: {stubbed: true, reason: "kala_darshana table contains 0 rows for this chart", data: []}
- emits_references: false

**Tool: `query_life_arc`** (per_chart, temporal, L-DOMAIN, drill)
- Asset: ka_jivana_parva (kala_jivana_parva, 739 rows)
- Input: chart_id, ayanamsha_id, mahadasha_lord (optional)
- Returns: biographical chapter rows — daśā-anchored parvas with theme keywords, quality labels
  (building/peak/consolidating/receding/transitional), convergence density
- emits_references: true (signal_id back to bo_laksana via activation link)
- lel_capable: false

**Tool: `query_projections`** (per_chart, temporal, L-TIMING, leaf)
- Asset: ka_bhavishya_lekha (kala_bhavishya, 50 rows)
- Input: chart_id, ayanamsha_id, horizon_years (default 3), probability_tier
  (tier_1_high|tier_2_moderate|tier_3_speculative)
- Returns: probabilistic forward projections with domain labels, falsifiability hooks, calibration records
- emits_references: true
- lel_capable: false

**Service tools (call-not-query, per §1 "lighter" sub-wave):**
- `call_transit_search` (global, temporal, L-TIMING, temporal) — wraps ka_gochara service
- `call_ephemeris_at_t` (global, temporal, L-TIMING, temporal) — wraps ka_graha_sancara service
- `call_dasha_eligibility` (per_chart, temporal, L-TIMING, temporal) — wraps ka_dasha_kala service
- `call_muhurta_score` (global, temporal, L-TIMING, temporal) — wraps ka_muhurta_seva service
- `call_priority_ranking` (per_chart, temporal, L-TIMING, temporal) — wraps ka_tulana service

---

### §1.3 — D5.4 L4 Phala: full tool roster

L4 has 9 data artifact assets (ph_*); all are `per_chart`, `catalog_status: DRAFT`, `scope: per_chart`.
Runtime: phala_anchors: 150; phala_sodhana: 200; phala_muhurta: 100; phala_pramana: 150;
phala_sankrama: 73; phala_phaladesa: 7. ph_pratikara/ph_suddha_sodhana/ph_rectification runtime
counts unknown — treat as sparse.

**Tool: `query_predictive_anchors`** (per_chart, rich_relational, L-DOMAIN, umbrella)
- Asset: ph_nimitta (phala_anchors, 150 rows)
- Input: chart_id, ayanamsha_id, domain (optional), derivation_axis (optional)
- Returns: predictive anchors with 8 derivation axes + 5 elevation fields
- emits_references: true (signal_id refs from anchor provenance)
- drill_children: ['marsys://tool/L4/query_domain_result', 'marsys://tool/L4/query_falsifiers']
- lel_capable: false
- grounds_to: {l1_fact_ids: true}

**Tool: `query_domain_result`** (per_chart, rich_relational, L-DOMAIN, drill)
- Asset: ph_phaladesa (phala_phaladesa, 7 rows — 7 domains × 1 row per chart)
- Input: chart_id, ayanamsha_id, domain (optional)
- Returns: B.11-compliant domain result declaration rows — anchor inventory, spillover coverage,
  mitigation/muhurta coverage. NOTE: 7 rows total, very sparse — this is by design (one row per domain)
- emits_references: true
- lel_capable: false

**Tool: `query_auspicious_windows`** (per_chart, temporal, L-TIMING, leaf)
- Asset: ph_muhurta (phala_muhurta, 100 rows)
- Input: chart_id, ayanamsha_id, date_from, date_to, event_class (optional)
- Returns: personalized auspicious windows scored by chart-strength + live-transit
- emits_references: true (anchor_id refs back to ph_nimitta)
- lel_capable: false

**Tool: `query_spillover_cascades`** (per_chart, cross_domain, L-DOMAIN, leaf)
- Asset: ph_sankrama (phala_sankrama, 73 rows)
- Input: chart_id, ayanamsha_id, source_domain (optional), target_domain (optional)
- Returns: cross-domain dynamics A→B→C cascades, conflicts, trajectory + mitigation routing
- emits_references: true (anchor_id back to ph_nimitta)
- lel_capable: false

**Tool: `query_falsifiers`** (per_chart, calibration, L-SIGNAL, quality)
- Asset: ph_pramana (phala_pramana, 150 rows)
- Input: chart_id, ayanamsha_id
- Returns: machine-evaluable falsifiers per L4 prediction; L5 onboarding contract status
- emits_references: true (prediction_id refs)
- lel_capable: false

**Tool: `query_anomaly_flags`** (per_chart, calibration, L-SIGNAL, quality)
- Asset: ph_sodhana (phala_sodhana, 200 rows)
- Input: chart_id, ayanamsha_id
- Returns: anomaly registry rows — 5 detector types (confidence inflation, magnitude drift,
  falsifier absent, ledger gap, layer leakage)
- emits_references: true
- lel_capable: false

**Tool: `query_remedy_program`** (per_chart, rich_relational, L-DOMAIN, leaf)
- Asset: ph_pratikara (phala_mitigation) — count unknown, treat as sparse
- Input: chart_id, ayanamsha_id, feasibility_tier (optional)
- Returns: managed remedy program rows — economics/feasibility tiered, sequenced, muhurta-timed
- emits_references: true (anchor_id back to ph_nimitta; remedy_id back to bo_upaya/bg_remedies)
- lel_capable: false

**Tool: `query_cleansed_anchors`** (per_chart, calibration, L-SIGNAL, quality)
- Asset: ph_suddha_sodhana (phala_suddha_sodhana) — count unknown
- Input: chart_id, ayanamsha_id, disposition (clean|flagged|staged_revision)
- Returns: cleansed disposition rows — one per phala_anchors entry; revision_approved_by always NULL
  (native sign-off required)
- emits_references: true (anchor_id back to ph_nimitta)
- lel_capable: false

**Tool: `query_rectification`** (per_chart, calibration, L-SIGNAL, quality)
- Asset: ph_rectification (phala_rectification) — count unknown; 185 candidate rows expected
- Input: chart_id, ayanamsha_id
- Returns: birth-time rectification candidates (±90 min, 5-min steps × 5 ayanamshas) — staged
  candidates only; canonical chart never auto-mutated (D43 NO-AUTO-OVERRIDE)
- emits_references: false
- lel_capable: false

---

### §1.4 — D5.5 L5 Mīmāṃsā: gaps to fill (beyond existing 2 capabilities)

L5 already has `query_insights` (mi_darshana) and `query_calibration` (mi_pramana, STUBBED-PENDING-DATA).
Remaining gaps:

**Tool: `query_predictions`** (per_chart, calibration, L-TIMING, quality)
- Asset: mi_bhavisya (mimamsa_predictions, 50 rows sparse)
- Input: chart_id, prediction_id (optional), outcome_status (pending|confirmed|disconfirmed|expired)
- Returns: logged predictions with confidence + falsifiers + outcome status
- emits_references: true (prediction_id → ph_pramana)
- lel_capable: false

**Tool: `query_signal_families`** (global, calibration, L-OVERVIEW, quality)
- Asset: mi_kula (mimamsa_signal_families — global catalog)
- Input: family_name (optional), include_negative_controls (bool)
- Returns: signal-family registry + negative-control battery
- scope: 'global' (no chart_id)
- emits_references: false
- lel_capable: false

**Tool: `query_manifestation_grammar`** (per_chart, calibration, L-SIGNAL, quality)
- Asset: mi_sambandha (mimamsa_manifestation_grammar) — count unknown
- Input: chart_id, signal_family (optional), house (optional)
- Returns: per-native grammar of how each signal/house/karaka expresses (structural + empirical cells)
- emits_references: true (signal_id back to bo_laksana)
- lel_capable: false

**`query_calibration`** (already registered) — STUBBED-PENDING-DATA:
- Asset: mi_pramana (mimamsa_calibration) — **EMPTY: 0 rows**
- Returns: {stubbed: true, reason: "mimamsa_calibration contains 0 rows", data: []}

**`query_insights`** (already registered) — SPARSE (10 rows):
- Asset: mi_darshana (mimamsa_insight_units, 10 rows, pgvector)
- Serve with sparse-row note in output

---

## §2 — Guarantees by construction

**F1 dedup (umbrella-first + reference-drill):**
- query_ucd is the single L-ORIENT entry point — it calls domain/signal tools by reference
- No tool re-states a fact already returned by a parent umbrella tool
- Drill tools return signal_id / fact_id references; composition layer resolves each once

**Completeness (full enumeration parity):**
- Salience is a column never a filter (query_signals returns all signals, sorted by salience)
- No silent truncation — all tools expose a top_k or limit parameter with explicit max
- EMPTY assets are explicitly stubbed (not silently omitted): ka_vighnakara, ka_kala_darshana,
  mi_pramana are explicitly STUBBED-PENDING-DATA

**Retrievability (hybrid for prose, structured hydration for facts):**
- L0 prose/citation assets use BM25+dense (query_classical_texts, query_remedy_corpus)
- L2 signal semantic path: bodha_signal_embeddings 100% populated — query_signals supports
  semantic_query parameter for vector similarity
- L1 facts: exact SQL keyed by (chart_id, fact_category) — chart-agnostic by construction

**Chart-agnostic gate (#14):**
- Every per_chart tool lists 'chart_id' in required_inputs
- No tool defaults chart_id to the native `482012f1-…` — that pattern is the CRITICAL defect
  found in V12b (4 tools in platform-mcp still have this — D5 tools MUST NOT repeat it)

---

## §3 — What this is NOT

Not new tool shapes (use R1–R6 from the topology framework). Not the router/graph/grounding
(consumed from D2/D3/D4). Not channel wiring (D7). Not a fix for DEFECT-001 (that is an L2
rebuild task outside D5 scope — but D5 tools MUST gracefully handle the 91.5% orphan state).

---

## §4 — Acceptance criteria

- Every asset in the 81-asset seed catalog has a contract-conformant CapabilityDescriptor OR is
  explicitly accounted for (service assets → call_* wrappers; EMPTY assets → STUBBED-PENDING-DATA).
- Roster collapses 81 assets into ~25 umbrella/drill/leaf/graph tools + 5 service wrappers +
  3 already-implemented stubs = total tool count ≤ 35 (not 81 tools — siblings are consolidated).
- All D1 contract fields present on every capability (archetype, traversal_level, tool_role,
  emits_references, lel_capable, scope, required_inputs).
- chart_id in required_inputs on every per_chart tool; NO native chart_id default anywhere.
- EMPTY assets (ka_vighnakara, ka_kala_darshana, mi_pramana) return {stubbed:true} not errors.
- DEFECT-001 note present on any tool that attempts constituent_facts_array lookups.
- Assets without populated data are explicitly noted in tool description and output.
- L3/L4/L5 index files (`layers/L3_kala/index.ts`, `layers/L4_phala/index.ts`) register all
  new capabilities (currently both index files are empty stubs).

---

## §5 — Detail-pass log: resolved markers

| Marker | Resolved from | Resolution |
|---|---|---|
| `[resolved from D1]` — frozen contract fields | `platform/src/lib/retrieval/registry/types.ts` | 15 required fields listed in §0.1; 8 archetypes, 5 traversal levels, 7 tool roles extracted |
| `[resolved from runtime brief]` — which assets have DATA | `RETRIEVAL_GROUNDTRUTH_RUNTIME_FINDINGS_v1_0.md` V1–V6, §A | Per-layer population table in §0.2; 3 EMPTY assets named; DEFECT-001 noted |
| `[resolved from D0.5 manifest reconciliation]` — authoritative asset list | `platform/scripts/seed/asset_registry_seed.ts` (81 assets) | Full per-layer asset_id roster in §0.3; runtime-confirmed 81 rows, 0 dangling target_tables |
| `[resolved from acharya validation]` — traversal-model ordering | `RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL_v1_0.md` | Classical L-ORIENT→L-DOMAIN→L-FACTOR→L-DERIVATION→L-TIMING→L-SOURCE sequence mapped to D1 traversal levels in §0.4 |

**Additional critical facts surfaced during detail-pass:**
- L1 chart_facts live count is 142,416 (not 27,554 stated in CLAUDE.md §B — L1 has grown since closure seal)
- signature_tier is 100% 'background' — all ranking must use computed_salience only
- relationship_basis is 100% NULL on 360 CGM edges — traverse_chart_graph must not filter by it
- L2 has only 1 implemented capability (query_ucd) out of 10 assets — 5 more tools needed
- L3 index.ts is an empty stub — 11 capabilities needed (5 service wrappers + 6 data tools)
- L4 index.ts is an empty stub — 9 tools needed
- L5 has 2 of ~5 needed capabilities; 3 more tools to add
- 4 platform-mcp tools have NATIVE_CHART_ID fallback (V12b) — D5 tools in lib/retrieval MUST NOT repeat

*End of CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT v1.1 (resolved) — 2026-06-28.*
