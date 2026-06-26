-- Migration 355: mi_vistara — export-integrity ledger
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_export_log (
  export_id              text        NOT NULL,
  chart_id               uuid        NOT NULL,
  exported_at            timestamptz NOT NULL DEFAULT now(),
  export_format          text        NOT NULL,  -- 'pdf'|'json'|'mcp_bundle'|'portal_view'
  recipient_ref          text,
  included_insight_ids   jsonb       NOT NULL,
  contribution_state     jsonb       NOT NULL,
  calibration_mode       text        NOT NULL,
  disclosures_attached   jsonb       NOT NULL,
  payload_hash           text        NOT NULL,
  lel_version            text        NOT NULL,
  export_formula_version text        NOT NULL,
  PRIMARY KEY (export_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_chart_id
  ON mimamsa_export_log (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_exported_at
  ON mimamsa_export_log (chart_id, exported_at);

COMMIT;
