-- 949_nirmana_l2_bo_pramana_mapa_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 948 (bo_pramana_mapa output_digest_spec) -- see
-- that migration's header for the full verified account.
-- synthesis_quality_scorecard has exactly ONE writer (bo_pramana_mapa.py;
-- confirmed via grep -- bo_samvada.py only reads the table inside a
-- CREATE VIEW definition, no INSERT/UPDATE). Declared per the DEP-ASSERT
-- precedent (880/908/909/910/927/930/939-940/941-942/943-944/946-947):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'synthesis_quality_scorecard (chart_id) -- sole writer; single-row-per-chart asset, replace_prior_scorecard (bodha_writers/_idempotency.py:484) deletes ALL prior rows for chart_id (not build_id-scoped) before inserting exactly one new row, so chart_id alone is a sufficient live natural key; scorecard_id (bare uuid4) and build_id (per-run identifier) excluded from the digest key/value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'bo_pramana_mapa'
   AND natural_key_partition IS NULL;
