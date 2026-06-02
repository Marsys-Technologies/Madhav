-- platform/migrations/038_observatory_schema.sql
-- Migration: Observatory schema — five tables for the Phase O (LLM Cost & Usage
--            Observatory) two-layer ledger: telemetry (computed) +
--            reconciliation (authoritative). See OBSERVATORY_PLAN_v1_0.md §3.
--
--   Table 1 — llm_pricing_versions       (versioned price book; append-only)
--   Table 2 — llm_usage_events           (per-call telemetry; FK to pricing)
--   Table 3 — llm_provider_cost_reports  (raw daily admin-API pulls)
--   Table 4 — llm_cost_reconciliation    (variance ledger; computed vs authoritative)
--   Table 5 — llm_budget_rules           (spend thresholds + alert thresholds)
--
-- Created by USTAD_S1_1_OBSERVATORY_SCHEMA (2026-05-03) — Phase O sub-phase O.1.
-- Consumed by S1.2 (instrumentation shim), S1.3 (dashboard backend),
--             S1.4–S1.8 (per-provider adapters), S2.1+ (reconciliation framework),
--             S3.1+ (budget rules), S4.5 (replay & re-cost).
-- Idempotent:  CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.
-- Down:        platform/migrations/038_observatory_schema_down.sql

BEGIN;

-- -----------------------------------------------------------------------------
-- Table 1: llm_pricing_versions  (created first — llm_usage_events FKs into it)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_pricing_versions (
  pricing_version_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider                TEXT NOT NULL,
  model                   TEXT NOT NULL,
  token_class             TEXT NOT NULL,
  price_per_million_usd   NUMERIC(14, 8) NOT NULL,
  effective_from          TIMESTAMPTZ NOT NULL,
  effective_to            TIMESTAMPTZ,
  source_url              TEXT,
  recorded_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_pricing_versions_token_class_check
    CHECK (token_class IN ('input','output','cache_read','cache_write','reasoning'))
);

CREATE INDEX IF NOT EXISTS idx_llm_pricing_versions_lookup
  ON llm_pricing_versions (provider, model, effective_from DESC);

-- Idempotent seed support: dedupe on the natural key.
-- Allows seed_v1 to use INSERT ... ON CONFLICT DO NOTHING.
CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_pricing_versions_natural_key
  ON llm_pricing_versions (provider, model, token_class, effective_from);

-- -----------------------------------------------------------------------------
-- Table 2: llm_usage_events  (per-call telemetry)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_usage_events (
  event_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id       TEXT NOT NULL,
  conversation_name     TEXT,
  prompt_id             TEXT NOT NULL,
  parent_prompt_id      TEXT,
  user_id               TEXT NOT NULL,
  provider              TEXT NOT NULL,
  model                 TEXT NOT NULL,
  pipeline_stage        TEXT NOT NULL,
  prompt_text           TEXT,
  response_text         TEXT,
  system_prompt         TEXT,
  parameters            JSONB,
  input_tokens          INTEGER,
  output_tokens         INTEGER,
  cache_read_tokens     INTEGER DEFAULT 0,
  cache_write_tokens    INTEGER DEFAULT 0,
  reasoning_tokens      INTEGER DEFAULT 0,
  computed_cost_usd     NUMERIC(12, 6),
  pricing_version_id    UUID REFERENCES llm_pricing_versions(pricing_version_id),
  latency_ms            INTEGER,
  status                TEXT NOT NULL,
  error_code            TEXT,
  provider_request_id   TEXT,
  started_at            TIMESTAMPTZ NOT NULL,
  finished_at           TIMESTAMPTZ,
  feature_flag_state    JSONB,
  client_ip_hash        TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_usage_events_provider_check
    CHECK (provider IN ('anthropic','openai','gemini','deepseek','nim')),
  CONSTRAINT llm_usage_events_pipeline_stage_check
    CHECK (pipeline_stage IN ('classify','compose','retrieve','synthesize','audit','other')),
  CONSTRAINT llm_usage_events_status_check
    CHECK (status IN ('success','error','timeout')),
  -- Required for parent_prompt_id self-FK below: PostgreSQL FKs need a
  -- UNIQUE (or PK) on the referenced column. Brief column list specifies
  -- `parent_prompt_id text nullable references llm_usage_events(prompt_id)`.
  CONSTRAINT uq_llm_usage_events_prompt_id UNIQUE (prompt_id),
  CONSTRAINT fk_llm_usage_events_parent_prompt
    FOREIGN KEY (parent_prompt_id) REFERENCES llm_usage_events(prompt_id)
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_started_at
  ON llm_usage_events (started_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_provider_model
  ON llm_usage_events (provider, model);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_conversation_id
  ON llm_usage_events (conversation_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_user_id
  ON llm_usage_events (user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_pipeline_stage
  ON llm_usage_events (pipeline_stage);

-- -----------------------------------------------------------------------------
-- Table 3: llm_provider_cost_reports  (raw daily admin-API pulls)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_provider_cost_reports (
  report_id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider                      TEXT NOT NULL,
  model                         TEXT,
  time_bucket_start             TIMESTAMPTZ NOT NULL,
  time_bucket_end               TIMESTAMPTZ NOT NULL,
  workspace_id                  TEXT,
  authoritative_cost_usd        NUMERIC(14, 6) NOT NULL,
  authoritative_input_tokens    BIGINT,
  authoritative_output_tokens   BIGINT,
  raw_payload                   JSONB,
  pulled_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_provider_cost_reports_provider_bucket
  ON llm_provider_cost_reports (provider, time_bucket_start);

-- -----------------------------------------------------------------------------
-- Table 4: llm_cost_reconciliation  (per-day per-provider variance ledger)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_cost_reconciliation (
  reconciliation_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reconciliation_date       DATE NOT NULL,
  provider                  TEXT NOT NULL,
  model                     TEXT,
  computed_total_usd        NUMERIC(14, 6) NOT NULL,
  authoritative_total_usd   NUMERIC(14, 6),
  variance_usd              NUMERIC(14, 6),
  variance_pct              NUMERIC(8, 4),
  event_count               INTEGER NOT NULL,
  status                    TEXT NOT NULL,
  notes                     TEXT,
  reconciled_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_cost_reconciliation_status_check
    CHECK (status IN ('matched','variance_within_tolerance','variance_alert','missing_authoritative'))
);

CREATE INDEX IF NOT EXISTS idx_llm_cost_reconciliation_date_provider
  ON llm_cost_reconciliation (reconciliation_date, provider);

-- Brief: `Unique constraint: (reconciliation_date, provider, coalesce(model, ''))`.
-- Constraints can't reference expressions, so use a UNIQUE INDEX over the
-- expression. Effect is identical: rejects duplicate (date, provider, model)
-- including the model=NULL case, which a plain UNIQUE column tuple would
-- treat as not-equal-to-itself.
CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_cost_reconciliation_natural_key
  ON llm_cost_reconciliation (reconciliation_date, provider, COALESCE(model, ''));

-- -----------------------------------------------------------------------------
-- Table 5: llm_budget_rules  (spend thresholds + alert thresholds)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_budget_rules (
  budget_rule_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                  TEXT NOT NULL,
  scope                 TEXT NOT NULL,
  scope_value           TEXT,
  period                TEXT NOT NULL,
  amount_usd            NUMERIC(12, 2) NOT NULL,
  alert_thresholds      JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by_user_id    TEXT,
  active                BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_budget_rules_scope_check
    CHECK (scope IN ('total','provider','model','pipeline_stage')),
  CONSTRAINT llm_budget_rules_period_check
    CHECK (period IN ('daily','weekly','monthly'))
);

COMMIT;
