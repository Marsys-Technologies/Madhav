-- 684_phala_pramana_detector_unavailable.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · F2 (L4_W1_ANALYSIS_BATCH_D.md §ph_pramana, §N.8 / §N.7 item 6).
--
-- WHAT WAS WRONG
-- --------------
-- ph_pramana's LEL-match lookup compared `phala_anchors.domain` (one of the 13 canonical
-- L4 domains) against the raw `life_events.domain` column verbatim -- but `life_events.domain`
-- is a compound "<category>/<subtype>" slug (e.g. 'career/award_selection'), never a bare
-- canonical domain. The exact-string comparison could therefore never match: measured live,
-- `life_event_match` fired 0 times across the whole DB, while every past-window anchor with
-- no match fell through to `life_event_miss` -- an UNEARNED refutation. A vocabulary mismatch
-- was being read as "the predicted event did not happen."
--
-- THE FIX'S SHAPE
-- ----------------
-- (services/ph_pramana/engine.py, this same PR): normalise via
-- `brahmagyan/domain_vocabulary.py`'s existing synonym map + `life_events.category` (the
-- coarse bucket already aligned with the canonical vocabulary) before comparing. That alone
-- is not sufficient -- it would silently turn every unmatched past-window anchor into a
-- "miss" again for domains the detector never had ANY data for (e.g. 'other', 'loss', or a
-- category the synonym map genuinely cannot resolve). This migration's constraint widening is
-- what makes the engine's honest third answer -- 'detector_unavailable': the window closed and
-- the detector has NO life-event data at all in this anchor's domain, so absence-of-match
-- proves nothing -- a value the schema will actually accept.
--
-- WHY WIDEN THE CHECK CONSTRAINT RATHER THAN REUSE 'pending_observation'
-- ------------------------------------------------------------------------
-- 'pending_observation' means "the window has not closed yet -- we are still waiting to
-- observe." 'detector_unavailable' means the window HAS closed and we have no domain data to
-- check against at all. Conflating the two would hide a real gap (no LEL corpus in that
-- domain) behind a label that means something else entirely.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE phala_pramana DROP CONSTRAINT IF EXISTS phala_pramana_evidence_type_check;
ALTER TABLE phala_pramana ADD CONSTRAINT phala_pramana_evidence_type_check
  CHECK (evidence_type = ANY (ARRAY[
    'life_event_match'::text, 'life_event_miss'::text, 'proxy_indicator'::text,
    'self_report'::text, 'pending_observation'::text, 'detector_unavailable'::text
  ]));

-- Prove the widened constraint actually accepts the new value and still rejects garbage --
-- the C12 rewrite-floor discipline applied to a constraint, not just a detector query.
DO $$
DECLARE v_anchor uuid;
BEGIN
  SELECT anchor_id INTO v_anchor FROM phala_anchors LIMIT 1;
  IF v_anchor IS NULL THEN
    RAISE EXCEPTION 'migration 684 cannot run its constraint probe: phala_anchors is empty';
  END IF;

  BEGIN
    INSERT INTO phala_pramana (
      pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label,
      falsifier_text, observable_criteria_jsonb, window_status,
      derivation_ledger_jsonb, source_citation
    ) SELECT gen_random_uuid(), chart_id, v_anchor, 'detector_unavailable', 'proxy',
             'migration 684 probe row', '{}'::jsonb, 'past_window',
             '{}'::jsonb, 'migration 684 probe row'
        FROM phala_anchors WHERE anchor_id = v_anchor;
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN
      RAISE EXCEPTION
        'migration 684 FAILED: the widened constraint rejected a legitimate '
        'detector_unavailable row (%)', SQLERRM;
    END IF;
  END;

  BEGIN
    INSERT INTO phala_pramana (
      pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label,
      falsifier_text, observable_criteria_jsonb, window_status,
      derivation_ledger_jsonb, source_citation
    ) SELECT gen_random_uuid(), chart_id, v_anchor, 'not_a_real_evidence_type', 'proxy',
             'migration 684 probe row', '{}'::jsonb, 'past_window',
             '{}'::jsonb, 'migration 684 probe row'
        FROM phala_anchors WHERE anchor_id = v_anchor;
    RAISE EXCEPTION
      'migration 684 FAILED the rewrite floor test: the widened constraint accepted a garbage '
      'evidence_type -- it must still reject anything outside the six named values';
  EXCEPTION WHEN check_violation THEN
    NULL; -- expected: garbage is still rejected
  END;
END $$;
