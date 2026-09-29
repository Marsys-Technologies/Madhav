-- step03_guard_n6a.sql — WP10 runbook step 3 (plan §9): generation guard + N-6a.
--
-- Tranche 1 (PRODUCTION_TRANCHE_1_AUTHORIZED). Sheet A-2.
--
-- (a) Guard trigger keyed on (table, generation) — never asset_id-keyed —
--     refusing DELETE/UPDATE/TRUNCATE of generation 'v1' and '3.0' rows on
--     kala_gochara_windows. '4.0' writes pass. Composes with migration 540's
--     asset_id-keyed build_protected_assets pair; does not replace it.
--     build_protected_assets is re-seeded (idempotent) for the sweep asset.
-- (b) N-6a: the century writer (ka_gochara_v3_century_materialize) is set
--     is_active=false. Reversible; nothing deleted; g3_* staging preserved.
--     Disclosed consequence (plan §9 step 3): from here the century writer's
--     production DELETE+INSERT (ka_gochara_v3_century_materialize.py:2257)
--     would fail loudly if it ever ran — the hold made structural rather than
--     procedural, which is why the lifecycle flip belongs in the same step as
--     the guard.
--     NOTE (remainder brief §7.A, correcting a withdrawn stream record): N-14
--     does NOT require the century writer to run. The '4.0' candidate is
--     built by ka_gochara (N-5); '3.0' is the rollback surface and is never
--     regenerated (plan §4.7). N-6a therefore blocks nothing the sheet rules
--     for.
--
-- Gate (runbook): attempted DELETE/UPDATE/TRUNCATE on 'v1'/'3.0' rows fail
-- loudly; '4.0' writes pass; the century cannot be dispatched (is_active
-- false). Exercised by tests/l3/gochara/test_wp10_cutover.py on the
-- disposable database.
--
-- Reversal: step03_reversal.sql (DROP trigger + restore is_active; both
-- recorded in evidence).
--
-- Idempotent: CREATE OR REPLACE FUNCTION + DROP TRIGGER IF EXISTS + CREATE
-- TRIGGER; UPDATE is a fixed-point write.

BEGIN;

-- (a) the (table, generation)-keyed guard -------------------------------------

CREATE OR REPLACE FUNCTION kala_gochara_generation_guard()
RETURNS TRIGGER AS $$
DECLARE
  guard_generation TEXT;
BEGIN
  -- Per-session override reserved for the release authority, same convention
  -- as migration 540's app.allow_protected_sweep_rewrite.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  IF TG_OP = 'TRUNCATE' THEN
    -- TRUNCATE has no row scope: refuse whenever the table holds any
    -- protected-generation row.
    IF EXISTS (SELECT 1 FROM kala_gochara_windows
               WHERE generation IN ('v1', '3.0')) THEN
      RAISE EXCEPTION
        'GOCHARA GENERATION GUARD: TRUNCATE on kala_gochara_windows refused — '
        'the table holds protected generations (v1, 3.0). Set '
        'app.allow_protected_sweep_rewrite=on for this session to override '
        '(release authority only).';
    END IF;
    RETURN NULL;
  END IF;

  guard_generation := OLD.generation;
  IF guard_generation IN ('v1', '3.0') THEN
    RAISE EXCEPTION
      'GOCHARA GENERATION GUARD: % on kala_gochara_windows refused for '
      'protected generation % (row id %, chart %). Set '
      'app.allow_protected_sweep_rewrite=on for this session to override '
      '(release authority only).',
      TG_OP, guard_generation, OLD.id, OLD.chart_id;
  END IF;
  -- UPDATE may not re-label a row INTO a protected generation either.
  IF TG_OP = 'UPDATE' AND NEW.generation IN ('v1', '3.0')
     AND NEW.generation IS DISTINCT FROM OLD.generation THEN
    RAISE EXCEPTION
      'GOCHARA GENERATION GUARD: UPDATE may not re-label row id % into '
      'protected generation %.', OLD.id, NEW.generation;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION kala_gochara_generation_guard() IS
  'WP10 step 3 (plan §9): (table, generation)-keyed guard on '
  'kala_gochara_windows — refuses DELETE/UPDATE/TRUNCATE touching generations '
  '''v1''/''3.0'', and UPDATE re-labelling into them. Keyed on generation, '
  'never asset_id. ''4.0'' writes pass. Override: session GUC '
  'app.allow_protected_sweep_rewrite=on (release authority only).';

DROP TRIGGER IF EXISTS trg_kgw_generation_guard_row ON kala_gochara_windows;
CREATE TRIGGER trg_kgw_generation_guard_row
  BEFORE DELETE OR UPDATE ON kala_gochara_windows
  FOR EACH ROW EXECUTE FUNCTION kala_gochara_generation_guard();

DROP TRIGGER IF EXISTS trg_kgw_generation_guard_truncate ON kala_gochara_windows;
CREATE TRIGGER trg_kgw_generation_guard_truncate
  BEFORE TRUNCATE ON kala_gochara_windows
  FOR EACH STATEMENT EXECUTE FUNCTION kala_gochara_generation_guard();

-- build_protected_assets re-seed (idempotent; the 540 pair remains in force).
-- Seeded for every chart that currently holds v1 rows, so the asset-keyed
-- layer and the generation-keyed layer cover the same corpus.
INSERT INTO build_protected_assets (asset_id, chart_id, reason)
SELECT 'ka_gochara_sweep', w.chart_id,
       'WP10 step 3 re-seed: v1 corpus protected under the (table, generation) '
       'guard (trg_kgw_generation_guard_row) in addition to this asset-keyed '
       'layer (migration 540).'
FROM (SELECT DISTINCT chart_id FROM kala_gochara_windows WHERE generation = 'v1') w
ON CONFLICT (asset_id, chart_id) DO NOTHING;

-- (b) N-6a: century lifecycle hold ------------------------------------------------

UPDATE asset_registry
   SET is_active = false
 WHERE asset_id = 'ka_gochara_v3_century_materialize';

-- Gate probe inside the same transaction (§N.8: never trust a silent no-op).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM asset_registry
                 WHERE asset_id = 'ka_gochara_v3_century_materialize'
                   AND is_active = false) THEN
    RAISE EXCEPTION 'step 3 gate failed: ka_gochara_v3_century_materialize is_active is not false';
  END IF;
END $$;

COMMIT;
