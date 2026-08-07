-- Migration 545: bodha_pratijna — add 'no_evidence' to status CHECK constraint
-- SHABDA-SHUDDHI lane-l2-pratijna fix.
--
-- Context: bo_pratijna v1.0 emitted 'denied' when both supporting and contradicting
-- signal lists were empty. 'denied' means "evaluated and found against"; 'no_evidence'
-- means "no information". The distinction is load-bearing for stage2_promise (which
-- uses pratijna rows as MODIFIERS, not gates — R6).
--
-- This migration widens the CHECK constraint to allow 'no_evidence'.
-- The data rebuild (bo_pratijna writer fix) converts the formerly-mislabelled 'denied'
-- rows (empty evidence) to 'no_evidence' on the next per-chart rebuild.
--
-- Idempotent: DROP CONSTRAINT IF EXISTS + ADD CONSTRAINT pattern.

BEGIN;

-- Drop the existing CHECK constraint on status (name from migration 391).
-- Using IF EXISTS so this is safe to re-apply.
ALTER TABLE bodha_pratijna
    DROP CONSTRAINT IF EXISTS bodha_pratijna_status_check;

-- Re-add the constraint with 'no_evidence' included.
ALTER TABLE bodha_pratijna
    ADD CONSTRAINT bodha_pratijna_status_check
    CHECK (status IN ('promised', 'denied', 'conditional', 'no_evidence'));

-- Update the table comment to reflect the expanded status vocabulary.
COMMENT ON TABLE bodha_pratijna IS
  'BA-P3B: Promise Register — per-event-class verdict (promised/denied/conditional/no_evidence) '
  'for each chart/ayanamsha. '
  'grade [0–10]: 0=strongly denied, 10=strongly promised; NULL when status=no_evidence. '
  'no_evidence means no signals overlapped the domain — distinct from denied (evidence against). '
  'Reads bodha_msr_signals salience + valence; keys to brahma_event_ontology. '
  'base-rate priors consumed at L4/P5B (JL-009 carry-forward — surfaced to native before anchor freeze). '
  'Writer: bo_pratijna. DAG: bo_laksana → bo_pratijna.';

COMMIT;
