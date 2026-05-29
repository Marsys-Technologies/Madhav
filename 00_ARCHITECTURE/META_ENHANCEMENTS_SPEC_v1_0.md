---
artifact: META_ENHANCEMENTS_SPEC_v1_0.md
document: META-Enhancements — Synthesis Layer across A1-A16
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: lock all 5 META-enhancements; ensure retrieval-tool-ready schemas across the entire stack)
intended_for: Claude Code sub-agents implementing the META-layer writers + retrieval tools
prime_directive: Only computed facts. META-layer synthesizes across A1-A16 to surface patterns no single asset reveals. No narrative.
depends_on: ALL of A1-A16 (META consumes everything)
---

# META-Enhancements Specification

## §0 — Mission

Five synthesis-layer enhancements that leverage the entire A1-A16 stack to surface patterns invisible to any single asset and unmanageable by any single acharya:

- **META-α (Λ-LATTICE)** — Structural Timeline Lattice (single moment-in-time omniscient join)
- **META-β (Π-CATALOG)** — Pattern Catalog Unified (every named pattern, one query)
- **META-γ (Δ-LEDGER)** — Divergence Detector (cross-system disagreement audit trail)
- **META-δ (Ω-SPACE)** — Negative Space Map (absence-as-feature)
- **META-ε (Φ-TRAIL)** — Derivation Trail Index (claim → L1 facts DAG)

Each is small in storage but large in retrieval-leverage. Total per-chart cost: ~10K additional rows. Each is read-time-optimized.

## §1 — META-α — Λ-LATTICE — Structural Timeline Lattice

**Mission**: Single read for any moment in a native's life. One query → all active structural features at that moment.

**Storage**: Hybrid — materialized view for next-3-year window + on-demand compute for historical/future.

```sql
CREATE MATERIALIZED VIEW mv_chart_lattice_at_date AS
SELECT
  chart_id, ayanamsha_id, date_iso,
  -- A7 chart_dashas (3 systems, all active levels)
  json_build_object(
    'vimshottari', vim_lattice_jsonb,
    'chara_karaka', chara_lattice_jsonb,
    'yogini', yogini_lattice_jsonb
  ) AS active_dasha_jsonb,
  -- A11 CDLM dynamic snapshot at this date
  cdlm_dynamic_snapshot_jsonb,
  -- A12 CGM dynamic Maha snapshot
  cgm_dynamic_snapshot_jsonb,
  -- A13 RM active prescriptions
  active_prescriptions_jsonb,
  -- A15 active synchronicity window
  active_synchronicity_jsonb,
  -- A16 active predicted-event anchors
  active_anchors_jsonb,
  -- A8 transit-triggered yogas/doshas at this date
  active_transit_yogas_jsonb,
  -- A9 active Sade Sati phase
  active_sade_sati_jsonb,
  -- A4 panchanga of the moment
  panchanga_at_date_jsonb,
  -- Cross-asset summary
  total_active_pattern_count INT,
  resonance_class_at_date TEXT,
  high_priority_attention_flag BOOLEAN,
  -- Embeddings
  lattice_moment_embedding_vec VECTOR(768)
FROM chart_dashas_joined_with_all_dynamic_snapshots;

-- Indexes
CREATE INDEX lattice_chart_date_idx ON mv_chart_lattice_at_date (chart_id, ayanamsha_id, date_iso);
CREATE INDEX lattice_attention_idx ON mv_chart_lattice_at_date (chart_id, ayanamsha_id) WHERE high_priority_attention_flag = true;
CREATE INDEX lattice_embedding_hnsw ON mv_chart_lattice_at_date USING hnsw (lattice_moment_embedding_vec vector_cosine_ops);
```

Refresh: Cloud Scheduler daily for rolling next-3-year window. On-demand compute via `query_lattice_at_date(chart_id, date)` for arbitrary dates.

**Retrieval tools**:
- `query_lattice_at_date(chart_id, ayanamsha_id, date_iso, depth_class?)` → single lattice row
- `query_lattice_in_range(chart_id, ayanamsha_id, start_iso, end_iso, attention_only?)` → range
- `query_lattice_high_resonance_windows(chart_id, ayanamsha_id, top_k=10)` → top windows
- `query_lattice_peers(lattice_moment_embedding, top_k=10)` → cross-chart cohort moments

**Acharya-leverage**: "Tell me about July 2028" returns ONE row with EVERY active structural feature simultaneously. Acharya cannot mentally hold this join. LLM gets temporal omniscience.

## §2 — META-β — Π-CATALOG — Pattern Catalog Unified

**Mission**: Every named pattern across the stack in one queryable catalog. Cross-pattern linkage discovery.

```sql
CREATE TABLE l25_pattern_catalog (
  pattern_catalog_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,

  pattern_kind TEXT NOT NULL,                       -- enum: 'yoga' | 'dosha' | 'cdlm_pattern_cluster' | 'cgm_motif' | 'cgm_sub_graph' | 'magnification' | 'anti_magnification' | 'near_miss_yoga' | 'synchronicity' | 'phase_locked_anchor' | 'classical_archetype' | 'sade_sati_phase' | 'time_convergence_cluster' | 'spiritual_progress_marker' | 'karmic_signature_component' | 'negative_space'
  pattern_name TEXT NOT NULL,                       -- canonical name (e.g., 'gajakesari_yoga', 'kala_sarpa_axis')
  pattern_strength NUMERIC,                         -- normalized 0-1
  active_flag BOOLEAN NOT NULL,
  active_window_iso_array JSONB,                    -- when this pattern is active

  source_asset TEXT NOT NULL,                       -- 'A8' | 'A10' | 'A11' | 'A12' | 'A13' | 'A15' | 'A16' | etc.
  source_row_id UUID NOT NULL,                      -- back-reference to originating row

  classical_citation_array TEXT[],
  cross_pattern_links_array UUID[],                 -- linked patterns across kinds

  pattern_polarity TEXT,                            -- 'positive' | 'negative' | 'transformational' | 'neutral'
  pattern_domain_array TEXT[],                      -- which life domains it affects
  pattern_severity_class TEXT,                      -- 'foundational' | 'major' | 'moderate' | 'minor'

  -- Cross-pattern enrichment
  reinforced_by_pattern_ids_array UUID[],
  contradicted_by_pattern_ids_array UUID[],
  preconditions_pattern_ids_array UUID[],

  -- Channel rendering
  channel_render_priority_jsonb JSONB,

  -- pgvector
  pattern_embedding_vec VECTOR(768),

  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, pattern_kind, pattern_name, source_asset, source_row_id)
);

CREATE INDEX pattern_catalog_chart_idx ON l25_pattern_catalog (chart_id, ayanamsha_id);
CREATE INDEX pattern_catalog_active_idx ON l25_pattern_catalog (chart_id, ayanamsha_id) WHERE active_flag = true;
CREATE INDEX pattern_catalog_kind_idx ON l25_pattern_catalog (chart_id, ayanamsha_id, pattern_kind);
CREATE INDEX pattern_catalog_severity_idx ON l25_pattern_catalog (chart_id, ayanamsha_id, pattern_severity_class);
CREATE INDEX pattern_catalog_embedding_hnsw ON l25_pattern_catalog USING hnsw (pattern_embedding_vec vector_cosine_ops);
```

Volume: ~500-1,000 pattern rows per chart aggregated across all kinds.

**Retrieval tools**:
- `query_patterns(chart_id, ayanamsha_id, pattern_kind?, active_only?, severity?, domain?)` → patterns
- `query_pattern_links(pattern_catalog_id)` → reinforced + contradicted + precondition linkage walk
- `query_pattern_peers(pattern_embedding, top_k=10)` → cross-chart pattern cohort

**Acharya-leverage**: "What patterns are present in this chart at this date?" → ONE query returns yogas + doshas + motifs + clusters + magnifications + near-misses + synchronicities + anchors + archetypes + sade sati phases + spiritual markers + karmic components + negative spaces. Acharya tracks 3-5 of these mentally; the LLM gets all of them.

## §3 — META-γ — Δ-LEDGER — Divergence Detector

**Mission**: Explicit ledger of every place sub-systems disagree. Diagnostic uncertainty becomes auditable signal.

```sql
CREATE TABLE l25_divergence_ledger (
  divergence_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,

  divergence_kind TEXT NOT NULL,                    -- 'cross_tradition' | 'cross_ayanamsha' | 'cross_system_temporal' | 'cross_channel_magnification' | 'cross_rule_prediction'
  structural_point TEXT NOT NULL,                   -- the point at issue (e.g., 'SAT_in_7H', 'career_domain', '2028_career_period')
  divergence_severity_class TEXT NOT NULL,          -- 'critical' | 'significant' | 'moderate' | 'minor'

  source_systems_array TEXT[] NOT NULL,             -- which systems
  per_system_verdicts_jsonb JSONB NOT NULL,         -- {parashari: 'X', jaimini: 'Y', tajik: 'Z', kp: 'W'}
  divergence_magnitude_score NUMERIC,

  -- Resolution
  classical_resolution_methodology TEXT,            -- e.g., 'BPHS_priority_over_Phaladeepika_for_yoga_calls'
  classical_resolution_citation TEXT,
  resolved_verdict TEXT,                            -- the verdict to surface as primary
  surface_uncertainty_flag BOOLEAN,                 -- when LLM should reflect the uncertainty rather than pick one side

  affected_assets_array TEXT[],                     -- which downstream assets care about this divergence
  affected_pattern_ids_array UUID[],                -- which Π-CATALOG patterns this affects

  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX divergence_chart_idx ON l25_divergence_ledger (chart_id, ayanamsha_id);
CREATE INDEX divergence_severity_idx ON l25_divergence_ledger (chart_id, ayanamsha_id, divergence_severity_class);
CREATE INDEX divergence_surface_idx ON l25_divergence_ledger (chart_id, ayanamsha_id) WHERE surface_uncertainty_flag = true;
```

Volume: ~50-150 divergences per chart depending on actual cross-system conflicts.

**Retrieval tools**:
- `query_divergences(chart_id, ayanamsha_id, divergence_kind?, severity?, surface_only?)` → divergence rows
- `query_divergence_at_structural_point(chart_id, structural_point)` → divergences at this point

**Acharya-leverage**: When Parashari says raja yoga but Jaimini doesn't, that's structurally diagnostic. The LLM should reflect: "Parashari reading suggests recognition; Jaimini doesn't corroborate — uncertainty range here." Without Δ-LEDGER, this nuance is invisible.

## §4 — META-δ — Ω-SPACE — Negative Space Map

**Mission**: What's structurally ABSENT. Absence-as-feature is diagnostic.

```sql
CREATE TABLE l25_negative_space_map (
  negative_space_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,

  absence_class TEXT NOT NULL,                      -- 'house_empty' | 'no_exalted_graha' | 'no_vargottama' | 'no_yoga_karaka' | 'no_fired_raja_yoga' | 'no_dignity_anchor' | 'no_strong_kendra' | 'no_strong_trikona' | 'no_active_panchamahapurusha' | 'no_mutual_reception' | 'no_chara_karaka_in_kendra' | 'no_jupiter_aspect_on_lagna' | etc.
  absence_subject TEXT,                             -- if specific (e.g., 'HOUSE_7' for house_empty)

  expected_classical_frequency NUMERIC,             -- how often this absence appears classically in cohort
  rarity_score NUMERIC,                             -- this chart's deviation from expected
  diagnostic_implication_class TEXT,                -- structural implication of the absence
  classical_citation_array TEXT[],

  -- Linkage to active patterns that compensate
  compensating_pattern_ids_array UUID[],
  net_structural_implication_class TEXT,

  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX neg_space_chart_idx ON l25_negative_space_map (chart_id, ayanamsha_id);
CREATE INDEX neg_space_class_idx ON l25_negative_space_map (chart_id, ayanamsha_id, absence_class);
CREATE INDEX neg_space_rarity_idx ON l25_negative_space_map (chart_id, ayanamsha_id, rarity_score DESC);
```

Volume: ~50-100 absence-flags per chart.

**Retrieval tools**:
- `query_negative_space(chart_id, ayanamsha_id, absence_class?)` → absence rows
- `query_distinctive_absences(chart_id, ayanamsha_id, top_k=5)` → top-rarity absences

**Acharya-leverage**: "What's missing from this chart that's classically expected?" — surfaces the negative-space signature defining chart distinctiveness.

## §5 — META-ε — Φ-TRAIL — Derivation Trail Index

**Mission**: Every L2.5+ claim → explicit DAG showing L1 facts + derivation rules → final claim. Retrievable graph. Full work transparency.

```sql
CREATE TABLE l25_derivation_graph_nodes (
  graph_node_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,

  graph_node_kind TEXT NOT NULL,                    -- 'l1_fact' | 'l2_5_intermediate' | 'l2_5_claim' | 'derivation_rule' | 'corpus_citation'
  source_table TEXT,                                -- where this node's data lives
  source_row_id UUID,                               -- specific row
  short_label TEXT NOT NULL,                        -- human-readable label

  verification_pass_status TEXT NOT NULL, citation_ref TEXT, citation_human TEXT, computed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE l25_derivation_graph_edges (
  graph_edge_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  from_node_id UUID NOT NULL, to_node_id UUID NOT NULL,
  edge_kind TEXT NOT NULL,                          -- 'derives_via' | 'corroborates' | 'cited_in' | 'contradicts' | 'depends_on'
  derivation_rule_id TEXT,                          -- when edge represents a rule application
  edge_weight NUMERIC,                              -- contribution weight in derivation
  verification_pass_status TEXT NOT NULL, citation_ref TEXT, citation_human TEXT, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX deriv_nodes_chart_idx ON l25_derivation_graph_nodes (chart_id, ayanamsha_id);
CREATE INDEX deriv_nodes_source_idx ON l25_derivation_graph_nodes (source_table, source_row_id);
CREATE INDEX deriv_edges_chart_idx ON l25_derivation_graph_edges (chart_id, ayanamsha_id);
CREATE INDEX deriv_edges_from_idx ON l25_derivation_graph_edges (from_node_id);
CREATE INDEX deriv_edges_to_idx ON l25_derivation_graph_edges (to_node_id);
```

Volume: ~5,000-10,000 graph nodes + ~15,000-25,000 graph edges per chart depending on claim density.

**Retrieval tools**:
- `query_derivation_trail(claim_id)` → full DAG walking up to L1 facts
- `query_supporting_l1_facts(claim_id)` → set of L1 fact_ids that contribute
- `query_corpus_citations_for_claim(claim_id)` → classical citations
- `query_contributing_derivation_rules(claim_id)` → rule ids applied
- `query_claims_derived_from_l1_fact(l1_fact_id)` → which claims depend on this fact

**Acharya-leverage**: "Why do you say career stress in 2028?" → DAG retrieval shows: Saturn (FORENSIC fact_id 47) → Mars (fact_id 51) → opposition aspect (A8 derivation rule R12) → cell strength 0.78 (A11 row id X) → predicted_event 'career_strain' (A16 row id Y) with falsifiability statement. Full work, auditable, classical-citation-rich. Acharya-grade transparency.

## §6 — Cumulative impact

| META | Per-chart row cost | Storage class | Retrieval value |
|---|---|---|---|
| Λ-LATTICE | ~1,100 lattice rows for 3-year window + on-demand | MV + on-demand | Very high |
| Π-CATALOG | ~750 pattern rows | l25_pattern_catalog | Very high |
| Δ-LEDGER | ~100 divergences | l25_divergence_ledger | High |
| Ω-SPACE | ~75 absence-flags | l25_negative_space_map | High |
| Φ-TRAIL | ~7,500 nodes + ~20,000 edges | derivation graph | Very high |

**Total per chart: ~30K rows.** Still well within storage envelope.

## §7 — Cross-asset locks (cumulative)

| Asset | Lock | Status |
|---|---|---|
| A7 chart_dashas | Native PG range partitioning by period_start_iso | LOCKED in A12 §2.B |
| All ephemeris-derived facts | ephemeris_audit_jsonb (pyswisseph vs libephemeris JPL DE440 delta) | LOCKED in A12 §2.C |
| All graph compute | igraph C-core, no AGE | LOCKED in A12 §2.A |
| pgvector embeddings | 768-dim HNSW cosine | LOCKED in A12 §5 + A13 §4 + A15 + A16 + META |
| G27 corpus | exhaustiveness audit before A13-S1 | LOCKED in A13 §6 |
| G29 Classical Timing Rule Catalog | exhaustiveness audit before A16-S1 | LOCKED in A16 §3 |
| Channel render priority | pre-baked at write time on every primary asset | LOCKED across A10-A13, A15, A16, META-β |
| Retrieval-tool conformance | every asset has a registered retrieval contract (see RETRIEVAL_INTERFACE_REGISTER) | LOCKED here |

## §8 — Final locked surface

1. META-α LATTICE materialized view + on-demand compute fallback
2. META-β PATTERN CATALOG unified across all 16 pattern-kinds
3. META-γ DIVERGENCE LEDGER cross-system audit trail
4. META-δ NEGATIVE SPACE MAP absence-as-feature
5. META-ε DERIVATION TRAIL graph
6. ~30K additional rows per chart
7. 5 new retrieval-tool families exposed to MCP
8. Cross-asset pattern unification + epistemic-uncertainty surfacing + acharya-grade explainability

---

*End of META_ENHANCEMENTS_SPEC_v1_0.md — LOCKED 2026-05-29.*
