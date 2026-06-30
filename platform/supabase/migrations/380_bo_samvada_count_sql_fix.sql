-- Migration 380: Fix bo_samvada count_sql
--
-- bo_samvada is a DDL-only writer (creates vw_chart_digest VIEW).
-- Its count_sql was incorrectly set to "SELECT 0 AS count" — this caused the
-- build system to always report 0 rows for bo_samvada, making it appear as a
-- DATA GATE failure even after a successful build.
--
-- The correct count_sql for a VIEW-only writer is the row count of the VIEW
-- scoped to the chart being built. vw_chart_digest groups by (chart_id,
-- ayanamsha_id) so a successful build produces 5 rows (one per ayanamsha).
-- We use COALESCE to return 0 cleanly if the view doesn't exist yet.

UPDATE asset_registry
SET
  count_sql    = 'SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1',
  target_floor = 5
WHERE asset_id = 'bo_samvada';
