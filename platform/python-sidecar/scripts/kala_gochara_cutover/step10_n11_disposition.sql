-- step10_n11_disposition.sql — WP10 runbook step 10 (plan §9): N-11 disposition
-- of `_v2 '2.0'`; digest spec 1018 retired.
--
-- Tranche 2 (PRODUCTION_TRANCHE_2_AUTHORIZED). Sheet A-3. Gate: the native
-- ruling recorded (N-11) — this script refuses to run without
-- --ruling-ref supplied to the wrapper (recorded here as a DO-block guard on a
-- session GUC the wrapper sets: SET app.n11_ruling_ref = '<ref>').
--
-- What it does:
--   (a) deletes the '2.0' residue under ka_gochara's own scope:
--       kala_gochara_windows_v2 WHERE generation='2.0', plus its build-state
--       bookkeeping rows at generation '2.0' (kala_gochara_v2_build_state) —
--       delete-under-own-scope, the writer's own replacement key. 'g3_utkarsha'
--       rows (the century writer's staging surface) are NOT touched; the v1
--       corpus in kala_gochara_windows is NEVER touched.
--   (b) retires digest spec 1018 (asset_output_digest_specs row for
--       asset_id='ka_gochara' pinning generation='2.0', spec_sha256
--       ac32bdd3…) by stamping retired_at — retained until now for the '2.0'
--       residue (plan §6.3); retirement, not deletion, per the digest-spec
--       lane's convention. If a replacement '4.0' spec has been authored by
--       the digest lane it is inserted by ITS own migration, not here.
--
-- Reversal: none (N-11 is a native ruling; plan §9 step 10 has no reversal
-- entry). The retired digest row is recoverable by clearing retired_at.

BEGIN;

-- Refuse without the recorded ruling reference.
DO $$
BEGIN
  IF current_setting('app.n11_ruling_ref', true) IS NULL THEN
    RAISE EXCEPTION 'step 10 refused: N-11 is a native ruling — set '
      'app.n11_ruling_ref to the ruling record before applying';
  END IF;
END $$;

-- Pre-disposition measurement for the evidence file.
DO $$
DECLARE
  n_residue INT;
BEGIN
  SELECT count(*) INTO n_residue FROM kala_gochara_windows_v2
   WHERE generation = '2.0';
  RAISE NOTICE 'N-11 disposition: % ''2.0'' residue rows under ruling %',
    n_residue, current_setting('app.n11_ruling_ref', true);
END $$;

DELETE FROM kala_gochara_windows_v2 WHERE generation = '2.0';
DELETE FROM kala_gochara_v2_build_state WHERE generation = '2.0';

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'ka_gochara'
   AND spec_sha256 = 'ac32bdd3e5c24abda422a61e3f9a6b51c5c67c4ac868044e465444f0de61c596'
   AND retired_at IS NULL;

-- Gate probe (§N.8): no '2.0' rows survive; the 1018 spec reads retired.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM kala_gochara_windows_v2 WHERE generation = '2.0') THEN
    RAISE EXCEPTION 'step 10 gate failed: ''2.0'' residue survives';
  END IF;
  IF EXISTS (SELECT 1 FROM asset_output_digest_specs
             WHERE asset_id = 'ka_gochara'
               AND spec_sha256 = 'ac32bdd3e5c24abda422a61e3f9a6b51c5c67c4ac868044e465444f0de61c596'
               AND retired_at IS NULL) THEN
    RAISE EXCEPTION 'step 10 gate failed: digest spec 1018 not retired';
  END IF;
END $$;

COMMIT;
