-- 686_phala_sodhana_ceiling_inputs_degenerate.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · F-13 (L4_W1_ANALYSIS_BATCH_C.md §1.5(b), §N.8).
--
-- detect_confidence_degenerate (ph_sodhana) guards confidence_high's chart-wide variance --
-- but the G-LADDER ceiling it protects is computed from TWO OTHER inputs
-- (dasha_consensus_count, ayanamsha_robustness), and confidence_high can vary for reasons
-- unrelated to those two (measured: 10 distinct confidence_high values on the canonical
-- chart, correctly passing the existing check) WHILE dasha_consensus_count/
-- ayanamsha_robustness are simultaneously frozen at one (0, 3) pair across all 139 anchors.
-- A detector that watches confidence_high cannot see that -- it is watching a proxy of the
-- claim ("the ceiling is a meaningful per-anchor calibration"), not the claim itself.
--
-- This migration widens phala_sodhana_anomaly_type_check to accept the new detector
-- (services/ph_sodhana/engine.py, this same PR) ships under: 'ceiling_inputs_degenerate'.
-- Rewrite-floor clean: it is an ADDITION alongside 'confidence_degenerate', not a
-- replacement -- the existing detector's own behaviour is untouched.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE phala_sodhana DROP CONSTRAINT IF EXISTS phala_sodhana_anomaly_type_check;
ALTER TABLE phala_sodhana ADD CONSTRAINT phala_sodhana_anomaly_type_check
  CHECK (anomaly_type = ANY (ARRAY[
    'confidence_inflation'::text, 'magnitude_drift'::text, 'falsifier_absent'::text,
    'ledger_gap'::text, 'layer_leakage'::text, 'confidence_degenerate'::text,
    'ceiling_inputs_degenerate'::text
  ]));

-- Prove the widened constraint actually accepts the new value and still rejects garbage.
DO $$
DECLARE v_anchor uuid; v_chart uuid;
BEGIN
  SELECT anchor_id, chart_id INTO v_anchor, v_chart FROM phala_anchors LIMIT 1;
  IF v_anchor IS NULL THEN
    RAISE EXCEPTION 'migration 686 cannot run its constraint probe: phala_anchors is empty';
  END IF;

  BEGIN
    INSERT INTO phala_sodhana (
      sodhana_id, chart_id, anchor_id, anomaly_type, anomaly_severity,
      detected_field, expected_value_text, observed_value_text,
      recommendation_text, derivation_ledger_jsonb, source_citation
    ) VALUES (
      gen_random_uuid(), v_chart, v_anchor, 'ceiling_inputs_degenerate', 'major',
      'migration 686 probe', 'probe', 'probe',
      'migration 686 probe row', '{}'::jsonb, 'migration 686 probe row'
    );
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN
      RAISE EXCEPTION
        'migration 686 FAILED: the widened constraint rejected a legitimate '
        'ceiling_inputs_degenerate row (%)', SQLERRM;
    END IF;
  END;

  BEGIN
    INSERT INTO phala_sodhana (
      sodhana_id, chart_id, anchor_id, anomaly_type, anomaly_severity,
      detected_field, expected_value_text, observed_value_text,
      recommendation_text, derivation_ledger_jsonb, source_citation
    ) VALUES (
      gen_random_uuid(), v_chart, v_anchor, 'not_a_real_anomaly_type', 'major',
      'migration 686 probe', 'probe', 'probe',
      'migration 686 probe row', '{}'::jsonb, 'migration 686 probe row'
    );
    RAISE EXCEPTION
      'migration 686 FAILED the rewrite floor test: the widened constraint accepted a '
      'garbage anomaly_type -- it must still reject anything outside the seven named values';
  EXCEPTION WHEN check_violation THEN
    NULL; -- expected: garbage is still rejected
  END;
END $$;
