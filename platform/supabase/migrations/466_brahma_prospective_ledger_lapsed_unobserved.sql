-- Migration 466: brahma_prospective_ledger — add 'lapsed_unobserved' lifecycle_status
-- Created: 2026-07-27
--
-- Numbering note: highest numbered file across BOTH migration dirs combined is 465
-- (platform/migrations/465_classical_text_chunks_ocr_cleanup.sql and
-- platform/supabase/migrations/465_cr130_jaimini_karakamsha_yogas.sql). 466 is the
-- next free number per platform/supabase/migrations/README.md's guidance.
--
-- Context: PARIŚODHANA (Full Reconciliation + Clean Sweep) B3 item R-42/EL-58 — the
-- SQL below is the exact, previously-authored, ready migration text carried verbatim
-- from `LAPSED_UNOBSERVED_MIGRATION_SQL` in
-- platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts
-- (Elevation Campaign v2.1, Lane γ.J, EL-58). That lane's own manifest excluded
-- platform/migrations/** (charter §4 — the migrations manifest was exclusively β's),
-- so the ALTER TABLE was written but never landed as a numbered migration; it sat
-- PARKED-HONEST, "blocked_pending_migration: true", for the sweep tool's
-- brahma_prospective_ledger no-match half. PARISHODHANA_BRIEF_v1_0.md names this
-- migration as its one explicitly-authorized exception to the "no rebuild" rail.
--
-- Live-reproduced 2026-07-27 (PARIŚODHANA Phase A, prober A7, item R-42/EL-58):
--   - `brahma_prospective_ledger_lifecycle_status_check` still
--     CHECK (lifecycle_status = ANY (ARRAY['open','matched','confirmed','falsified',
--     'withdrawn'])) — no 'lapsed_unobserved' value.
--   - prediction_id 8d85d0c7-dbf0-4636-8f6a-af159aa58770 (chart
--     482012f1-710e-4a25-994a-93821f5871aa, event_class major_gain, observation_window
--     [2011-02-15,2011-03-11)) is still lifecycle_status='open' in 2026 — the exact
--     "2011-window-open-in-2026" class this widening exists to let the sweep close.
--
-- Additive only: widens an existing CHECK constraint, no data touched, no other table
-- altered, no rows written by this migration itself (prediction_lifecycle_sweep with
-- dry_run:false performs the actual UPDATE on its next invocation once this value is
-- schema-legal).
--
-- Rollback is MANUAL ONLY — migrate.ts has no DOWN/rollback mechanism (forward-apply-only,
-- tracked once per filename in _migrations_applied). To manually reverse, an operator must
-- run the block below directly, and only after confirming no rows have
-- lifecycle_status = 'lapsed_unobserved' (re-triage them first if any exist):
--
-- BEGIN;
-- ALTER TABLE public.brahma_prospective_ledger
--   DROP CONSTRAINT brahma_prospective_ledger_lifecycle_status_check;
-- ALTER TABLE public.brahma_prospective_ledger
--   ADD CONSTRAINT brahma_prospective_ledger_lifecycle_status_check
--   CHECK (lifecycle_status IN ('open', 'matched', 'confirmed', 'falsified', 'withdrawn'));
-- COMMENT ON COLUMN public.brahma_prospective_ledger.lifecycle_status IS
--   'open|matched|confirmed|falsified|withdrawn.';
-- COMMIT;

BEGIN;

ALTER TABLE public.brahma_prospective_ledger
  DROP CONSTRAINT brahma_prospective_ledger_lifecycle_status_check;
ALTER TABLE public.brahma_prospective_ledger
  ADD CONSTRAINT brahma_prospective_ledger_lifecycle_status_check
  CHECK (lifecycle_status IN
    ('open', 'matched', 'confirmed', 'falsified', 'withdrawn', 'lapsed_unobserved'));
COMMENT ON COLUMN public.brahma_prospective_ledger.lifecycle_status IS
  'open|matched|confirmed|falsified|withdrawn|lapsed_unobserved. lapsed_unobserved '
  '(EL-58, Elevation Campaign v2.1): the claimed window closed and the periodic '
  'lifecycle sweep (prediction_lifecycle_sweep, L5_mimamsa) found no candidate LEL '
  'event — itself calibration data, not a failure state.';

COMMIT;
