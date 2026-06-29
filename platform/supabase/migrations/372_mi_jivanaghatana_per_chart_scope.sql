-- 372_mi_jivanaghatana_per_chart_scope.sql
-- Reclassify mi_jivanaghatana (L5 Mīmāṃsā) from global → per-chart scope.
--
-- mi_jivanaghatana writes mimamsa_event_provenance, whose primary key is
-- (chart_id, event_id) — i.e. a PER-CHART table. It was mis-registered with
-- scope='global', and both its build-path DELETE (writer) and its clear-path
-- DELETE (deriveDeleteSqlFromCountSql, derived from count_sql) were unscoped.
-- Result: building/clearing any chart wiped EVERY chart's provenance. Benign in
-- the single-native era, data-loss the moment a second chart is built.
--
-- Two coordinated fixes (writer code re-scopes its own DELETE + read separately):
--   1. scope     : 'global' → 'per_chart'  (correct layer/scope semantics)
--   2. count_sql : add WHERE chart_id = $1  (chart-scoped cockpit count AND, via
--                  deriveDeleteSqlFromCountSql, a chart-scoped clear-path DELETE)
--
-- Both are idempotent UPDATEs.

-- ── mi_jivanaghatana: scope ───────────────────────────────────────────────────
UPDATE asset_registry
SET scope = 'per_chart'
WHERE asset_id = 'mi_jivanaghatana';

-- ── mi_jivanaghatana: count_sql (chart-scoped) ───────────────────────────────
UPDATE asset_registry
SET count_sql = $sql$SELECT count(*) FROM mimamsa_event_provenance WHERE chart_id = $1$sql$
WHERE asset_id = 'mi_jivanaghatana';
