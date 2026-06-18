-- Migration 315: fix ga_prashna count_sql stray leading parenthesis
-- The malformed SQL caused a parse error → false-red in cockpit.
-- Prashna FULL activation stays deferred post-L2; this just stops the false-red.
UPDATE asset_registry
SET count_sql = 'SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1'
WHERE asset_id = 'ga_prashna';
