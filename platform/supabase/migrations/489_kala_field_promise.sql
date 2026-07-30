-- Migration 489: kala_field_promise_nodes/edges/routes — ṢAḌ-DARŚANA W2
-- Lane A, Stage 2 (the promise graph + alternate routings).
-- =============================================================================
-- Spec: KALA_W2_FIELD_DESIGN_v1_0.md §3.3. Owned by Lane A per §0's
-- anti-collision contract — Lane A owns these three tables exclusively.
--
-- Migration-range note: see 488_kala_field_stage0_1.sql's header — same
-- range (474-483), re-verified free immediately before writing this file.
--
-- Nirmāṇa contract (brief §2.5, CLAUDE.md §N.4): no asset_registry row lands
-- here — `ka_kshetra` is the ONE registered asset per §9.2, owned by Lane C.
-- These tables are Lane A's per-chart derived data, populated by
-- services/ka_kshetra/stage2_promise.py once `ka_kshetra` invokes it.
-- Idempotency (§N.3): per-chart delete-then-insert, scoped ONCE in
-- ka_kshetra.plan_substeps (Lane C); row-level upserts here (ON CONFLICT DO
-- UPDATE on the natural key) are the row-grain safety net.
-- =============================================================================

BEGIN;

-- ── kala_field_promise_nodes ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_promise_nodes (
  id             BIGSERIAL PRIMARY KEY,
  chart_id       UUID NOT NULL,
  node_id        TEXT NOT NULL,   -- e.g. 'graha:Ma' | 'bhava:10' | 'event_class:career_change'
  node_kind      TEXT NOT NULL CHECK (node_kind IN (
                   'graha', 'bhava', 'bhava_lord', 'karaka', 'yoga', 'arudha', 'event_class'
                 )),
  label          TEXT NOT NULL,
  source_kind    TEXT NOT NULL CHECK (source_kind IN (
                   'l0_reference', 'l1_fact', 'l2_signal', 'l3_row', 'derived'
                 )),
  source_table   TEXT,
  source_pk      TEXT,
  source_fact_id TEXT,
  computed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chart_id, node_id)
);

CREATE INDEX IF NOT EXISTS idx_kfpn_chart_kind ON kala_field_promise_nodes (chart_id, node_kind);

COMMENT ON TABLE kala_field_promise_nodes IS
  'SAD-DARSANA W2 Lane A Stage 2: promise-graph nodes, digested from L2 Bodha '
  '(bodha_cgm_nodes for graha/bhava/yoga/arudha structural nodes; bodha_pratijna '
  'for event_class sinks). KALA_W2_FIELD_DESIGN_v1_0.md Sec3.3.';

-- ── kala_field_promise_edges ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_promise_edges (
  id                  BIGSERIAL PRIMARY KEY,
  chart_id            UUID NOT NULL,
  from_node           TEXT NOT NULL,
  to_node             TEXT NOT NULL,
  edge_kind           TEXT NOT NULL CHECK (edge_kind IN (
                        'dispositor', 'lordship', 'occupation', 'aspect', 'argala',
                        'yoga_membership', 'karaka_signification', 'class_signification'
                      )),
  conductance         DOUBLE PRECISION NOT NULL CHECK (conductance > 0 AND conductance <= 1),
  conductance_source  TEXT NOT NULL CHECK (conductance_source IN ('l2_inherited', 'ungraded_default')),
  source_fact_id      TEXT,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chart_id, from_node, to_node, edge_kind)
);

CREATE INDEX IF NOT EXISTS idx_kfpe_chart_from ON kala_field_promise_edges (chart_id, from_node);
CREATE INDEX IF NOT EXISTS idx_kfpe_chart_to   ON kala_field_promise_edges (chart_id, to_node);

COMMENT ON TABLE kala_field_promise_edges IS
  'SAD-DARSANA W2 Lane A Stage 2: promise-graph edges. edge_kind=class_signification '
  'is the ONLY kind pointing at an event_class node. conductance is INHERITED from '
  'the L2 signal strength that asserts the relation, never invented — '
  'conductance_source=ungraded_default (c=0.60) only when the L2 signal carries no '
  'graded strength. KALA_W2_FIELD_DESIGN_v1_0.md Sec3.3.';

-- ── kala_field_routes ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_routes (
  id              BIGSERIAL PRIMARY KEY,
  chart_id        UUID NOT NULL,
  event_class     TEXT NOT NULL,
  route_rank      INT NOT NULL,
  path_node_ids   TEXT[] NOT NULL,
  path_edge_ids   BIGINT[] NOT NULL,
  route_gain      DOUBLE PRECISION NOT NULL CHECK (route_gain > 0 AND route_gain <= 1),
  is_primary      BOOLEAN NOT NULL,
  suppressed_by   TEXT[] NOT NULL DEFAULT '{}',
  computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chart_id, event_class, route_rank)
);

CREATE INDEX IF NOT EXISTS idx_kfr_chart_class ON kala_field_routes (chart_id, event_class);

COMMENT ON TABLE kala_field_routes IS
  'SAD-DARSANA W2 Lane A Stage 2: alternate routings from significator seeds to an '
  'event_class sink — Yen''s K-shortest-loopless-paths (K=5) over the promise '
  'graph, route_gain = product of edge conductances along the path. The '
  'noisy-OR combination of these routes'' route_gain is the event class''s '
  'promise prior P_e (served via the promise_prior() published function, not '
  'stored as a column on this table). KALA_W2_FIELD_DESIGN_v1_0.md Sec3.3.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_field_routes;
--   DROP TABLE IF EXISTS kala_field_promise_edges;
--   DROP TABLE IF EXISTS kala_field_promise_nodes;
--   COMMIT;
-- =============================================================================
