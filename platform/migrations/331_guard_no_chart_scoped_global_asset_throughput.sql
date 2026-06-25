-- Migration 331: Guard against chart-scoped throughput rows for global assets.
--
-- WHY: asset_throughput.chart_id must be NULL for scope='global' assets (bg_*).
-- A build_run with chart_id set can include global assets in its plan; if the
-- orchestrator runner passes that chart_id to run_asset() for a global asset it
-- inserts a chart-scoped row that shadows the correct global row in the stats
-- ORDER BY (chart_id=$1) DESC NULLS LAST query, blanking the cockpit bars.
--
-- FIX IN CODE: runner.py now resolves effective_chart_id=None for global assets.
-- THIS TRIGGER: belt-and-suspenders DB-level guard — any INSERT or UPDATE that
-- would create a chart-scoped row for a global asset raises immediately, making
-- the invariant unbypassable regardless of the calling path.

CREATE OR REPLACE FUNCTION _assert_throughput_global_no_chart_id()
RETURNS TRIGGER AS $$
DECLARE
  asset_scope text;
BEGIN
  SELECT scope INTO asset_scope
    FROM asset_registry
   WHERE asset_id = NEW.asset_id;

  IF asset_scope = 'global' AND NEW.chart_id IS NOT NULL THEN
    RAISE EXCEPTION
      'asset_throughput integrity violation: global asset "%" must have chart_id IS NULL, got chart_id=%',
      NEW.asset_id, NEW.chart_id
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Fire on INSERT and on any UPDATE that touches chart_id (SET chart_id = ...).
-- Using FOR EACH ROW so we check every affected row individually.
DROP TRIGGER IF EXISTS trg_asset_throughput_no_chart_scoped_global ON asset_throughput;
CREATE TRIGGER trg_asset_throughput_no_chart_scoped_global
BEFORE INSERT OR UPDATE OF chart_id ON asset_throughput
FOR EACH ROW
EXECUTE FUNCTION _assert_throughput_global_no_chart_id();
