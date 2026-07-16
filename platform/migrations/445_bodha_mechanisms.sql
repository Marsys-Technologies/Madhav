-- Migration 445: bodha_mechanisms — Mechanism object (D-2 Lane V-4)
-- Created: 2026-07-16
--
-- CR-24/CR-25/CR-86 (BRIEF_D2.md Lane V-4; DIS.020/DR-7 edge-strength ruling):
-- a Mechanism is a named, valenced CGM subgraph — first-class table + serving
-- face. Promotes bodha_cgm_motifs (yoga_cluster / mutual_reception /
-- parivartana_chain / stellium / mutual_aspect_triangle) plus the new
-- dispositor/house-lordship chain-and-circuit detector (bo_yantra_mechanism)
-- into a single named-mechanism surface with real edge-strength provenance
-- (constituent ga_vichara row ids, DR-7 formula_version) and a centrality
-- summary over its member nodes.
--
-- Idempotency (§N.3): per-chart delete-then-insert, scoped via fingerprint_hash
-- + UNIQUE(chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash).
--
-- Also (DR-7 / CR-86): bodha_cgm_edges gains constituent_ga_vichara_ids_array so
-- every edge_strength_v1 edge cites the specific chart_vichara.id rows it was
-- computed from (§N.5 — L1/L2 authority is referenced, never restated).

BEGIN;

CREATE TABLE IF NOT EXISTS bodha_mechanisms (
  mechanism_id                        UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL DEFAULT 'static_natal',

  mechanism_name                      TEXT NOT NULL,
  mechanism_class                     TEXT NOT NULL,   -- yoga_cluster | mutual_reception | parivartana_chain | stellium | mutual_aspect_triangle | convergent_dispositor_chain | dispositor_cycle | house_lordship_cycle
  valence                             TEXT NOT NULL,    -- benefic | malefic | mixed | neutral

  member_node_ids_array               UUID[] NOT NULL,
  member_edge_ids_array               UUID[] NOT NULL DEFAULT '{}',
  domains_affected_array              TEXT[],

  edge_strength_avg                   NUMERIC,
  edge_strength_min                   NUMERIC,
  edge_strength_max                   NUMERIC,
  edge_strength_formula_version       TEXT,             -- 'edge_strength_v1' (DR-7)
  constituent_ga_vichara_ids_array    TEXT[] NOT NULL DEFAULT '{}',

  centrality_summary_jsonb            JSONB,            -- {pagerank_avg, eigenvector_avg, betweenness_avg, harmonic_avg}
  source_motif_id                     UUID,             -- bodha_cgm_motifs.motif_id when promoted from a motif; NULL for chain/circuit-only mechanisms

  fingerprint_hash                    TEXT NOT NULL,

  verification_pass_status            TEXT NOT NULL DEFAULT 'documented_approximation',
  citation_ref                        TEXT,
  citation_human                      TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL,
  engine_version                      TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash)
);

CREATE INDEX IF NOT EXISTS idx_bodha_mechanisms_chart
  ON bodha_mechanisms (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_bodha_mechanisms_class
  ON bodha_mechanisms (chart_id, mechanism_class);

-- DR-7: every edge_strength_v1 edge cites the chart_vichara.id rows (valence_pass /
-- varga_ratification / varga_consistency) it was computed from.
ALTER TABLE bodha_cgm_edges
  ADD COLUMN IF NOT EXISTS constituent_ga_vichara_ids_array TEXT[] NOT NULL DEFAULT '{}';

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_yantra_mechanism', 'bodha', 20,
  'yantra', 'Mechanism (Yantra)',
  'Named, valenced CGM subgraph — promotes CGM motifs + dispositor/house-lordship chain-and-circuit detection into first-class mechanisms with real edge-strength provenance (DR-7) and a centrality summary (CR-24/CR-25/CR-86)',
  'postgres_table', 'bodha_mechanisms',
  'SELECT count(*) FROM bodha_mechanisms WHERE chart_id = $1',
  1, ARRAY['bo_karanajala', 'bo_cgm_motifs', 'bo_cgm_paths'], 'per_chart', true, NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET
  layer                = EXCLUDED.layer,
  sanskrit_name         = EXCLUDED.sanskrit_name,
  english_name          = EXCLUDED.english_name,
  english_description   = EXCLUDED.english_description,
  storage_type          = EXCLUDED.storage_type,
  target_table          = EXCLUDED.target_table,
  count_sql             = EXCLUDED.count_sql,
  target_floor          = EXCLUDED.target_floor,
  depends_on            = EXCLUDED.depends_on,
  scope                 = EXCLUDED.scope,
  has_writer            = true;

COMMIT;
