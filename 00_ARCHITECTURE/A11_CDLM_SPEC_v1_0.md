---
artifact: A11_CDLM_SPEC_v1_0.md
document: A11 — CDLM (Cross-Domain Linkage Matrix) Specification
status: LOCKED
version: 1.1
date: 2026-05-29
changelog:
  - v1.1 (2026-06-12, L2 Bodha §13.1 amendment): (a) Table prefix `l25_cdlm_*` → `bodha_cdlm_*`
    per the native naming decision (L2_BODHA_BUILD_CAMPAIGN §3.1); schemas otherwise unchanged.
    (b) ADDED first-class artifact `bodha_convergence` — convergence-density-per-domain (N
    independent MSR signals converging on one of the 9 domains = computed weight-of-evidence),
    governed by `convergence_formula_v1` (versioned pure function in bodha_writers/formulas.py).
    The §13.1 design-philosophy extension (native-APPROVED 2026-06-12); `bo_sangati` owns it. See §2.6.
    (c) Reads `bodha_contradictions` (owned by bo_karanajala) for contradiction-aware linkage.
    Tables already built by migration 226. — see §2.6.
  - v1.0 (2026-05-29): initial LOCKED spec, native sign-off.
authored_by: Cowork (native-confirmed: 3 dasha systems × Maha-Antar dynamic; everything included; storage redesigned for retrieval-optimal; wipe-existing)
intended_for: Claude Code sub-agents implementing the A11 CDLM writer to L2.5 layer
prime_directive: Only computed facts. Structural cross-domain linkage from MSR signal aggregation. Versioned linkage formula. No narrative.
depends_on: A10 MSR (heavy), A6 vargas, A8 T1 structural, A7 chart_dashas (Vimshottari + Chara + Yogini for dynamic snapshots), G19 karaka assignments, G27 remedies
window: 1950-01-01 → 2100-12-31 per A7 rule
---

# A11 — CDLM (Cross-Domain Linkage Matrix) Specification

## §0 — Mission

For each chart per ayanamsha, compute structural linkage between life domains via aggregation of A10 MSR signals tagged for those domains. Output static natal 9×9 (+ 27×27 sub-domain) + dynamic 9×9 snapshots per (Maha-lord, Antar-lord) combination across 3 dasha systems (Vimshottari + Chara + Yogini) + per-tradition CDLM views + chart-level summary + pattern clusters + evolution gradients. All deterministic. Two-pass verified. Storage architected for retrieval-optimal access patterns.

## §1 — Locked decisions

- Dasha system scope: **Vimshottari + Chara Karaka + Yogini** for Maha-Antar dynamic snapshots
- Sub-domain hierarchy: **9×9 + 27×27 at static natal only**; dynamic Maha-Antar at 9×9 only per native direction
- Per-tradition views: **YES** — Parashari + Jaimini + Tajik + KP separate matrices (static only)
- House-domain mapping per chart: **YES**
- Karaka-domain mapping per chart: **YES**
- Chart-typology classification: **YES**
- Top-K cell ranking depth: **Top 20** per Q7 final answer
- Cell-level remedy hooks: **YES**
- Pattern cluster detection: **YES**
- Linkage formula v1 weights: **CONFIRMED**
- All downstream enrichments (CGM/RM/UCN/M6/multi-channel): **INCLUDED**
- Architectural freedom: storage restructured for retrieval-optimal; **WIPE existing l25_cdlm rows**
- Two-pass verification: MANDATORY per row

## §1.1 — v1.1 amendment: naming + the convergence-density extension (§13.1)

**Naming (v1.1):** every `l25_cdlm_*` table name in this spec is read as `bodha_cdlm_*` (the native
naming decision; schemas unchanged). Migration 226 created them under the `bodha_` prefix.

**`bodha_convergence` (new first-class artifact, §13.1):** beyond the pairwise cells in
`bodha_cdlm_cells`, CDLM now computes, per (chart, ayanamsha, domain, snapshot), the
**convergence density** — the count and weighted strength of independent MSR signals pointing at
that domain (the "weight of evidence" move). This is a deterministic aggregation over
`bodha_msr_signals.domains_affected_array` / `domain_salience_jsonb`, governed by
**`convergence_formula_v1`** (`bodha_writers/formulas.py`, pure + unit-tested). One row per
(chart, ayanamsha, domain, snapshot_type). It is a COLUMN-bearing artifact, not a gate — no
threshold drop. Owned by the `bo_sangati` writer. Schema built by migration 226; documented at §2.6.

**`bodha_contradictions` (read dependency):** CDLM reads contradiction-pairs (owned by
`bo_karanajala`, A12 §13.1) to flag contradiction-aware linkage; it does not write that table.

## §2 — Storage architecture (5 core tables + `bodha_convergence` + 5 MVs)

> v1.1: table names below are `bodha_cdlm_*` (was `l25_cdlm_*`). Schemas unchanged from v1.0.

### Table 1 — `l25_cdlm_cells` (main fact table; all cells across all dimensions)

```sql
CREATE TABLE l25_cdlm_cells (
  cell_id                       UUID PRIMARY KEY,
  chart_id                      UUID NOT NULL,
  ayanamsha_id                  TEXT NOT NULL,
  build_id                      UUID NOT NULL,

  -- Snapshot dimensions (the cube)
  snapshot_type                 TEXT NOT NULL,    -- 'static_natal_9x9' | 'static_natal_27x27' | 'static_tradition_<id>' | 'dynamic_maha_antar'
  dynamic_system_id             TEXT,             -- 'vimshottari' | 'chara_karaka' | 'yogini' (NULL for static)
  dynamic_maha_lord             TEXT,             -- (NULL for static)
  dynamic_antar_lord            TEXT,             -- (NULL for static)
  dynamic_window_start_iso      TIMESTAMPTZ,
  dynamic_window_end_iso        TIMESTAMPTZ,
  tradition_view_id             TEXT,             -- 'parashari' | 'jaimini' | 'tajik' | 'kp' (NULL for combined)

  -- Cell identity
  domain_row                    TEXT NOT NULL,
  domain_col                    TEXT NOT NULL,
  subdomain_row                 TEXT,             -- only set when snapshot_type='static_natal_27x27'
  subdomain_col                 TEXT,

  -- Counts
  shared_signal_count           INT NOT NULL,
  shared_factor_count           INT NOT NULL,
  unique_signals_row_domain     INT NOT NULL,
  unique_signals_col_domain     INT NOT NULL,

  -- Linkage strength (formula v1.0)
  shared_signal_salience_sum    NUMERIC NOT NULL,
  shared_signal_max_salience    NUMERIC,
  positive_contribution         NUMERIC NOT NULL,
  negative_contribution         NUMERIC NOT NULL,
  net_linkage_strength          NUMERIC NOT NULL,
  computed_linkage_strength     NUMERIC NOT NULL,
  linkage_formula_version       TEXT NOT NULL,

  -- Contradiction tracking
  contradicting_signal_pairs_count INT NOT NULL,
  contradicting_signal_pairs_jsonb JSONB,
  cross_domain_contradiction_flag  BOOLEAN NOT NULL,

  -- Shared factor details
  shared_factor_keys_jsonb      JSONB,
  shared_signal_ids_array       UUID[],
  shared_signals_by_tradition_jsonb JSONB,
  shared_signals_high_convergence_count INT,
  recurring_pattern_markers_array TEXT[],

  -- Cross-ayanamsha stability
  cross_ayanamsha_cell_stability_score NUMERIC,

  -- Cell ranking
  top_k_rank_in_snapshot        INT,

  -- Asymmetry
  asymmetric_linkage_flag       BOOLEAN NOT NULL,
  asymmetry_score               NUMERIC,

  -- Downstream enrichment for A12 CGM
  cgm_subgraph_cluster_id       TEXT,
  cgm_bridge_edge_seeds_jsonb   JSONB,
  cgm_domain_super_node_strength_contribution_jsonb JSONB,
  cgm_antagonist_edge_seeds_jsonb JSONB,

  -- Downstream enrichment for A13 RM
  cell_remedy_priority_rank     INT,
  weakest_constituent_graha_jsonb JSONB,
  pattern_remedy_theme_jsonb    JSONB,
  cell_remedy_hooks_array       TEXT[],

  -- Downstream enrichment for A14 UCN
  dominant_linkage_rank_in_chart INT,
  domain_relationship_class     TEXT,             -- 'mutually_reinforcing' | 'one_drives_other' | 'oppositional' | 'parallel_independent'
  narrative_thread_seed         JSONB,

  -- Downstream enrichment for M6 prospective
  predicted_activation_dasha_windows_jsonb JSONB,
  cell_evolution_gradient_score NUMERIC,

  -- Multi-channel retrieval
  channel_render_priority_jsonb JSONB,

  -- Phase-aligned pattern detection
  phase_aligned_pattern_marker  TEXT,

  -- Provenance
  msr_salience_version_used     TEXT NOT NULL,
  verification_pass_status      TEXT NOT NULL,
  citation_ref                  TEXT NOT NULL,
  citation_human                TEXT NOT NULL,
  computed_at                   TIMESTAMPTZ NOT NULL,
  engine_version                TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id, domain_row, domain_col, subdomain_row, subdomain_col)
);

CREATE INDEX cdlm_chart_aya_idx ON l25_cdlm_cells (chart_id, ayanamsha_id);
CREATE INDEX cdlm_snapshot_type_idx ON l25_cdlm_cells (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cdlm_dynamic_lookup_idx ON l25_cdlm_cells (chart_id, ayanamsha_id, dynamic_system_id, dynamic_window_start_iso, dynamic_window_end_iso);
CREATE INDEX cdlm_tradition_idx ON l25_cdlm_cells (chart_id, ayanamsha_id, tradition_view_id) WHERE tradition_view_id IS NOT NULL;
CREATE INDEX cdlm_top_rank_idx ON l25_cdlm_cells (chart_id, ayanamsha_id, snapshot_type, top_k_rank_in_snapshot);
CREATE INDEX cdlm_dominant_chart_rank_idx ON l25_cdlm_cells (chart_id, ayanamsha_id, dominant_linkage_rank_in_chart);
CREATE INDEX cdlm_pattern_markers_gin_idx ON l25_cdlm_cells USING gin (recurring_pattern_markers_array);
CREATE INDEX cdlm_remedy_hooks_gin_idx ON l25_cdlm_cells USING gin (cell_remedy_hooks_array);
CREATE INDEX cdlm_contradiction_idx ON l25_cdlm_cells (chart_id, ayanamsha_id) WHERE cross_domain_contradiction_flag = true;
```

### Table 2 — `l25_cdlm_domain_rollups` (per-domain aggregations)

```sql
CREATE TABLE l25_cdlm_domain_rollups (
  rollup_id, chart_id, ayanamsha_id, build_id,
  snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  domain                        TEXT NOT NULL,
  total_inbound_linkage         NUMERIC NOT NULL,
  total_outbound_linkage        NUMERIC NOT NULL,
  diagonal_density              NUMERIC NOT NULL,
  signal_count_for_domain       INT NOT NULL,
  top_3_linked_domains_jsonb    JSONB,
  contradiction_density         NUMERIC,
  pattern_markers_for_domain_array TEXT[],
  verification_pass_status      TEXT NOT NULL,
  citation_ref                  TEXT NOT NULL,
  citation_human                TEXT NOT NULL,
  computed_at                   TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id, domain)
);
```

### Table 3 — `l25_cdlm_chart_summary` (per-chart-per-snapshot meta)

```sql
CREATE TABLE l25_cdlm_chart_summary (
  summary_id, chart_id, ayanamsha_id, build_id,
  snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  chart_typology_class          TEXT,                  -- 'career_dominant' | 'spirituality_focused' | 'relationship_centric' | 'balanced' | 'fragmented' | etc.
  pattern_cluster_markers_jsonb JSONB,
  total_chart_linkage           NUMERIC,
  contradiction_density         NUMERIC,
  house_to_domain_strength_jsonb JSONB,                -- per chart: house × domain strength
  karaka_to_domain_strength_jsonb JSONB,               -- per chart: karaka × domain strength
  dominant_3_domains_array      TEXT[],
  weakest_3_domains_array       TEXT[],
  bridge_link_count             INT,
  asymmetric_link_count         INT,
  verification_pass_status      TEXT NOT NULL,
  citation_ref                  TEXT NOT NULL,
  citation_human                TEXT NOT NULL,
  computed_at                   TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id)
);
```

### Table 4 — `l25_cdlm_pattern_clusters` (first-class detected patterns)

```sql
CREATE TABLE l25_cdlm_pattern_clusters (
  pattern_id, chart_id, ayanamsha_id, build_id,
  snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  pattern_marker_type           TEXT NOT NULL,         -- 'three_domain_cluster' | 'hub_spoke' | 'opposition_diad' | 'reinforcing_triad' | etc.
  involved_domains_array        TEXT[] NOT NULL,
  cluster_strength_total        NUMERIC NOT NULL,
  involved_cells_array          UUID[] NOT NULL,       -- references to l25_cdlm_cells
  involved_signals_array        UUID[] NOT NULL,       -- references to l25_msr_signals
  contradicts_other_patterns_array UUID[],
  remedy_theme_jsonb            JSONB,
  cgm_subgraph_cluster_seed     JSONB,                 -- pre-shaped for A12 CGM consumption
  classical_archetype_match     TEXT,                  -- if pattern matches a classical archetype (e.g., 'kala_sarpa_dosha_career_axis')
  predicted_outcome_class       TEXT,
  active_dasha_windows_jsonb    JSONB,
  verification_pass_status      TEXT NOT NULL,
  citation_ref                  TEXT NOT NULL,
  citation_human                TEXT NOT NULL,
  computed_at                   TIMESTAMPTZ NOT NULL
);
```

### Table 5 — `l25_cdlm_evolution_gradients` (time-series for dynamic cells)

```sql
CREATE TABLE l25_cdlm_evolution_gradients (
  gradient_id, chart_id, ayanamsha_id, build_id,
  dynamic_system_id, tradition_view_id,
  domain_row, domain_col,
  evolution_class               TEXT,                  -- 'steepening' | 'weakening' | 'stable' | 'oscillating'
  gradient_score                NUMERIC,
  trend_iso_window_array        JSONB,                 -- (start_iso, end_iso, linkage_at_window) tuples
  peak_period_lord              TEXT,
  peak_period_iso               TIMESTAMPTZ,
  trough_period_iso             TIMESTAMPTZ,
  predicted_next_peak_iso       TIMESTAMPTZ,
  verification_pass_status      TEXT NOT NULL,
  citation_ref                  TEXT NOT NULL,
  citation_human                TEXT NOT NULL,
  computed_at                   TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, dynamic_system_id, tradition_view_id, domain_row, domain_col)
);
```

## §3 — Linkage formula v1.0 (versioned)

```python
def linkage_formula_v1(cell):
    positive = sum(s.salience for s in cell.shared_signals if not s.in_contradiction)
    negative = sum(s.salience for s in cell.contradicting_pairs) * 0.5
    net = positive - negative

    high_convergence_bonus = (cell.high_convergence_count / max(cell.shared_signal_count, 1)) * 0.3
    factor_density_bonus   = math.log(1 + cell.shared_factor_count) * 0.1
    stability_factor       = cell.cross_ayanamsha_stability_score

    computed_linkage = net * (1 + factor_density_bonus) * (1 + high_convergence_bonus) * stability_factor
    return computed_linkage
```

Unit-tested with known fixture inputs.

## §4 — Materialized views (5)

All natal-fixed per snapshot (dynamic snapshots are pre-computed at build time per (Maha, Antar) — NOT parametric on query_date):

1. **`mv_cdlm_static_summary`** — joins l25_cdlm_cells (static_natal_9x9) + rollups + chart_summary for one wide row per (chart, ayanamsha) static query
2. **`mv_cdlm_top_K_links_per_chart`** — top-20 cells across all snapshots per (chart, ayanamsha) ranked by dominant_linkage_rank_in_chart
3. **`mv_cdlm_per_tradition_summary`** — pivots tradition_view_id into wide columns per (chart, ayanamsha, domain_row, domain_col)
4. **`mv_cdlm_dasha_window_lookup`** — fast lookup: given (chart, ayanamsha, system, date) → which Maha-Antar window applies + that snapshot's cells
5. **`mv_cdlm_pattern_summary`** — pattern_clusters per chart with cluster_strength_total + involved_domains + remedy_theme

All refresh synchronously at build close.

## §5 — Volume projection per chart (3 systems × Maha-Antar)

| Component | Rows per chart |
|---|---|
| Static natal 9×9 cells (× 5 ay) | 405 |
| Static natal 27×27 sub-domain cells (× 5 ay) | 3,645 |
| Per-tradition static views (4 tradtions × 81 cells × 5 ay) | 1,620 |
| Dynamic Maha-Antar — Vimshottari (~80 combos × 81 × 5 ay) | 32,400 |
| Dynamic Maha-Antar — Chara Karaka (~120 combos × 81 × 5 ay) | 48,600 |
| Dynamic Maha-Antar — Yogini (~250 combos × 81 × 5 ay) | 101,250 |
| Domain rollups per snapshot (~9 domains × snapshots × 5 ay) | ~20,500 |
| Chart summaries per snapshot | ~2,300 |
| Pattern clusters (~5-15 per chart × snapshots × 5 ay) | ~1,500 |
| Evolution gradients per dynamic cell-pair (81 × 3 systems × 5 ay) | 1,215 |

**Total A11 per chart: ~213,400 rows.**
**For 100 charts: ~21.3M rows.** Well within Postgres single-table comfort.

## §6 — Verification

`verification_pass_status` mandatory `two_pass_verified`:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Cell counts (shared_signal_count, etc.) | Engine SQL aggregation over l25_msr_signals | Independent count from MSR snapshot | Algebraic invariants (totals match per-chart MSR counts) |
| Linkage formula v1 application | Engine formula | Unit-test fixtures | Reproducibility check |
| Contradiction detection | MSR contradicts_signals_array scan | Independent contradiction graph traversal | — |
| Pattern cluster detection | Threshold + topology rule application | Independent graph-cluster algorithm cross-check | — |
| Cross-ayanamsha stability | 5-ayanamsha cell-strength variance | Independent calculation | — |
| Evolution gradient classification | Time-series slope analysis | Statistical regression cross-check | — |

Halt on divergent_flagged.

## §7 — Tool retrieval contract

- `query_cdlm_static_natal(chart_id, ayanamsha_ids[], scope='9x9'|'27x27'|'tradition_<id>')` → cells
- `query_cdlm_dynamic_at_date(chart_id, ayanamsha_id, date)` → 3 snapshot views (one per system) for that date's current Maha-Antar
- `query_cdlm_dynamic_window(chart_id, ayanamsha_id, system_id, maha_lord?, antar_lord?)` → cells for specific window
- `query_cdlm_top_links(chart_id, ayanamsha_id, top_k=20)` → ranked cells
- `query_cdlm_cell(chart_id, ayanamsha_id, snapshot_type, domain_row, domain_col)` → 1 row
- `query_cdlm_domain_rollup(chart_id, ayanamsha_id, snapshot_type, domain)` → rollup row
- `query_cdlm_chart_summary(chart_id, ayanamsha_id, snapshot_type)` → summary row
- `query_cdlm_pattern_clusters(chart_id, ayanamsha_id, pattern_type?)` → clusters
- `query_cdlm_evolution_gradients(chart_id, ayanamsha_id, system_id, domain_pair?)` → gradient rows

## §8 — Implementation notes

1. **WIPE existing l25_cdlm_cells rows** before A11 writer runs (per native directive). Fresh-rebuild discipline.
2. Cell computation pass order: MSR signals fully written → static_natal_9x9 → static_natal_27x27 → static_tradition_views → dynamic Maha-Antar per 3 systems → rollups → chart_summary → pattern clusters → evolution gradients
3. Pattern cluster detection algorithm: scan cells for (a) ≥3 domains with mutual linkage > threshold (default 0.6) → reinforcing triad; (b) one domain linked to ≥4 others → hub-spoke; (c) two domains with high contradiction_density → opposition diad
4. Asymmetric linkage detection: compute row→col and col→row linkages separately (they differ when domain_salience weighting differs between row and col domains for shared signals); flag asymmetry_score > 0.15
5. Per-tradition CDLM views: filter MSR signals by signal_tradition; recompute cells using only those signals
6. Evolution gradient computation: for each dynamic cell pair, fit linear regression across consecutive Maha-Antar snapshot strengths
7. Two-pass verification: per-cell algebraic invariants (counts match), per-table cross-validation (rollups sum to expected)

## §9 — Downstream enrichment delivery (the load-bearing piece)

### For A12 CGM:
- `cgm_subgraph_cluster_id` → CGM clusters cells by this ID
- `cgm_bridge_edge_seeds_jsonb` → CGM materializes bridge edges directly
- `cgm_domain_super_node_strength_contribution_jsonb` → CGM accumulates per-domain super-node weights
- `cgm_antagonist_edge_seeds_jsonb` → CGM antagonist edges
- Pattern clusters → CGM hub-detection input

### For A13 RM:
- `cell_remedy_priority_rank` → RM targeting order
- `weakest_constituent_graha_jsonb` → RM primary remedy candidate
- `pattern_remedy_theme_jsonb` → RM theme aggregation
- `cell_remedy_hooks_array` → G27 remedy_ids per cell

### For A14 UCN:
- `dominant_linkage_rank_in_chart` → UCN top-K selection
- `domain_relationship_class` → UCN deterministic categorical
- `narrative_thread_seed` → UCN structural argument seed
- `chart_typology_class` → UCN summary

### For M6 prospective:
- `predicted_activation_dasha_windows_jsonb` → calibration anchors
- `cell_evolution_gradient_score` → predictive signal

### For multi-channel retrieval:
- `channel_render_priority_jsonb` → per-channel prominence

## §10 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Career-Wealth static linkage (Lahiri) | `l25_cdlm_cells.static_natal_9x9.career-wealth@chart=...:ay=lahiri:linkage=0.78` | "Career-Wealth domain linkage: 0.78 (12 shared signals; 3 contradictions; Lahiri)." |
| Dynamic Vimshottari Saturn-Sun Maha-Antar | `l25_cdlm_cells.dynamic_maha_antar.vimshottari.SAT-SUN.career-relationships@...:ay=lahiri:linkage=0.65` | "During Vimshottari Saturn-Sun Maha-Antar (2014-2017): Career-Relationships linkage 0.65 (Lahiri)." |
| Pattern cluster | `l25_cdlm_pattern_clusters.three_domain_cluster.<id>@...:ay=lahiri:strength=2.34` | "Three-domain reinforcing cluster: career + wealth + learning; strength 2.34; remedy theme: discipline-focused (Lahiri)." |

## §11 — Locked decisions (final committed surface)

1. 5-table storage architecture (cells + rollups + chart_summary + pattern_clusters + evolution_gradients)
2. 3 dasha systems × Maha-Antar dynamic (Vimshottari + Chara + Yogini)
3. Sub-domain 27×27 at static natal only
4. Per-tradition views (4 traditions) at static only
5. House-domain + karaka-domain mappings per chart
6. Chart-typology classification (deterministic)
7. Top 20 cell ranking per snapshot
8. Pattern cluster detection (first-class table)
9. Evolution gradients table for dynamic time-series
10. All downstream enrichments (CGM/RM/UCN/M6/multi-channel)
11. Linkage formula v1 versioned + unit-tested
12. 5 materialized views for hot retrieval paths
13. ~213K rows per chart × 100 charts = ~21M total — comfortable
14. Two-pass verification mandatory per row
15. WIPE existing l25_cdlm rows before rebuild

---

*End of A11_CDLM_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
