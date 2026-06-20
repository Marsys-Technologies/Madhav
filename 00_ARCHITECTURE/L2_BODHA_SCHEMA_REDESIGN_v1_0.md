---
artifact: L2_BODHA_SCHEMA_REDESIGN_v1_0.md
canonical_id: L2_BODHA_SCHEMA_REDESIGN
version: 1.0
status: SCHEMA_CONTRACT_FOR_NATIVE_REVIEW
authored_by: Cowork (grounded in live code: 14 L1 writers + mig 226 + ga_structural v2.0) 2026-06-19
purpose: >
  The single holistic schema contract for the ENTIRE L2 Bodha layer, redesigned for MAXIMUM COMPLETENESS
  — projecting ALL 14 L1 assets (not the original ~5), bridging every signal to L0, and carrying the deep
  graph value-vector. The bodha_* tables are EMPTY (never built), so this redesigns them freely; migration
  226 is the first draft this supersedes. Every per-asset build brief (the 8 that follow) builds to ITS
  SLICE of this contract. Settling the schema once, holistically, prevents brief rework.
grounded_against:
  - 14 L1 ga_ writers (live category inventory — see §2)
  - ga_structural v2.0 (build a712b250, 106,103 rows, 72 cats, refs in fact_value_jsonb.constituent_fact_ids)
  - migration 226 (22 bodha_* tables + 8 MVs — the schema being superseded)
  - L2_BODHA_OVERALL_APPROACH_v1_0 (the governing approach) + the A10–A14 specs
supersedes_schema_of: migration 226 (the new migration set this produces REPLACES 226's table defs; empty tables, no data risk)
---

# L2 Bodha — Schema Redesign v1.0 (the enriched contract)

## §1 — The redesign principles (what changed vs migration 226, and why)
Migration 226 was designed for the original scope (~5 L1 assets, no full L0 bridge, placeholder embeddings,
a curated MSR). Five things force a redesign for maximum completeness:

1. **Project ALL 14 L1 assets** — the MSR signal must be able to represent EVERY L1 category (positions,
   vargas [~30 cats], strength [per-varga shadbala+ashtakavarga], sensitive [sahams/tajik/special-lagnas],
   sade_sati, panchanga, dashas, tajaka, condition, structural [72 cats], medical, vastu, prashna, yoga).
   The original MSR assumed ~32 categories. → `fact_kind` typing + a category-agnostic configuration model.
2. **L0 classical bridge is first-class** — `classical_sources_array` exists in 226 but was never the
   designed-for-population column it must be. → make it structured (catalog id + rule id + text chunk id +
   citation), not a flat string array.
3. **ga_structural v2.0 reference reality** — refs live in `fact_value_jsonb.constituent_fact_ids`. The MSR
   `constituent_facts_array` column is where L2 STORES what it read. → keep the column; document the read path.
4. **Real embeddings, shared L0 vector space** — `bodha_signal_embeddings` exists; the model must be the
   Vertex model L0 uses (`text-multilingual-embedding-002`, 768-dim) so signals ↔ citations are comparable.
5. **The deep graph value-vector** — CGM edges need intrinsic-strength + valence + domains + directionality +
   varga-provenance as first-class columns (ga_structural already computed much of this per-varga).

**Cross-cutting columns added to EVERY bodha_* fact row (the consistency spine):**
- `fact_kind` TEXT — relationship | magnitude | position | time_window | birth_moment | configuration
- `source_l1_asset` TEXT — which of the 14 L1 assets the row projects (provenance + retrieval filter)
- `constituent_facts_array` TEXT[] — the L1 fact_ids it references (read from fact_value_jsonb.constituent_fact_ids)
- `classical_sources_jsonb` JSONB — {catalog_ids[], rule_ids[], text_chunk_ids[], citations[]} (the L0 bridge)
- `epistemic_tier` TEXT — two_pass_verified | documented_approximation (carried from L1)
- `signal_summary_text` TEXT — lossless deterministic NL summary (iterates ALL config keys)
- `*_formula_version` TEXT — every computed value stamps its versioned formula

## §2 — The L1 source inventory the schema must cover (grounded, the completeness baseline)
Maximum-completeness means MSR must project every category below. Grain in brackets.

- **ga_positions** — graha_position, graha_sign_attributes, graha_combustion_state, graha_retrogression_state,
  graha_speed_state, nakshatra/nakshatra_lord/nakshatra_pada [per-graha, ×ayanamsha].
- **ga_vargas** (~30 cats) — varga_position, varga_dignity, varga_house_lord/occupant, varga_aspect_matrix,
  varga_ashtakavarga, varga_vargottama_flag (+super/trans/trikona), varga_pushkara_bhaga/navamsa_flag,
  varga_deity/rishi_attribution, varga_d108/d150/d2700/d30/d27/d9 specials, varga_lal_kitab_special,
  varga_saptavargaja_bala_component, varga_vimsopaka_contribution, karaka_per_varga [per-graha×30 varga×ayanamsha].
- **ga_strength** — graha_shadbala_{sthana,dig,kala,cheshta,naisargika,drik,total} + per_varga variants,
  graha_ishta/kashta_phala, ashtakavarga_bindu(+per_varga), ashtakavarga_pinda_{bhinna,sarva,sodhita}(+per_varga),
  bhava_bala_{adhipati,dig,drishti,...}, graha_vimsopaka_{shadvarga,saptavarga,dasavarga,shodasavarga} [per-graha/house, per-varga, ×ayanamsha].
- **ga_sensitive** — arudha_pada, karaka_chara_position, karaka_rank/school, karakamsa_position, swamsa,
  kp_cuspal_significators, kp_ruling_planets_natal, saham_position, special_lagna, nakshatra_pada_sensitive,
  tajik_{aapamrityu,hadda_lord,triraashipathi,vargottama_specific} [per-point/cusp, D1+D9, ×ayanamsha].
- **ga_sade_sati** — sade_sati_cycle/phase/phase_quarter, _cancellation_check, _concurrent_dasha_overlay,
  _modifier_overlay, _saturn_retrograde_subset, _downstream_cross_reference [per-cycle/phase/time-window, ×ayanamsha].
- **ga_panchanga** — panchanga_{tithi,vara,yoga,karana,nakshatra_moon,agni_vasa,choghadiya_birth,hora_birth,
  disha_shul,panchaka_classification,solar_context,sun_moon_dynamics,special_yoga_combinations,*_shoonya_rashi} [birth-moment, ×ayanamsha].
- **ga_dashas** — dasha periods (Vimshottari + others), karaka_role_at_period, karakas_active_during_period,
  kp_sub_lord/sub_sub_lord/sublevel, shadbala_total-at-period [per-dasha-period, multi-system, ×ayanamsha].
- **ga_tajaka** — tajik_classical(+winner), aspects_lagna, house_from_natal/varsha_lagna [annual/varshaphal, ×ayanamsha].
- **ga_condition** — condition_score(+breakdown), graha_avastha_{baladi,deeptaadi,jagradadi,lajjitadi,sayanadi}_per_varga,
  combustion(+arc/penalty), graha_yuddha_result/with [per-graha, per-varga, ×ayanamsha].
- **ga_structural** (72 cats) — the full relational + graph-theoretic fabric (see GA_STRUCTURAL_REBUILD_VERIFY v2.1 §6).
- **ga_medical** — body_part, body_part_watch, disease_tendency, nakshatra_body_part [per-body-part/graha].
- **ga_vastu** — directional/vastu facts [per-direction] (confirm exact categories at brief time).
- **ga_prashna** — prashna, health_illness, tajik_yoga [per-query/horary].
- **ga_yoga** — yoga firings/labels (confirm exact categories at brief time).

**MSR design consequence:** the signal row is CATEGORY-AGNOSTIC — `signal_type_id` + `signal_type_class` +
`configuration_jsonb` + `fact_kind` + `source_l1_asset` represent ANY L1 category uniformly. No per-category
column proliferation; completeness via a uniform projection model, not 200 bespoke columns.

## §3 — Per-asset schema (the contract each brief builds to)

### bo_laksana — `bodha_msr_signals` (the root; category-agnostic projection of all 14 L1 assets)
KEEP from 226: identity, salience-decomposition columns, domain columns, the downstream hook-columns
(graph/resonance/digest hooks), MVs. ADD/CHANGE for completeness:
- `fact_kind`, `source_l1_asset`, `signal_summary_text` (lossless), `classical_sources_jsonb` (structured L0 bridge).
- `varga_id` TEXT + `varga_provenance_jsonb` — which varga the signal lives in / its weight came from.
- `cross_ayanamsha_consistency_score` NUMERIC — how many of 5 ayanamshas the signal holds in (intrinsic, deterministic).
- widen `signal_type_class` enum to cover all 14 assets' kinds (relationship/magnitude/position/time_window/birth_moment/configuration/medical/vastu/prashna/annual/dasha_period).
- `constituent_facts_array` populated by READING `fact_value_jsonb.constituent_fact_ids` from ga_structural (+ direct fact_ids for value-assets).
- 3 MVs refreshed (top_signals / recurring_patterns / domain_summary).

### bo_sangati — CDLM (`bodha_cdlm_cells` + rollups/summary/clusters/gradients + `bodha_convergence`)
KEEP the 9×9/27×27 + dynamic-snapshot structure. ADD: the cross-cutting spine columns; ensure
`bodha_convergence` carries `convergence_count` + cross-tradition + per-domain + `convergence_formula_version`;
domains derived from MSR `domains_affected_array` (now spanning all 14 assets' domains incl. medical/vastu).

### bo_bimba + bo_karanajala — CGM (`bodha_cgm_nodes`, `_edges`, `_sub_graphs`, `_motifs`, `_chart_topology_summary`, `bodha_cgm_paths`, `bodha_contradictions`)
KEEP the per-node centrality columns + per-edge structure. ADD the **full edge value-vector** as first-class
columns on `bodha_cgm_edges`: `intrinsic_strength`, `valence` (benefic/malefic/mixed), `affected_domains` TEXT[],
`directionality` (directed/mutual), `weight_varga_source`, `relationship_basis`. Node set = multi-entity
(grahas/houses/signs/nakshatras/special-points/configs) — `node_type` enum widened. ga_structural ALREADY
computed centrality/dispositor_tree/paths per-varga → CGM PROJECTS these (reference, don't recompute).
`bodha_contradictions` owned here; `bodha_cgm_paths` carries the significator/dispositor chains.

### bo_samskara — `bodha_signal_embeddings` (real Vertex embeddings)
CHANGE: `embedding_model` default → `text-multilingual-embedding-002` (NOT placeholder_hash); 768-dim;
`embedding_input` = MSR `signal_summary_text`; pin `embedding_model_version`. 1:1 with MSR signals.

### bo_upaya — RM (`bodha_rm_resonances` + remedy_prescriptions/dasha_windowed/dosha_bundles/pattern_remedies/chart_summary)
KEEP the 6-table structure. SEED FIX (apply with this brief): bo_upaya OWNS `bodha_rm_resonances` (primary)
+ summed count_sql across all 6. Every remedy row carries `classical_sources_jsonb` → brahma_remedy_corpus
(L0) citation (grounded, never invented). Resonance can now target medical body-parts too (ga_medical projected).

### bo_samvada — UCD (read-side: `vw_chart_digest` view + `query_ucd` tool; NO writer table)
SEED FIX: clear bo_samvada off `bodha_rm_resonances`; set to UCD/Option-A (view, no per-chart table).
The view joins the chart_summary rows across assets into one digest.

### bo_pramana_mapa — `synthesis_quality_scorecard` (global)
KEEP. ADD the standing Trap-1 audit columns (count of unresolved constituent_facts; per-asset projection
coverage: did all 14 L1 assets get projected?). Drop the `WHERE chart_id` (it's global).

## §4 — The retrieval contract (retrievability pillar, designed WITH the schema)
Every table above gets ≥1 `L2_bodha` retrieval tool (extend the registry, don't fork it). Every tool return
MUST carry: `epistemic_tier`, salience, `classical_sources_jsonb` (citations), `constituent_facts_array`
(provenance), `fact_kind`, `source_l1_asset`. Plus the cross-table tools: `query_chart_convergences`,
`query_chart_contradictions`, `query_chart_graph_paths`, `query_ucd` (deep digest). The coverage gate asserts
every bodha_* table + every L1 source-asset is reachable. This is the schema's retrieval half — designed now
so storage and retrieval are one contract, not two.

## §5 — Migration plan (empty tables → redefine freely)
Because the bodha_* tables are EMPTY: author a new migration set that DROPs + re-CREATEs the bodha_* tables
at the enriched schema (or ALTERs where additive). No data migration. Mig 226 tables that are unchanged stay;
changed ones are redefined. Each per-asset brief carries its table's final DDL. Verify max migration number on
prod first (handoff cites ~324). The `signal_type_registry` (G52) orphan from 226 is dropped (G52 eliminated).

## §6 — What each of the 8 briefs inherits from this contract
| brief | builds tables | key enriched columns it must populate |
|---|---|---|
| bo_laksana | bodha_msr_signals + 3 MVs | fact_kind, source_l1_asset, classical_sources_jsonb, signal_summary_text, varga_id, cross_ayanamsha — ALL 14 assets projected |
| bo_sangati | cdlm_* + bodha_convergence | convergence_count + formula_version; domains span 14 assets |
| bo_karanajala | cgm_edges/sub_graphs/motifs/topology/paths + contradictions | full edge value-vector (strength/valence/domains/directionality/varga-source) |
| bo_bimba | cgm_nodes | multi-entity node_type; centrality projected from ga_structural |
| bo_samskara | signal_embeddings | real Vertex model + version pinned |
| bo_upaya | 6 rm_* tables | classical_sources_jsonb → brahma_remedy_corpus; seed-fix ownership |
| bo_samvada | vw_chart_digest + query_ucd | seed-fix off rm_resonances; read-side only |
| bo_pramana_mapa | synthesis_quality_scorecard | Trap-1 audit + 14-asset projection-coverage |

---
*End of L2_BODHA_SCHEMA_REDESIGN v1.0. The holistic enriched contract: a category-agnostic MSR projecting ALL
14 L1 assets, a structured L0 classical bridge on every row, real Vertex embeddings in L0's vector space, the
full graph value-vector on CGM edges, the cross-cutting consistency spine (fact_kind / source_l1_asset /
constituent_facts / classical_sources / epistemic_tier / signal_summary_text / formula_version), and the
retrieval contract designed alongside storage. Tables redefined freely (empty). Each of the 8 per-asset briefs
builds to its slice. This is the thing the briefs depend on — settled once, here.*
