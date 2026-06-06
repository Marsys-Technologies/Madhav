-- Migration 170: layer_approvals
-- Cockpit v2 — sign-off ledger per chart × layer.
-- UNIQUE constraint ensures only one active (non-revoked) approval per chart×layer.
-- Applied: 2026-06-06

BEGIN;

CREATE TABLE IF NOT EXISTS layer_approvals (
  approval_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  layer                   text NOT NULL CHECK (layer IN ('brahmagyan','ganita','bodha','kala','phala','mimamsa')),
  approver_uid            text NOT NULL,
  approver_role           text NOT NULL CHECK (approver_role IN ('super_admin','acharya')),
  approved_at             timestamptz DEFAULT now(),
  revoked_at              timestamptz,
  revoked_by              text,
  revocation_reason       text,
  stats_snapshot          jsonb NOT NULL,
  amber_acknowledgements  jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT exclude_overlapping_active UNIQUE NULLS NOT DISTINCT (chart_id, layer, revoked_at)
);

CREATE INDEX IF NOT EXISTS idx_layer_approvals_chart_layer
  ON layer_approvals(chart_id, layer)
  WHERE revoked_at IS NULL;

COMMIT;
