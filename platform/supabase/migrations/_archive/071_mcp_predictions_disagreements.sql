-- Migration 071: MCP Predictions and Disagreement Log tables
--
-- Purpose (MCP-4-S1):
--   mcp_predictions  — interim PPL substrate for predictions logged via MCP.
--                      Per MCP_BRIEF §8 R9, the formal 06_LEARNING_LAYER/ PPL
--                      substrate is not yet scaffolded; this table is the interim
--                      path. Migrate to the formal PPL API when 06_LEARNING_LAYER/
--                      scaffolds per CLAUDE.md §E.
--   mcp_disagreements — in-DB log for flag_disagreement MCP writes. Entries mirror
--                       the schema of DISAGREEMENT_REGISTER_v1_0.md §2, stored
--                       relationally for query/audit. The markdown register itself
--                       remains the human-readable governance surface; this table
--                       is the machine-queryable mirror.
--
-- TODO(MCP-MIGRATION): when 06_LEARNING_LAYER/ is scaffolded, migrate all rows
-- from mcp_predictions to the formal PPL API. Migration path:
--   1. Read all rows from mcp_predictions.
--   2. POST each to the new PPL API endpoint (to be authored in M-arc scope).
--   3. Mark migrated rows with migrated_at timestamp.
--   4. Retain this table as archive with status='migrated'.

-- ── mcp_predictions ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mcp_predictions (
  -- Identity
  prediction_id       text        PRIMARY KEY,          -- "PPL.MCP." + nanoid(8)
  logged_at           timestamptz NOT NULL DEFAULT now(),

  -- Prediction content
  horizon             text        NOT NULL,             -- "2026-Q3" or "2026-09-30"
  domain              text        NOT NULL,             -- "career", "health", etc.
  prediction_text     text        NOT NULL,             -- prediction prose (≤2000 chars)
  confidence          text        NOT NULL
                      CHECK (confidence IN ('high', 'medium', 'low')),
  falsifier           text        NOT NULL,             -- what would falsify this

  -- Provenance (G4 — full traceability)
  key_id              text        NOT NULL,             -- mcp_api_keys.key_id
  trace_id            text,                             -- query_id of originating call
  caller_context      text,                             -- optional label from caller

  -- Outcome (populated by record_outcome)
  outcome_text        text,
  verified            boolean,                          -- null until outcome is recorded
  outcome_notes       text,
  outcome_recorded_at timestamptz,
  outcome_key_id      text,
  outcome_trace_id    text,

  -- Migration tracking
  migrated_at         timestamptz,                      -- set when migrated to formal PPL
  migrated_to         text                              -- destination PPL entry ID
);

-- Index for principal-keyed lookups (list_predictions per key)
CREATE INDEX IF NOT EXISTS mcp_predictions_key_id_idx
  ON mcp_predictions (key_id, logged_at DESC);

-- Index for trace-id linkage (find predictions from a given query)
CREATE INDEX IF NOT EXISTS mcp_predictions_trace_id_idx
  ON mcp_predictions (trace_id)
  WHERE trace_id IS NOT NULL;

-- ── mcp_disagreements ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mcp_disagreements (
  -- Identity (mirrors DR schema §2)
  disagreement_id     text        PRIMARY KEY,          -- "DIS.MCP." + nanoid(8)
  logged_at           timestamptz NOT NULL DEFAULT now(),

  -- Classification (from DISAGREEMENT_REGISTER_v1_0.md §1 + §1a)
  class               text        NOT NULL
                      CHECK (class IN (
                        'factual', 'interpretive', 'structural',
                        'mirror_desync', 'scope',
                        -- Additional classes from the DR
                        'output_conflict', 'version_disagreement',
                        'scope_disagreement', 'closure_disagreement',
                        'l3_zero_supports', 'panel_divergence',
                        'school_disagreement', 'acceptance_rate_anomaly'
                      )),

  -- Content
  description         text        NOT NULL,
  source_session      text        NOT NULL,             -- caller-provided session label
  proposed_resolution text,

  -- Status (starts open; native updates via governance session)
  status              text        NOT NULL DEFAULT 'open'
                      CHECK (status IN ('open', 'resolved', 'escalated', 'reopened')),

  -- Provenance
  key_id              text        NOT NULL,
  trace_id            text,

  -- Resolution (populated when status changes to resolved)
  resolved_on         timestamptz,
  resolved_by_session text,
  resolution_notes    text
);

-- Index for open-entry audit queries
CREATE INDEX IF NOT EXISTS mcp_disagreements_status_idx
  ON mcp_disagreements (status, logged_at DESC);

CREATE INDEX IF NOT EXISTS mcp_disagreements_key_id_idx
  ON mcp_disagreements (key_id, logged_at DESC);
