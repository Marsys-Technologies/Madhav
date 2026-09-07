-- Migration 905: bg_sarvatobhadra_grid asset_freshness sentinel row
-- =============================================================================
-- CONDUCTOR ruling (D-NATIVE-12, overnight), issue #2393 — closing the mechanical
-- DEP-ASSERT collision #2387 authorized dispatch on but did not itself resolve.
--
-- ── ROOT CAUSE ─────────────────────────────────────────────────────────────
-- Migration 553 (SAMPŪRTI G4a) gave bg_sarvatobhadra_grid a sentinel
-- asset_throughput row (state='lit', rows_written=0) so the deliberately-empty
-- asset (ADJUDICATION-11 Part 2 — see migration 529's own header for the full
-- "why this table is empty" rationale; unchanged, not revisited here) reads
-- correctly in the cockpit/stats route. It did NOT give it a matching
-- asset_freshness row, because at the time nothing depended on its freshness
-- leg. `ka_vedha_gochara` (L3) now declares bg_sarvatobhadra_grid as a real
-- dependency (its writer genuinely tries this table first — see migration
-- 529's "ACTIVATION PATH" note) and asset_runner.py's deps_unsatisfied() gate
-- (platform/python-sidecar/pipeline/orchestrator/asset_runner.py) requires
-- BOTH asset_throughput.state='lit' AND asset_freshness.freshness_state='fresh'
-- for any non-service data dep. bg_sarvatobhadra_grid is registered
-- asset_kind='data' (correctly — it's a genuine, if empty, content table, not
-- a service), so it does not get the service-dependency bypass that lets
-- bg_panchanga's identical "monitored, intentionally empty" pattern pass with
-- no freshness row at all. Result: every ka_vedha_gochara dispatch attempt
-- fails deterministically with `DEP-ASSERT: bg_sarvatobhadra_grid(receipt:absent)`
-- (reproduced live, build run 08983928-3820-4bdb-bf77-125caecd1b2c, 19:57Z).
--
-- ── RULING (#2393; three options were on the table, none the reporting lane's
--    to take unilaterally) ────────────────────────────────────────────────────
-- (a) CHOSEN: complete migration 553's own sentinel pattern symmetrically —
--     add the matching asset_freshness row. Same table, same asset, same
--     ADJUDICATION-11 citation, no new mechanism.
-- (b) rejected: dropping the depends_on edge would mask a real, intentionally-
--     activating dependency (the writer really does query this table first).
-- (c) rejected: a gate-level empty-by-ruling carve-out touches FROZEN
--     orchestrator-adjacent code (asset_runner.py) for a single-asset problem
--     a plain data migration already solves without any code change.
-- This migration is authorized under Conductor overnight ruling authority
-- (D-NATIVE-12) as the direct, symmetric completion of an already-ruled
-- pattern; it does not reopen ADJUDICATION-11 or migration 553/529's content
-- decisions, and changes no orchestrator code.
--
-- ── WHY freshness_state='fresh' IS HONEST HERE ────────────────────────────────
-- 'fresh' does not assert "this table has current content" — it asserts "the
-- dependency-readiness question this gate exists to answer is honestly
-- answered: yes, downstream writers may proceed, because this table's empty
-- state is a settled, monitored design decision, not a missing/broken build."
-- That is exactly what asset_throughput.state='lit' already asserts for this
-- same asset via migration 553; this row asserts the identical fact on the
-- freshness leg the gate additionally checks. reasons[] discloses the
-- empty-by-ruling basis explicitly so nothing here reads as a silently
-- fabricated green (§N.8).
--
-- ── SCOPE ──────────────────────────────────────────────────────────────────
-- Global asset (scope='global' per migration 529): chart_id IS NULL,
-- partition_key = WHOLE_ASSET_PARTITION ('__whole_asset__', the sidecar's own
-- default per provenance.py). deps_unsatisfied()'s freshness lookup matches a
-- chart_id IS NULL row for any requesting chart_id (asset_runner.py's
-- `af.chart_id IS NOT DISTINCT FROM %s OR af.chart_id IS NULL` clause), so one
-- global row covers every chart's dispatch, matching migration 553's own
-- global-scope precedent.
--
-- receipt_version is stamped to the sidecar's current RECEIPT_VERSION
-- constant (provenance.py) for consistency, but is inert here: has_writer=false
-- means no real Receipt is ever computed or reconciled against this asset, so
-- reconcile_receipt()'s receipt_version-mismatch staleness check never runs
-- against this row (same "zero code change" activation path migration 529
-- already documents).
--
-- ── IDEMPOTENCY ────────────────────────────────────────────────────────────────
-- ON CONFLICT on the table's own primary key (asset_id, scope_key,
-- partition_key); safe to re-run.
-- =============================================================================

BEGIN;

-- ── Preflight guard: the throughput sentinel (migration 553) must already be live
DO $$
DECLARE _cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO _cnt
    FROM asset_throughput
    WHERE asset_id = 'bg_sarvatobhadra_grid'
      AND chart_id IS NULL
      AND state = 'lit';
    IF _cnt = 0 THEN
        RAISE EXCEPTION
            'Migration 905 preflight failed: no asset_throughput(state=''lit'') row '
            'for bg_sarvatobhadra_grid at global scope. Apply migration 553 first.';
    END IF;
END $$;

-- ── Preflight guard: content table must still have 0 rows (B.10 safety net,
--    same guard migration 553 carries — this migration must not be re-purposed
--    if a native-approved school's grid has since landed content rows)
DO $$
DECLARE _cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO _cnt FROM bg_sarvatobhadra_grid;
    IF _cnt != 0 THEN
        RAISE EXCEPTION
            'Migration 905 preflight failed: bg_sarvatobhadra_grid has % rows '
            '(expected 0 — deliberately empty per ADJUDICATION-11). If content has '
            'landed, this sentinel is obsolete; re-evaluate rather than applying.',
            _cnt;
    END IF;
END $$;

-- ── Sentinel asset_freshness row (global; chart_id IS NULL) ──────────────────
INSERT INTO asset_freshness
  (asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
VALUES (
    'bg_sarvatobhadra_grid',
    NULL,
    '__whole_asset__',
    'fresh',
    '["empty_by_ruling:ADJUDICATION-11", "conductor_ruling:#2393"]'::jsonb,
    'nirmana-provenance-receipt-v2',
    NOW()
)
ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE SET
    freshness_state = EXCLUDED.freshness_state,
    reasons         = EXCLUDED.reasons,
    receipt_version = EXCLUDED.receipt_version,
    observed_at     = NOW();

-- ── Post-condition verification ───────────────────────────────────────────────
DO $$
DECLARE _state TEXT;
BEGIN
    SELECT freshness_state
    INTO _state
    FROM asset_freshness
    WHERE asset_id = 'bg_sarvatobhadra_grid'
      AND chart_id IS NULL
      AND partition_key = '__whole_asset__';

    IF _state IS NULL THEN
        RAISE EXCEPTION
            'Migration 905 post-condition failed: no asset_freshness row found '
            'for bg_sarvatobhadra_grid after INSERT. This should not happen.';
    END IF;

    IF _state != 'fresh' THEN
        RAISE EXCEPTION
            'Migration 905 post-condition failed: asset_freshness.freshness_state=% '
            '(expected ''fresh'') for bg_sarvatobhadra_grid.', _state;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_freshness
--     WHERE asset_id = 'bg_sarvatobhadra_grid' AND chart_id IS NULL
--       AND partition_key = '__whole_asset__';
--   COMMIT;
-- =============================================================================
