---
artifact: A12_CGM_SPEC_v1_0.md
document: A12 — CGM (Chart Graph Model) Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: Option E technology realignment; all 10 A12 clarifications = YES; 3 execution adjustments locked)
intended_for: Claude Code sub-agents implementing the A12 CGM writer to L2.5 layer
prime_directive: Only computed facts. Structural graph of the chart as nodes + typed/weighted edges. Pre-materialized at build time via igraph in-memory compute. No runtime graph engine. No narrative.
depends_on: A8 T1 structural (heavy), A10 MSR (heavy), A11 CDLM (heavy — domain super-nodes + bridge_edge_seeds + antagonist_edge_seeds + pattern_clusters), A6 vargas (D9/D10/D60 + key vargas as nodes), A5 sensitive points (sahams + arudhas + midpoints as nodes), A7 chart_dashas (Vimshottari Maha lord level × 3 systems for dynamic snapshots), G19 karaka assignments
window: 1950-01-01 → 2100-12-31 per A7 rule
technology_stack: Cloud SQL Postgres (or AlloyDB) + pgvector + native declarative partitioning + igraph (Python C-core build-time compute) + libephemeris JPL DE440 dual-source ephemeris audit + BigQuery cold-data export. No Apache AGE. No TimescaleDB.
---

# A12 — CGM (Chart Graph Model) Specification

## §0 — Mission

For each chart per ayanamsha, build a structural graph: nodes = meaningful entities (grahas, houses, signs, sensitive points, configurations, vargas, domains, dasha lords, pattern clusters), edges = classical structural relationships (24 edge types), weights = composite strengths from A8 + A10 MSR salience aggregation. Pre-compute all graph-theoretic metrics (centrality, PageRank, motif detection, sub-graph extraction) **at write time using igraph in-memory compute**. Materialize all retrieval-required sub-graphs into Postgres tables. No runtime graph traversal engine — graph integrity is the Python writer's responsibility, not the database's.

## §1 — Locked decisions (all 10 clarifications = YES + Option E technology realignment)

### A12 clarification answers:
1. **Snapshot scope**: Static natal + Maha-lord level × 3 systems (Vimshottari + Chara Karaka + Yogini). NOT Maha-Antar — graph topology changes at Maha-lord boundary, activation lighting is captured by A11 CDLM dynamic cells + chart_dashas.
2. **Edge bundling**: Separate edges per type. Sun-Mars conjunction ≠ Sun-Mars aspect classically.
3. **Per-tradition CGM views**: All 4 (Parashari + Jaimini + Tajik + KP).
4. **Sub-graph extraction**: Full set (per-domain + per-tradition + karaka_network + saham_network + midpoint_network + cluster + ego_network + sade_sati_active).
5. **Classical motif detection**: ~30-50 motif library pre-defined.
6. **Per-graha story arc**: Materialized.
7. **GraphML/GEXF export hooks**: YES.
8. **Subgraph fingerprinting**: YES (hash columns on motifs + topology summary).
9. **Conflict resolution edges**: YES.
10. **Wipe existing l25_cgm_*** rows before A12 writer runs.

### Option E technology stack locks:
- **Storage**: Cloud SQL Postgres / AlloyDB (managed) as SoR. NO Apache AGE.
- **Vector**: pgvector embeddings on chart topology summary + key nodes (replaces AGE vector-search ambitions).
- **Time-series cross-asset**: Native PostgreSQL declarative range partitioning on `chart_dashas` by `period_start_iso` (NOT TimescaleDB). Documented here because it is a load-bearing prerequisite for CGM's dasha_lord_link edges + per-graha story arcs.
- **Graph compute**: igraph (Python C-core) at write time. Two-pass verified vs NetworkX as secondary algorithm.
- **Ephemeris audit**: `ephemeris_audit_jsonb` column on root fact tables, populated with libephemeris JPL DE440 delta against pyswisseph semi-analytical.
- **Research analytics**: BigQuery cold-data export as read replica for cross-chart cohort OLAP. NOT in CGM SoR write path; orthogonal layer.

## §2 — Technology execution adjustments (3 native-mandated locks)

### A. In-Memory Graph Compiler (igraph)

Because the database has no active graph execution layer, the Python writer engine is **strictly responsible** for graph integrity.

- igraph constructs the graph entirely in-memory at write time using its C-core (benchmarked ~10× faster than NetworkX on PageRank/centrality at our graph size).
- All graph-theoretic indices computed at write time and written as **flat columns** on `l25_cgm_nodes`:
  - `degree_in`, `degree_out`
  - `betweenness_centrality`
  - `eigenvector_centrality`
  - `pagerank_score`
  - `clustering_coefficient`
  - `closeness_centrality`
  - `harmonic_centrality`
  - `core_number` (k-core decomposition)
- All graph-theoretic indices computed on per-edge contribution and written as flat columns on `l25_cgm_edges`:
  - `edge_betweenness`
  - `in_shortest_path_count`
- Canonical sub-graphs, classical motifs, ego-networks materialized as serialized pointer arrays in `l25_cgm_sub_graphs` (`node_ids_array UUID[]`, `edge_ids_array UUID[]`) and `l25_cgm_motifs` (`involved_node_ids_array`, `involved_edge_ids_array`).
- **No runtime multi-hop graph walks required.** Retrieval queries hit pre-materialized rows.
- For edge cases requiring ad-hoc multi-hop walks (research only), SQL recursive CTE on `l25_cgm_edges` is the fallback — acceptable at our row count (<100K edges per (chart, ay)).

### B. Native PostgreSQL Range Partitioning (chart_dashas)

`chart_dashas` (cross-asset prerequisite for CGM dasha_lord nodes + per-graha story arcs):

```sql
CREATE TABLE chart_dashas (...) PARTITION BY RANGE (period_start_iso);
CREATE TABLE chart_dashas_y1950_y2000 PARTITION OF chart_dashas FOR VALUES FROM ('1950-01-01') TO ('2000-01-01');
CREATE TABLE chart_dashas_y2000_y2050 PARTITION OF chart_dashas FOR VALUES FROM ('2000-01-01') TO ('2050-01-01');
CREATE TABLE chart_dashas_y2050_y2100 PARTITION OF chart_dashas FOR VALUES FROM ('2050-01-01') TO ('2100-01-01');
```

Window queries from CGM dynamic Maha-lord snapshots execute with immediate partition pruning. Mitigates index bloat. Cross-asset implication: A7 spec amendment may be needed to reflect this — flag at A12 implementation kickoff.

### C. Dual-Source Ephemeris Audit Tracking (`ephemeris_audit_jsonb`)

Append `ephemeris_audit_jsonb` column to root fact tables (chart_facts, l25_cgm_nodes where position_in_chart_jsonb derives from ephemeris). Logs absolute positional delta between pyswisseph semi-analytical and libephemeris JPL DE440 coordinates.

```json
{
  "primary_source": "pyswisseph_semi_analytical",
  "primary_source_version": "2.10.03",
  "secondary_source": "libephemeris_jpl_de440",
  "secondary_source_version": "1.0.0",
  "longitude_delta_arcsec": 0.073,
  "latitude_delta_arcsec": 0.012,
  "distance_delta_au": 1.4e-9,
  "audit_passed_flag": true,
  "audit_threshold_arcsec": 3.0,
  "audit_timestamp_iso": "2026-05-29T..."
}
```

`audit_passed_flag = false` triggers halt on divergent_flagged.

## §3 — Node types (10 classes; ~200-300 nodes per (chart, ayanamsha))

| Class | Subject examples | Approx count per snapshot |
|---|---|---|
| `graha` | SUN, MOON, MAR..ERI (23 bodies) | 23 |
| `house` | HOUSE_1..HOUSE_12 | 12 |
| `sign` | ARI..PIS | 12 |
| `lagna` | LAGNA | 1 |
| `special_point` | Upagrahas (6) + Saturn-derived (5) + esoteric bindus (~10) + Sahams (70+) + Arudhas (19) + Karakas (8) + Midpoints (54) | ~170 |
| `configuration` | YOGA_HAMSA, DOSHA_MANGAL, PARIVARTANA_SUN_MOON — one node per fired MSR signal | ~50-100 |
| `varga_node` | D9_NAVAMSA, D10_DASAMSA, D60_SHASHTIAMSA + Parashari 16 | 16 |
| `domain` | CAREER, RELATIONSHIPS, ..., CHARACTER (9 meta-nodes from CDLM) | 9 |
| `dasha_lord` | Current Vim/Chara/Yogini lords (3 per snapshot) | 3 |
| `pattern_cluster` | references to A11 CDLM pattern_clusters | ~5-15 |

## §4 — Edge types (24 classes; ~500-1500 edges per snapshot)

`aspect_parashari`, `aspect_jaimini`, `aspect_tajik`, `dispositor`, `lordship`, `karaka_link` (natural), `karaka_chara_link` (Jaimini), `conjunction`, `parivartana`, `mutual_reception`, `configuration_constituent`, `domain_membership` (weighted by CDLM domain_salience), `bridge_edge` (from CDLM cgm_bridge_edge_seeds), `antagonist_edge` (from CDLM cgm_antagonist_edge_seeds), `pattern_cluster_membership`, `varga_dignity`, `karakamsa_link`, `swamsa_link`, `argala_edge` (Jaimini), `virodha_argala_edge`, `saham_link`, `midpoint_link`, `dasha_lord_link` (temporal), `conflict_resolution_edge` (new — connects contradicting signals to net-effect resolution path).

## §5 — Storage architecture (5 tables)

### Table 1 — `l25_cgm_nodes`

```sql
CREATE TABLE l25_cgm_nodes (
  node_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,

  -- Snapshot dimensions
  snapshot_type TEXT NOT NULL,                     -- 'static_natal' | 'dynamic_maha_vimshottari_<lord>' | 'dynamic_maha_chara_<lord>' | 'dynamic_maha_yogini_<lord>' | 'tradition_parashari' | 'tradition_jaimini' | 'tradition_tajik' | 'tradition_kp' | 'sade_sati_active_<phase>'

  -- Identity
  node_type TEXT NOT NULL,
  node_subject TEXT NOT NULL,
  node_label_human TEXT NOT NULL,

  -- Position + properties
  position_in_chart_jsonb JSONB,
  strength_score NUMERIC,
  dignity_state TEXT,

  -- Graph-theoretic indices (flat columns, igraph-computed at write time)
  degree_in INT NOT NULL, degree_out INT NOT NULL,
  betweenness_centrality NUMERIC,
  eigenvector_centrality NUMERIC,
  pagerank_score NUMERIC,
  clustering_coefficient NUMERIC,
  closeness_centrality NUMERIC,
  harmonic_centrality NUMERIC,
  core_number INT,

  -- Domain + cluster
  primary_domain TEXT,
  domain_affiliations_jsonb JSONB,
  cluster_membership_array TEXT[],
  cgm_subgraph_cluster_id TEXT,                    -- from CDLM enrichment

  -- Configuration specifics
  msr_signal_id UUID, configuration_constituents_array UUID[],
  configuration_lifecycle_state TEXT,

  -- Hub identification
  hub_flag BOOLEAN NOT NULL,
  hub_score NUMERIC,
  hub_edge_types_array TEXT[],

  -- Tradition presence
  present_in_traditions_array TEXT[],

  -- Cross-ayanamsha stability
  cross_ayanamsha_presence_score NUMERIC,

  -- pgvector embedding (for cross-chart cohort discovery)
  node_embedding_vec VECTOR(768),

  -- Dual-source ephemeris audit
  ephemeris_audit_jsonb JSONB,                     -- pyswisseph vs libephemeris JPL DE440 delta

  -- Provenance
  msr_salience_version_used TEXT,
  cdlm_version_used TEXT,
  graph_compute_library TEXT NOT NULL,             -- 'igraph_0.11.x'
  graph_compute_library_version TEXT NOT NULL,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL,
  citation_human TEXT NOT NULL,
  computed_at TIMESTAMPTZ NOT NULL,
  engine_version TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, node_type, node_subject)
);

CREATE INDEX cgm_nodes_chart_aya_idx ON l25_cgm_nodes (chart_id, ayanamsha_id);
CREATE INDEX cgm_nodes_snapshot_idx ON l25_cgm_nodes (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_nodes_hub_idx ON l25_cgm_nodes (chart_id, ayanamsha_id) WHERE hub_flag = true;
CREATE INDEX cgm_nodes_pagerank_idx ON l25_cgm_nodes (chart_id, ayanamsha_id, pagerank_score DESC);
CREATE INDEX cgm_nodes_traditions_gin ON l25_cgm_nodes USING gin (present_in_traditions_array);
CREATE INDEX cgm_nodes_embedding_hnsw ON l25_cgm_nodes USING hnsw (node_embedding_vec vector_cosine_ops);
```

### Table 2 — `l25_cgm_edges`

```sql
CREATE TABLE l25_cgm_edges (
  edge_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  snapshot_type TEXT NOT NULL,

  edge_type TEXT NOT NULL,
  from_node_id UUID NOT NULL, to_node_id UUID NOT NULL,
  direction TEXT NOT NULL,

  computed_strength NUMERIC NOT NULL,
  weight_formula_version TEXT NOT NULL,
  edge_properties_jsonb JSONB,

  relationship_class TEXT,                         -- 'reinforcing' | 'opposing' | 'neutral' | 'modulating'
  semantic_path_class TEXT,

  active_duration_class TEXT,                      -- 'lifelong' | 'dasha_bounded' | 'transit_bounded'
  active_dasha_periods_jsonb JSONB,

  underlying_msr_signal_ids_array UUID[],
  cross_system_consensus_count INT,

  cancelled_flag BOOLEAN NOT NULL,
  cancelled_by_jsonb JSONB,

  cross_ayanamsha_edge_stability_score NUMERIC,
  present_in_traditions_array TEXT[],

  -- Edge-level graph indices (igraph-computed at write time)
  edge_betweenness NUMERIC,
  in_shortest_path_count INT,

  graph_compute_library TEXT NOT NULL,
  graph_compute_library_version TEXT NOT NULL,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL,
  citation_human TEXT NOT NULL,
  computed_at TIMESTAMPTZ NOT NULL,
  engine_version TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type, from_node_id, to_node_id)
);

CREATE INDEX cgm_edges_chart_aya_idx ON l25_cgm_edges (chart_id, ayanamsha_id);
CREATE INDEX cgm_edges_snapshot_idx ON l25_cgm_edges (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_edges_from_idx ON l25_cgm_edges (from_node_id);
CREATE INDEX cgm_edges_to_idx ON l25_cgm_edges (to_node_id);
CREATE INDEX cgm_edges_type_idx ON l25_cgm_edges (chart_id, ayanamsha_id, edge_type);
CREATE INDEX cgm_edges_msr_gin ON l25_cgm_edges USING gin (underlying_msr_signal_ids_array);
```

### Table 3 — `l25_cgm_sub_graphs`

```sql
CREATE TABLE l25_cgm_sub_graphs (
  subgraph_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  subgraph_type TEXT NOT NULL,                     -- 'per_domain_<id>' | 'per_tradition_<id>' | 'karaka_network' | 'saham_network' | 'midpoint_network' | 'ego_<node_subject>' | 'cluster_<id>' | 'sade_sati_active'
  subgraph_label TEXT NOT NULL,
  node_ids_array UUID[] NOT NULL,                  -- serialized pointer array
  edge_ids_array UUID[] NOT NULL,                  -- serialized pointer array
  subgraph_density NUMERIC,
  subgraph_centroid_node_id UUID,
  representative_path_jsonb JSONB,
  classical_archetype_match TEXT,
  graphml_export_jsonb JSONB,                      -- pre-shaped for Gephi/Cytoscape
  gexf_export_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX cgm_sub_graphs_chart_idx ON l25_cgm_sub_graphs (chart_id, ayanamsha_id, subgraph_type);
```

### Table 4 — `l25_cgm_motifs`

```sql
CREATE TABLE l25_cgm_motifs (
  motif_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id, snapshot_type,
  motif_name TEXT NOT NULL,                        -- from classical motif library (~30-50 entries)
  motif_class TEXT NOT NULL,                       -- 'reinforcing_triad' | 'tension_diad' | 'hub_spoke' | 'cycle_3' | 'kala_sarpa_axis' | 'adhi_yoga_formation' | 'gajakesari_triad' | etc.
  involved_node_ids_array UUID[] NOT NULL,
  involved_edge_ids_array UUID[] NOT NULL,
  motif_strength NUMERIC NOT NULL,
  classical_citation_id TEXT,
  fingerprint_hash TEXT NOT NULL,                  -- for cross-chart similarity search
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX cgm_motifs_chart_idx ON l25_cgm_motifs (chart_id, ayanamsha_id);
CREATE INDEX cgm_motifs_name_idx ON l25_cgm_motifs (motif_name);
CREATE INDEX cgm_motifs_fingerprint_idx ON l25_cgm_motifs (fingerprint_hash);
```

### Table 5 — `l25_cgm_chart_topology_summary`

```sql
CREATE TABLE l25_cgm_chart_topology_summary (
  summary_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id, snapshot_type,
  total_nodes INT, total_edges INT,
  top_5_hub_nodes_jsonb JSONB,
  top_5_central_nodes_jsonb JSONB,                 -- by pagerank
  triangle_count INT,
  strongly_connected_components_count INT,
  graph_diameter INT,
  graph_density NUMERIC,
  isolated_node_ids_array UUID[],
  dispositor_cycle_jsonb JSONB,                    -- bidirectional dispositor chains
  hub_dominance_score NUMERIC,                     -- max(pagerank) - mean(pagerank)
  fragmentation_score NUMERIC,
  graph_fingerprint_hash TEXT,                     -- chart-level structural fingerprint for cohort search
  chart_topology_embedding_vec VECTOR(768),        -- pgvector for cross-chart similarity
  per_graha_story_arc_jsonb JSONB,                 -- materialized per-graha lifetime arcs (23 grahas)
  graphml_full_export_jsonb JSONB,
  gexf_full_export_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX cgm_topology_chart_idx ON l25_cgm_chart_topology_summary (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_topology_fingerprint_idx ON l25_cgm_chart_topology_summary (graph_fingerprint_hash);
CREATE INDEX cgm_topology_embedding_hnsw ON l25_cgm_chart_topology_summary USING hnsw (chart_topology_embedding_vec vector_cosine_ops);
```

## §6 — Volume projection per (chart, ayanamsha)

| Component | Rows |
|---|---|
| Nodes — static_natal | ~300 |
| Nodes — per-tradition (×4) | ~1,200 |
| Nodes — dynamic Maha-lord (Vim ~10 + Chara ~12 + Yogini ~16 = ~38 snapshots × 300) | ~11,400 |
| Edges — static_natal | ~1,000 |
| Edges — per-tradition (×4) | ~4,000 |
| Edges — dynamic Maha-lord (~38 × 1000) | ~38,000 |
| Sub-graphs (per-domain × 9 + per-tradition × 4 + karaka + saham + midpoint + cluster × 10 + sade_sati) | ~30 |
| Motifs (~30-50 detected) | ~40 |
| Conflict resolution edges | ~10 |
| Topology summaries (per snapshot) | ~45 |

**Total per (chart, ayanamsha): ~56K rows × 5 ay = ~280K per chart × 20 charts = ~5.6M total.** Comfortable on Cloud SQL.

## §7 — Classical motif library (~30-50 entries)

Pre-defined detection rules each motif fires against. Examples:

- `kala_sarpa_axis_configuration`
- `adhi_yoga_formation_natural_benefics_6_7_8`
- `gajakesari_triad_jupiter_moon_kendra`
- `maharishi_yoga_jupiter_venus_saturn_strong`
- `saraswati_yoga_jupiter_venus_mercury_kendra`
- `lakshmi_yoga_pattern_venus_9L_strong`
- `panch_mahapurusha_<graha>_<position>` (×5)
- `shubha_kartari_yoga_<house>`
- `papa_kartari_yoga_<house>`
- `sunaphi_yoga_planet_in_2H_from_moon`
- `anaphi_yoga_planet_in_12H_from_moon`
- `durudhara_yoga_planets_both_sides_moon`
- `kemadruma_yoga_moon_isolation`
- `vipareeta_raja_yoga_<lord>_in_dusthana`
- `dharma_karma_adhipati_yoga_9L_10L_link`
- `chandra_mangala_yoga_moon_mars_link`
- `shakata_yoga_moon_jupiter_6_8_12_from_each`
- `nadi_yoga_natural_benefic_in_kendra_lord_aspect`
- `parijata_yoga_lagna_lord_dispositor_chain`
- `kahala_yoga_4L_9L_with_lagna_lord`
- ... (extension list documented in motif_library.yaml at A12 implementation)

Each motif gets `fingerprint_hash` for cross-chart similarity.

## §8 — Per-graha story arc materialization

For each of 23 grahas in chart_topology_summary, materialize per_graha_story_arc_jsonb:

```json
{
  "graha": "SAT",
  "natal_position": {...},
  "natal_dignity": "...",
  "lifetime_dasha_activations": [
    {"system": "vimshottari", "level": "maha", "lord": "SAT", "start_iso": "...", "end_iso": "..."},
    {"system": "vimshottari", "level": "antar", "lord": "SAT", "start_iso": "...", "end_iso": "..."},
    ...
  ],
  "major_transit_hits_lifetime": [
    {"event": "sade_sati_cycle_1", "phase": "1", "start_iso": "...", "end_iso": "..."},
    ...
  ],
  "msr_signals_referencing_graha": [...],
  "cdlm_domains_dominated": [...],
  "dispositor_chain_to": [...],
  "predicted_activation_windows_jsonb": {...}
}
```

## §9 — Verification (two-pass + tertiary)

`verification_pass_status` mandatory `two_pass_verified`:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Node positions (ephemeris-derived) | pyswisseph semi-analytical | libephemeris JPL DE440 (delta logged in ephemeris_audit_jsonb) | — |
| Graph-theoretic metrics (centrality, PageRank, clustering, etc.) | igraph C-core | NetworkX cross-check on small sample | Algebraic invariants (sum-to-1 for PageRank, etc.) |
| Motif detection | Pattern detection rules + subgraph isomorphism | Independent subgraph isomorphism algorithm (vf2) | Classical citation cross-check |
| Sub-graph extraction | igraph subgraph() | Manual filter equivalent | — |
| Conflict resolution edges | Contradiction scan + path computation | Independent contradiction graph traversal | — |
| Cross-ayanamsha stability | Per-edge 5-ay variance | Independent calculation | — |
| Fingerprint hashes | SHA-256 over canonical motif structure | Deterministic recomputation | — |

Halt on divergent_flagged. Halt on `ephemeris_audit_jsonb.audit_passed_flag = false`.

## §10 — Retrieval contract

Tool primitives:

- `query_cgm_static_natal_graph(chart_id, ayanamsha_id, tradition?)` → nodes + edges + topology summary
- `query_cgm_dynamic_at_date(chart_id, ayanamsha_id, date)` → 3 snapshots (one per Vim/Chara/Yogini active Maha lord)
- `query_cgm_dynamic_window(chart_id, ayanamsha_id, system_id, maha_lord)` → snapshot
- `query_cgm_sub_graph(chart_id, ayanamsha_id, subgraph_type, subgraph_label?)` → sub-graph rows
- `query_cgm_motifs(chart_id, ayanamsha_id, motif_name?, motif_class?)` → motifs
- `query_cgm_topology_summary(chart_id, ayanamsha_id, snapshot_type)` → summary row
- `query_cgm_per_graha_arc(chart_id, ayanamsha_id, graha)` → arc JSONB
- `query_cgm_ego_network(chart_id, ayanamsha_id, node_subject, depth=2)` → pre-materialized ego sub-graph
- `query_cgm_similar_charts(chart_topology_embedding, top_k=10)` → pgvector cohort lookup
- `query_cgm_motif_peers(fingerprint_hash, top_k=10)` → motif fingerprint lookup
- `export_cgm_graphml(chart_id, ayanamsha_id, snapshot_type)` → GraphML XML
- `export_cgm_gexf(chart_id, ayanamsha_id, snapshot_type)` → GEXF XML

## §11 — BigQuery cold-data export hook

Orthogonal research analytics layer. NOT in SoR write path.

At A12 build close, scheduled Airflow/Cloud Composer DAG exports the following to BigQuery as columnar tables:

- `bq_l25_cgm_nodes` — partitioned by chart_id, clustered by snapshot_type
- `bq_l25_cgm_edges` — partitioned by chart_id, clustered by edge_type
- `bq_l25_cgm_motifs` — partitioned by chart_id
- `bq_l25_cgm_topology_summary` — partitioned by chart_id

Use cases: cross-chart cohort motif frequency analysis, per-domain centrality distributions, temporal evolution gradients across 1950-2100 window aggregated across N charts. Postgres remains SoR; BigQuery is read-only research layer.

## §12 — Implementation notes

1. **WIPE existing `l25_cgm_*` rows** before A12 writer runs.
2. Compute order: dependencies finalized → graph constructed in igraph in-memory → centrality/PageRank/clustering computed → motif detection → sub-graph extraction → ego-network materialization → conflict-resolution-edge derivation → per-graha story arc → topology summary → embeddings computed → GraphML/GEXF serialization → batch write to Postgres.
3. **igraph version pinning**: lock to igraph >= 0.11.x (Python). Version recorded on every row.
4. **Embedding model**: pgvector embeddings derived from node/chart structural features via Node2Vec or graph spectral methods. Embedding dimension 768. Cosine similarity index via HNSW.
5. **Fingerprint hash algorithm**: SHA-256 over canonical-form serialization of motif graph (sorted node types + edge types + topology), so isomorphic motifs across charts share the same hash.
6. **Cross-asset prerequisites**: A7 chart_dashas must be range-partitioned (cross-asset spec amendment may be needed); A11 CDLM enrichment fields populated; A10 MSR signals fully written; A6 vargas materialized for D9/D10/D60 + 16 Parashari nodes.
7. **Audit threshold**: ephemeris_audit_jsonb.audit_threshold_arcsec = 3.0 (generous; tighten as we learn distributions).

## §13 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Sun node static | `l25_cgm_nodes.static_natal.graha.SUN@chart=...:ay=lahiri:pr=0.142` | "Sun node — Lahiri static graph; PageRank 0.142; betweenness 0.087; hub for lordship + karaka edges." |
| Saturn-Mars opposition edge | `l25_cgm_edges.static_natal.aspect_parashari.SAT-MAR@chart=...:ay=lahiri:strength=0.78` | "Saturn-Mars Parashari opposition aspect, strength 0.78 (orb 2.3°, full quarter)." |
| Kala Sarpa motif | `l25_cgm_motifs.kala_sarpa_axis.<id>@chart=...:ay=lahiri:fp=<hash>` | "Kala Sarpa axis motif: all planets between Rahu-Ketu axis; strength 0.84; fingerprint <hash>." |
| Dynamic Saturn Maha graph | `l25_cgm_nodes.dynamic_maha_vimshottari.SAT@chart=...:ay=lahiri:start=2014-...:end=2017-...` | "Saturn Vimshottari Maha snapshot (2014-2017): graph centered on Saturn-7H configuration." |
| Career sub-graph | `l25_cgm_sub_graphs.per_domain_career@chart=...:ay=lahiri:nodes=23:edges=47` | "Career domain sub-graph: 23 nodes, 47 edges; centroid Saturn; density 0.18." |

## §14 — Locked decisions (final committed surface)

1. 5-table storage architecture (nodes + edges + sub_graphs + motifs + topology_summary)
2. Static + Maha-lord level dynamic snapshots × 3 systems (Vim + Chara + Yogini)
3. 4 tradition views (Parashari + Jaimini + Tajik + KP)
4. 24 edge types (separate, not bundled)
5. Full sub-graph extraction (domain + tradition + karaka + saham + midpoint + cluster + ego + sade_sati)
6. Classical motif library (~30-50 entries) with fingerprint hashes
7. Per-graha story arc materialized
8. GraphML + GEXF export hooks
9. Conflict resolution edges (new edge type)
10. pgvector embeddings on key nodes + topology summary
11. **igraph in-memory graph compute at write time** (no AGE, no runtime graph engine)
12. **Native PostgreSQL declarative range partitioning on chart_dashas** (cross-asset prerequisite)
13. **Dual-source ephemeris audit via libephemeris JPL DE440** (ephemeris_audit_jsonb)
14. BigQuery cold-data export as research analytics layer (orthogonal to SoR)
15. Two-pass verification mandatory; halt on ephemeris audit failure
16. WIPE existing l25_cgm_* rows before rebuild
17. ~280K rows per chart × 20 charts = ~5.6M total — comfortable on Cloud SQL

## §15 — What is NOT in A12 (out of scope)

- Apache AGE runtime graph engine — REJECTED per Option E (cloud constraint)
- TimescaleDB hypertables on chart_dashas — REJECTED per Option E (use native PG partitioning)
- Spanner Graph — REJECTED per Option E (scale mismatch; ~$700/mo floor)
- NumPyro Bayesian inference — DEFERRED to M6 (06_LEARNING_LAYER scaffold)
- Maha-Antar level dynamic graphs — graph topology doesn't change at Antar level
- Hypergraph native storage — reification via configuration nodes is the standard pattern
- LLM in compute path — never (prime directive)

---

*End of A12_CGM_SPEC_v1_0.md — LOCKED 2026-05-29 under Option E. Native sign-off complete.*
