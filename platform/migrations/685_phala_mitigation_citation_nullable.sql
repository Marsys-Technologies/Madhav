-- 685_phala_mitigation_citation_nullable.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · F-3 (L4_W1_ANALYSIS_BATCH_C.md §3.5, hard-floor violation).
--
-- WHAT WAS WRONG
-- --------------
-- phala_mitigation.classical_citation was NOT NULL with no schema path to an honest null.
-- The engine's fallback (services/ph_pratikara/engine.py, this same PR) therefore invented a
-- plausible-sounding generic citation -- 'Brihat Parashara Hora Shastra — Upaya chapter' --
-- whenever no prescription carried a real one. Measured live: 100% of 1,277 rows (both
-- charts) on the fabricated string, because the empty-programme defect (F-2, fixed separately
-- in commit 5f097e738 pending its rerun) meant `prescriptions` was always [] to begin with.
--
-- THE PROPAGATION THE FABRICATION ENABLED
-- ----------------------------------------
-- kala_upaya_diagnosis.ts's assignEfficacyTier() already keys `classically_attested` off
-- `citation !== null` -- honest logic, wired to a column that could never actually be null.
-- phala_mitigation_map.ts's `all_cited` computation is fixed alongside this migration (F-5,
-- same PR) to key on classical_citation alone rather than an unrelated always-populated field.
-- Both consumers were only ever wrong because this column had no way to tell them the truth.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE phala_mitigation ALTER COLUMN classical_citation DROP NOT NULL;

-- Prove the column actually accepts NULL now -- C12's rewrite-floor discipline applied to a
-- constraint relaxation, not just a detector query.
DO $$
DECLARE v_mitigation uuid;
BEGIN
  SELECT mitigation_id INTO v_mitigation FROM phala_mitigation LIMIT 1;
  IF v_mitigation IS NULL THEN
    RAISE EXCEPTION 'migration 685 cannot run its constraint probe: phala_mitigation is empty';
  END IF;

  BEGIN
    UPDATE phala_mitigation SET classical_citation = NULL WHERE mitigation_id = v_mitigation;
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN
      RAISE EXCEPTION
        'migration 685 FAILED: classical_citation still rejects NULL after DROP NOT NULL (%)',
        SQLERRM;
    END IF;
  END;
END $$;
