-- 687_phala_mitigation_source_id.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · F-6 (L4_W1_ANALYSIS_BATCH_C.md §3.5, partial).
--
-- phala_mitigation had no column carrying the classical SOURCE identifier (e.g. 'BPHS') --
-- only the free-text citation string. bo_upaya's classical_sources_jsonb already carries
-- {"source_id": ..., "citation": ...} together, and source_id is populated on 135/135 rows
-- across all three charts (verified live), but the writer (services/ph_pratikara/engine.py,
-- pipeline/orchestrator/writers/ph_pratikara.py, this same PR) only ever read `.citation`.
--
-- NOTE ON SCOPE: F-6 also named `estimated_time_minutes_daily` / `phase_duration_days` as
-- unpropagated real data. Re-verified live before starting this migration (D-CND-16: derive,
-- never restate a finding): both are 100% NULL on ALL THREE charts, including the damaged one
-- -- there is no real data behind either column to propagate. That half of F-6 does not apply
-- as originally framed; not attempted here, and not a silent gap -- there is nothing to wire.
-- `classical_sources_jsonb.source_id` IS genuinely populated and is what this migration adds.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE phala_mitigation ADD COLUMN IF NOT EXISTS source_id text;

-- Prove the column exists and accepts a real value -- cheap, but matches this campaign's
-- "prove the schema change actually works" discipline for every additive migration this session.
DO $$
DECLARE v_mitigation uuid;
BEGIN
  SELECT mitigation_id INTO v_mitigation FROM phala_mitigation LIMIT 1;
  IF v_mitigation IS NULL THEN
    -- Empty table is a legitimate state (fresh chart, ph_pratikara not yet run) -- not a
    -- migration failure, nothing to probe against.
    RETURN;
  END IF;

  BEGIN
    UPDATE phala_mitigation SET source_id = 'BPHS' WHERE mitigation_id = v_mitigation;
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN
      RAISE EXCEPTION
        'migration 687 FAILED: source_id rejected a legitimate value (%)', SQLERRM;
    END IF;
  END;
END $$;
