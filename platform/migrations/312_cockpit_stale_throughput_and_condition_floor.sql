-- Migration 312: Fix build_state_stale for L1 ga_* assets + ga_condition count_sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Root causes:
--
-- (A) 5 ga_* per-chart assets have state='stale' in asset_throughput for chart
--     482012f1-710e-4a25-994a-93821f5871aa. They were marked stale by the
--     orchestrator after a reload cycle but their data is present and correct.
--     Fix: UPDATE state = 'lit'.
--
-- (B) ga_nakshatra has no throughput record for this chart (writer was absent
--     from the registry until recently). Cockpit sees tp=NULL → build_state_stale.
--     Fix: INSERT a record with measured count.
--
-- (C) ga_condition count_sql was never updated from migration 252's simple version
--     (counts only ga_condition_composite → 45 rows) to the combined version that
--     also counts chart_facts graha_avastha_%_per_varga rows. Migration 310 set
--     target_floor = 2880 (combined measure) without updating count_sql, leaving
--     the cockpit showing "45 / 2880" — a nearly-empty bar for a fully-built asset.
--     Combined count verified: 45 (composite) + 2835 (per-varga avastha) = 2880.
--     Fix: UPDATE count_sql to combined form matching the seed.
--
-- L0 global stale (bg_dignity_reference, bg_nakshatra_medical, bg_transit_engine)
-- is fixed in the stats route (DISTINCT ON with chart_id=$1 OR IS NULL) — no SQL.
-- ─────────────────────────────────────────────────────────────────────────────

-- (A) Flip stale L1 per-chart throughput records to lit
UPDATE asset_throughput
SET state = 'lit'
WHERE asset_id IN (
    'ga_sade_sati',
    'ga_structural',
    'ga_transit_anchors',
    'ga_vastu',
    'ga_yoga'
  )
  AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND state = 'stale';

-- (B) Insert missing ga_nakshatra throughput record (1,802 rows measured 2026-06-18)
INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES (
    'ga_nakshatra',
    '482012f1-710e-4a25-994a-93821f5871aa',
    'lit',
    1802,
    1802,
    NOW()
)
ON CONFLICT DO NOTHING;

-- (C) Fix ga_condition count_sql to combined form (composite + per-varga avastha).
-- target_floor = 2880 is correct (set by migration 310); only count_sql needs fixing.
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1) + (SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE ''graha_avastha_%_per_varga'') AS count'
WHERE asset_id = 'ga_condition';
