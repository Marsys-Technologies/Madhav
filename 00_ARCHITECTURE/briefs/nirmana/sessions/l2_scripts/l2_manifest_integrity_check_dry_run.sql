-- Execute the current frozen definition's L2 registry integrity contracts.
-- TEMP-table only; production data is read but never persistently mutated.
-- A writable session is required for TEMP DDL; the explicit transaction always
-- ends in ROLLBACK so even the session-local objects are discarded.

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE _l2_integrity_results (
  asset_id text,
  integrity_passed boolean,
  error_note text
);

DO $l2_integrity$
DECLARE
  item record;
  passed boolean;
BEGIN
  FOR item IN
    SELECT registry.asset_id, registry.integrity_check_sql
    FROM asset_registry registry
    WHERE EXISTS (
      SELECT 1
      FROM nirmana_evidence.nirmana_elevation_campaign_definitions definition,
           jsonb_array_elements(definition.manifest -> 'assets') asset
      WHERE definition.campaign_id = 'nirmana-elevation'
        AND definition.definition_revision = 't3-2026-09-11-8b884eac'
        AND definition.definition_status = 'frozen'
        AND definition.superseded_at IS NULL
        AND asset ->> 'layer' = 'L2'
        AND asset ->> 'asset_id' = registry.asset_id
    )
      AND registry.integrity_check_sql IS NOT NULL
    ORDER BY registry.asset_id
  LOOP
    BEGIN
      EXECUTE item.integrity_check_sql INTO passed;
      INSERT INTO _l2_integrity_results VALUES (item.asset_id, passed, NULL);
    EXCEPTION WHEN OTHERS THEN
      INSERT INTO _l2_integrity_results VALUES (item.asset_id, NULL, SQLERRM);
    END;
  END LOOP;
END;
$l2_integrity$;

SELECT asset_id,
  CASE WHEN error_note IS NOT NULL THEN 'ERROR'
       WHEN integrity_passed IS TRUE THEN 'PASS'
       WHEN integrity_passed IS FALSE THEN 'FAIL'
       ELSE 'NULL-RESULT' END AS verdict,
  error_note
FROM _l2_integrity_results
ORDER BY (error_note IS NOT NULL) DESC, (integrity_passed IS NOT TRUE) DESC, asset_id;

WITH denominator AS (
  SELECT count(*) AS assets
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions definition,
       jsonb_array_elements(definition.manifest -> 'assets') asset
  WHERE definition.campaign_id = 'nirmana-elevation'
    AND definition.definition_revision = 't3-2026-09-11-8b884eac'
    AND definition.definition_status = 'frozen'
    AND definition.superseded_at IS NULL
    AND asset ->> 'layer' = 'L2'
)
SELECT
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS TRUE) AS pass_count,
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS FALSE) AS fail_count,
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS NULL) AS null_result_count,
  count(*) FILTER (WHERE error_note IS NOT NULL) AS error_count,
  count(*) AS total_checked,
  denominator.assets AS denominator
FROM _l2_integrity_results
CROSS JOIN denominator
GROUP BY denominator.assets;

ROLLBACK;
