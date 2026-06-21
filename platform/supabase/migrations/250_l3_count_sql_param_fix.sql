-- Migration 250: Fix L3 count_sql placeholder binding
-- Root cause: 5 ka_* artifact rows in asset_registry were registered with the
-- literal string $$CHART_ID$$ in count_sql instead of the $1 parameterized
-- binding that the /api/cockpit/stats route expects. The stats route binds
-- $1 = chart_id; with $$CHART_ID$$ postgres receives the string "CHART_ID"
-- which is not a valid UUID → "invalid input syntax for type uuid: CHART_ID".
-- Fix: replace the placeholder with $1 on all 5 affected rows.
-- Idempotent: UPDATE is safe to re-run; correct rows unchanged.

BEGIN;

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM kala_activation WHERE chart_id = $1'
 WHERE asset_id = 'ka_kalasutra'
   AND count_sql LIKE '%$$CHART_ID$$%';

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1'
 WHERE asset_id = 'ka_vighnakara'
   AND count_sql LIKE '%$$CHART_ID$$%';

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM kala_darshana WHERE chart_id = $1'
 WHERE asset_id = 'ka_kala_darshana'
   AND count_sql LIKE '%$$CHART_ID$$%';

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM kala_jivana_parva WHERE chart_id = $1'
 WHERE asset_id = 'ka_jivana_parva'
   AND count_sql LIKE '%$$CHART_ID$$%';

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM kala_bhavishya WHERE chart_id = $1'
 WHERE asset_id = 'ka_bhavishya_lekha'
   AND count_sql LIKE '%$$CHART_ID$$%';

COMMIT;

-- DOWN (manual rollback only):
-- BEGIN;
-- UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM kala_activation WHERE chart_id = $$CHART_ID$$' WHERE asset_id = 'ka_kalasutra';
-- UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $$CHART_ID$$' WHERE asset_id = 'ka_vighnakara';
-- UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM kala_darshana WHERE chart_id = $$CHART_ID$$' WHERE asset_id = 'ka_kala_darshana';
-- UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM kala_jivana_parva WHERE chart_id = $$CHART_ID$$' WHERE asset_id = 'ka_jivana_parva';
-- UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM kala_bhavishya WHERE chart_id = $$CHART_ID$$' WHERE asset_id = 'ka_bhavishya_lekha';
-- COMMIT;
