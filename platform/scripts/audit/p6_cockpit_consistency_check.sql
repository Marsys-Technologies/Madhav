-- p6_cockpit_consistency_check.sql
-- =============================================================================
-- P6: Cockpit-truth consistency sweep — read-only diagnostic.
-- Run against prod AFTER migration 232_drop_ganita_positions.sql is applied.
-- Replace '482012f1-710e-4a25-994a-93821f5871aa' with the native chart_id.
--
-- Acceptance criteria (L0_L1_CLOSURE brief §P6):
--   • All four surfaces agree per asset (stats API / registry / build cockpit / Atlas)
--   • No rows>0 asset shows building/stale/dormant/NOT MIGRATED on any surface
--   • ga_positions count_sql references chart_facts (not the dropped ganita_positions)
--   • chart_facts-partitioned assets all is_active=true (C1 hardening guard)
--   • No orphaned 'building' throughput records remain
--
-- Seed-apply hardening (C1) already in asset_registry_seed.ts:
--   • Line 1248: null target_table → skip (preserve is_active, not override to false)
--   • Lines 1368-1405: post-apply DB readback + hard assert on critical assets
-- =============================================================================

-- ── 1. Verify ga_positions now counts from chart_facts (migration 232) ────────
SELECT asset_id, target_table, left(count_sql, 90) AS count_sql_preview, is_active
FROM asset_registry
WHERE asset_id = 'ga_positions';
-- Expected: target_table='chart_facts', count_sql contains 'graha_position', is_active=true

-- ── 2. Hard check: no active asset references dropped ganita_positions ─────────
SELECT asset_id, count_sql
FROM asset_registry
WHERE (count_sql LIKE '%ganita_positions%' OR target_table = 'ganita_positions')
  AND is_active = true;
-- Expected: 0 rows (migration 232 repoints ga_positions; table dropped)

-- ── 3. chart_facts-partitioned assets are active (C1 guard) ──────────────────
SELECT asset_id, is_active, target_table
FROM asset_registry
WHERE asset_id IN ('ga_strength', 'ga_sensitive', 'ga_sade_sati', 'ga_structural');
-- Expected: all is_active=true, target_table=NULL

-- ── 4. Full L0+L1 asset surface: throughput state for native chart ────────────
SELECT
  ar.asset_id,
  ar.is_active,
  ar.target_table,
  at2.state          AS throughput_state,
  at2.rows_written,
  at2.last_built_at,
  ar.target_floor
FROM asset_registry ar
LEFT JOIN asset_throughput at2
  ON at2.asset_id = ar.asset_id
  AND at2.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
WHERE ar.layer IN ('brahmagyan', 'ganita')
  AND ar.is_active = true
ORDER BY ar.layer, ar.sort_order;
-- Expected: all rows with rows_written > 0 have throughput_state = 'lit'

-- ── 5. Orphaned 'building'/'stale' throughput check ──────────────────────────
SELECT at2.asset_id, at2.state, at2.last_error, at2.rows_written
FROM asset_throughput at2
JOIN asset_registry ar ON ar.asset_id = at2.asset_id
WHERE at2.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND at2.state IN ('building', 'stale')
  AND ar.layer IN ('brahmagyan', 'ganita')
ORDER BY at2.asset_id;
-- Expected: 0 rows (migration 229 reaped prior orphans; deriveState floor-gate handles future)
