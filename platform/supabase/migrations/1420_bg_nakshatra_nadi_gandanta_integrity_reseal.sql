-- Migration 1420: reseal bg_nakshatra integrity_check_sql for MC v.34 nāḍī and Aśvinī gaṇḍānta fixes.
-- Created: 2026-11-22
--
-- Migration 625 pinned every column of reference_nakshatra (44 columns),
-- reference_nakshatra_pada (16 columns), and reference_nakshatra_matrix (9 columns)
-- so any count-preserving semantic mutation fails closed until explicitly resealed.
--
-- Two primary-text defects in brahmagyan/l0_nakshatra.py are corrected here:
--   1. nadi on 10 of the 27 nakshatras (#4 Rohini, #6 Ardra, #10 Magha,
--      #12 Uttara Phalguni, #16 Vishakha, #18 Jyeshtha, #22 Shravana,
--      #24 Shatabhisha, #26 Uttara Bhadrapada, #27 Revati) per Muhurta
--      Chintamani Vivaha-prakarana v.34 (muhurta_chintamani:PG96:C2-PG97:C1).
--   2. is_gandanta on #1 Ashwini (False -> True), per BPHS Ch. 92 sl. 3
--      (bphs:PG1018:C1), Jataka Parijata VI.59 (jataka_parijata:PG632:C1), and
--      brahmagyan/gandanta.py.
--
-- Only reference_nakshatra changes; reference_nakshatra_pada (09eeb0e2...) and
-- reference_nakshatra_matrix (143ce4a3...) hashes are unchanged. Registry metadata
-- only; the governed rebuild updates reference_nakshatra and downstream tables.
-- Migration 625 is applied and is never edited (CLAUDE.md §N.4).
-- Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $m1420$
DECLARE
  expected_before constant text := '3a1bc82c78ed3f79aae62d18a4d29f0e';
  expected_after  constant text := 'c17250e197373669b61e56baaf487db0';
  prior_pin constant text := 'bbbf686205c208efe0a7f6dbd192b27e63931a9b37f442d194d8d17b72ee3fde';
  new_pin   constant text := '57279a04f69f3b7672020bc20b0577c60db76b11c8cc45b74fac30a131f2aa1c';
  changed_rows integer := 0;
  current_sql text;
  updated_sql text;
BEGIN
  SELECT integrity_check_sql INTO current_sql
    FROM public.asset_registry WHERE asset_id = 'bg_nakshatra' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1420 refuses: bg_nakshatra is not in asset_registry';
  END IF;
  IF current_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1420 refuses: bg_nakshatra has no integrity_check_sql';
  END IF;
  IF md5(current_sql) = expected_after THEN
    RETURN;
  END IF;
  IF md5(current_sql) IS DISTINCT FROM expected_before THEN
    RAISE EXCEPTION '1420: expected migration 625 integrity check (%), found %',
      expected_before, md5(current_sql);
  END IF;

  updated_sql := replace(current_sql, prior_pin, new_pin);
  IF md5(updated_sql) IS DISTINCT FROM expected_after THEN
    RAISE EXCEPTION '1420: resealed integrity check did not match expected digest (got %)',
      md5(updated_sql);
  END IF;

  UPDATE public.asset_registry
     SET integrity_check_sql = updated_sql
   WHERE asset_id = 'bg_nakshatra';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1420 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.asset_registry
    WHERE asset_id = 'bg_nakshatra'
      AND md5(integrity_check_sql) = expected_after
  ) THEN
    RAISE EXCEPTION 'migration 1420 postflight registry mismatch';
  END IF;
END
$m1420$;
