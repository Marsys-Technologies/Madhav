-- Migration 030 — KARN-W2-R3-CGM-FULL-EDGES — l25_cgm_edges auxiliary indexes
-- Predecessor: KARN-W1-R1-PHASE-ALPHA + Pre-KARN-2 (orphan resolution)
-- Purpose: Accelerate cgm_graph_walk traversal queries on edge_type / source / target / strength.

BEGIN;

CREATE INDEX IF NOT EXISTS l25_cgm_edges_edge_type_idx
  ON l25_cgm_edges(edge_type);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_source_idx
  ON l25_cgm_edges(source_node_id);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_target_idx
  ON l25_cgm_edges(target_node_id);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_strength_idx
  ON l25_cgm_edges(strength) WHERE strength IS NOT NULL;

COMMIT;
