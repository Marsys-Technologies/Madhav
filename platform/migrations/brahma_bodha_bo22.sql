-- brahma_bodha_bo22.sql
-- BRAHMA-BO-2-2: bodha.graph — CGM signal graph (valenced edges between signals)
--
-- Contract (BRAHMA_L1_L5_REGISTRY_SEED §C):
--   table:   bodha_graph (chart_id, from_signal_id, to_signal_id, edge_type, weight, source_citation)
--   tool:    cgm_subgraph(chart_id, signal_ids?) → edges with provenance
--   gate:    valenced edges present; traversal returns provenance; no self-loops
--   FORENSIC: ≥5 edges for native chart (1984-02-05 / chart_id = 362f9f17-...)
--
-- Edge type vocabulary (Gate-1 contract enum — valenced only):
--   reinforce  — two signals amplify each other's theme
--   contradict — two signals pull in opposite directions (contradiction hub)
--   modulate   — one signal contextually modulates another
--   amplify    — one signal intensifies another's expression
--   suppress   — one signal dampens or blocks another
--
-- Source: 22 edges from 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json
--         (Batch 2 reconciled, 0 P2 violations, session Madhav_M2A_Exec_5/6)
--
-- ROLLBACK: DROP TABLE IF EXISTS bodha_graph;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bodha_graph (
  edge_id          TEXT        NOT NULL,
  chart_id         UUID        REFERENCES charts(chart_id),
  from_signal_id   TEXT        NOT NULL,
  to_signal_id     TEXT        NOT NULL,
  edge_type        TEXT        NOT NULL CHECK (edge_type IN ('reinforce','contradict','modulate','amplify','suppress')),
  weight           FLOAT       NOT NULL CHECK (weight >= 0 AND weight <= 1),
  source_citation  TEXT        NOT NULL,
  ayanamsha_id     TEXT        NOT NULL DEFAULT 'lahiri',
  build_id         TEXT,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT bodha_graph_pk PRIMARY KEY (edge_id),
  CONSTRAINT no_self_loop CHECK (from_signal_id != to_signal_id)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- Primary traversal: all edges for a chart
CREATE INDEX IF NOT EXISTS idx_bodha_graph_chart_id
  ON bodha_graph (chart_id);

-- Forward traversal: outbound edges from a signal
CREATE INDEX IF NOT EXISTS idx_bodha_graph_from_signal
  ON bodha_graph (chart_id, from_signal_id);

-- Reverse traversal: inbound edges to a signal
CREATE INDEX IF NOT EXISTS idx_bodha_graph_to_signal
  ON bodha_graph (chart_id, to_signal_id);

-- Edge type filter
CREATE INDEX IF NOT EXISTS idx_bodha_graph_edge_type
  ON bodha_graph (chart_id, edge_type);

-- ── Staging mirror (idempotent swap pattern per project convention) ───────────

CREATE TABLE IF NOT EXISTS bodha_graph_staging
  (LIKE bodha_graph INCLUDING ALL);

-- ── Constraints comment ───────────────────────────────────────────────────────
COMMENT ON TABLE bodha_graph IS
  'BRAHMA-BO-2-2: CGM signal graph — valenced edges between CGM node signals. '
  'Seeded from 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json (22 reconciled edges). '
  'Contract: no self-loops; each edge carries source_citation back to FORENSIC_v8_0. '
  'Tool: cgm_subgraph via platform-mcp/src/tools/bodha_bo22.ts.';
