-- Migration 045: Gate II.5 — Add nullable disclosure + B10/B11 compliance columns
-- to audit_events so AuditStepDetail can render the full audit context.
--
-- Non-destructive: adds nullable columns only. No data backfill.
-- Audit writer updates to populate these columns are a SEPARATE follow-up
-- (see POST_GATE_II_FOLLOWUPS.md FU.2 — authored in W9).
--
-- FK dependents enumerated via:
--   SELECT conname, conrelid::regclass AS dependent_table
--   FROM pg_constraint WHERE confrelid = 'audit_events'::regclass;
-- Result: (0 rows) — no FK references to audit_events.

ALTER TABLE audit_events
  ADD COLUMN IF NOT EXISTS disclosure_tier TEXT,
  ADD COLUMN IF NOT EXISTS b10_compliant BOOLEAN,
  ADD COLUMN IF NOT EXISTS b11_compliant BOOLEAN;

-- Down migration:
-- ALTER TABLE audit_events
--   DROP COLUMN IF EXISTS disclosure_tier,
--   DROP COLUMN IF EXISTS b10_compliant,
--   DROP COLUMN IF EXISTS b11_compliant;
