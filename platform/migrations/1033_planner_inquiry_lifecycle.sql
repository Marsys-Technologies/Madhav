-- Migration 1033: durable planner inquiry lifecycle and evidence receipts
-- Created: 2026-09-13

BEGIN;

CREATE TABLE IF NOT EXISTS planner_inquiry_lifecycles (
  inquiry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  principal_uid text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE RESTRICT,
  semantic_contract_hash text NOT NULL,
  execution_plan_hash text NOT NULL,
  capability_content_hash text NOT NULL,
  capability_compatibility_version text NOT NULL,
  chart_overlay_version text,
  chart_build_id text,
  contract_jsonb jsonb NOT NULL,
  status text NOT NULL DEFAULT 'INCOMPLETE'
    CHECK (status IN ('INCOMPLETE', 'COMPLETE', 'BLOCKED')),
  revision integer NOT NULL DEFAULT 0 CHECK (revision >= 0),
  current_jti_hash text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS planner_inquiry_lifecycles_principal_chart_idx
  ON planner_inquiry_lifecycles (principal_uid, chart_id, created_at DESC);

CREATE INDEX IF NOT EXISTS planner_inquiry_lifecycles_expiry_idx
  ON planner_inquiry_lifecycles (expires_at)
  WHERE status = 'INCOMPLETE';

CREATE TABLE IF NOT EXISTS planner_inquiry_evidence_receipts (
  receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  inquiry_id uuid NOT NULL REFERENCES planner_inquiry_lifecycles(inquiry_id) ON DELETE RESTRICT,
  revision integer NOT NULL CHECK (revision >= 1),
  obligation_ids text[] NOT NULL,
  plan_item_id text NOT NULL,
  scu_id text NOT NULL,
  binding_id text NOT NULL,
  canonical_args_hash text NOT NULL,
  raw_result_hash text NOT NULL,
  disposition text NOT NULL CHECK (disposition IN ('served', 'empty', 'dark', 'failed')),
  pagination_jsonb jsonb NOT NULL DEFAULT '{"semantics":"none","exhausted":true}'::jsonb,
  evidence_jsonb jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (inquiry_id, revision)
);

CREATE INDEX IF NOT EXISTS planner_inquiry_evidence_receipts_inquiry_idx
  ON planner_inquiry_evidence_receipts (inquiry_id, created_at);

CREATE INDEX IF NOT EXISTS planner_inquiry_evidence_receipts_item_idx
  ON planner_inquiry_evidence_receipts (inquiry_id, plan_item_id, revision);

COMMENT ON TABLE planner_inquiry_lifecycles IS
  'Durable, principal-bound Inquiry Contract state. current_jti_hash + revision are consumed with compare-and-swap; raw MCP tokens are not bearer access to chart evidence.';
COMMENT ON TABLE planner_inquiry_evidence_receipts IS
  'Server-observed raw retrieval evidence. A client cannot self-assert served/empty completion.';
COMMENT ON COLUMN planner_inquiry_lifecycles.chart_build_id IS
  'Opaque build/provenance token copied from the chart overlay. Not a build_runs foreign key because legacy build identities are not uniformly UUID typed.';

-- Existing table grants are point-in-time, so new lifecycle tables require
-- explicit least-privilege grants. Evidence rows are immutable to the web role.
GRANT SELECT, INSERT, UPDATE ON planner_inquiry_lifecycles TO role_web_serve;
GRANT SELECT, INSERT ON planner_inquiry_evidence_receipts TO role_web_serve;

ALTER TABLE planner_inquiry_lifecycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE planner_inquiry_evidence_receipts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS planner_inquiry_lifecycles_principal_chart ON planner_inquiry_lifecycles;
CREATE POLICY planner_inquiry_lifecycles_principal_chart
  ON planner_inquiry_lifecycles AS PERMISSIVE FOR ALL TO role_web_serve
  USING (principal_uid = current_setting('app.principal_id', true)
         AND chart_id = app_chart_context())
  WITH CHECK (principal_uid = current_setting('app.principal_id', true)
              AND chart_id = app_chart_context());

DROP POLICY IF EXISTS planner_inquiry_evidence_receipts_principal_chart ON planner_inquiry_evidence_receipts;
CREATE POLICY planner_inquiry_evidence_receipts_principal_chart
  ON planner_inquiry_evidence_receipts AS PERMISSIVE FOR ALL TO role_web_serve
  USING (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_evidence_receipts.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_evidence_receipts.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ));

COMMIT;

-- DOWN (manual, destructive; retain/export evidence before use):
-- User/chart archival or deletion must first export retained evidence, then
-- delete receipts before lifecycles. ON DELETE RESTRICT is intentional so an
-- administrative deletion cannot silently destroy the audit trail.
-- DROP TABLE IF EXISTS planner_inquiry_evidence_receipts;
-- DROP TABLE IF EXISTS planner_inquiry_lifecycles;
