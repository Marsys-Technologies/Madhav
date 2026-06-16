-- 232_drop_ganita_positions.sql
-- =============================================================================
-- P5: ganita_positions legacy table deprecation (RUNWAY D2).
--
-- WHY: ga_positions_writer.py writes to chart_facts exclusively (dual-write
-- removed at D2). The `ganita_positions` table is now an empty legacy table;
-- chart_facts is the sole positions store.
--
-- REVERSE-CITATION GATE RESULTS (all references reclassified):
--   brahmagyan/ganita/engine.py:write_positions()        → REMOVED (dead code, no active callers)
--   brahmagyan/ganita/graha_sthana_writer.py fallback    → REMOVED (dead code, no active callers)
--   brahma_pipeline.py run_ganita() call                 → orphaned, no callers
--   asset_registry count_sql / target_table              → REPOINTED to chart_facts (this migration)
--   tests/test_ga_idempotency.py ganita_positions test   → REPOINTED to chart_facts
--   scope_filter.test.ts target_table                    → REPOINTED to chart_facts
--   admin/foundation/page.tsx label                      → REMOVED
--   ga_positions_writer.py stale comment                 → REMOVED
--
-- Idempotent (DROP TABLE IF EXISTS). Reversible via down-block.
-- =============================================================================

BEGIN;

-- ── 1. Repoint asset_registry for ga_positions ────────────────────────────────
UPDATE asset_registry
SET
  target_table = 'chart_facts',
  count_sql    = $$SELECT count(*) AS count FROM chart_facts
WHERE chart_id = $1
  AND fact_category IN ('graha_position', 'graha_sign_attributes')$$,
  size_sql     = $$SELECT pg_total_relation_size('chart_facts')$$
WHERE asset_id = 'ga_positions';

-- ── 2. Drop legacy table ──────────────────────────────────────────────────────
DROP TABLE IF EXISTS ganita_positions CASCADE;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — recreates the table and restores registry):
--
-- BEGIN;
-- UPDATE asset_registry
-- SET target_table = 'ganita_positions',
--     count_sql    = 'SELECT count(*) FROM ganita_positions WHERE chart_id = $1',
--     size_sql     = 'SELECT pg_total_relation_size(''ganita_positions'')'
-- WHERE asset_id = 'ga_positions';
--
-- CREATE TABLE IF NOT EXISTS ganita_positions (
--   id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--   chart_id        uuid NOT NULL,
--   build_id        text NOT NULL,
--   ayanamsha_id    text NOT NULL,
--   planet          text NOT NULL,
--   tropical_longitude  double precision,
--   sidereal_longitude  double precision,
--   sign_id         integer,
--   sign_name       text,
--   nakshatra_id    integer,
--   nakshatra_name  text,
--   nakshatra_pada  integer,
--   speed_dps       double precision,
--   is_retrograde   boolean,
--   source_citation text,
--   created_at      timestamptz NOT NULL DEFAULT NOW(),
--   updated_at      timestamptz NOT NULL DEFAULT NOW(),
--   CONSTRAINT ganita_positions_unique UNIQUE (chart_id, ayanamsha_id, planet),
--   CONSTRAINT ganita_positions_nakshatra_id_check CHECK (nakshatra_id >= 1 AND nakshatra_id <= 27),
--   CONSTRAINT ganita_positions_nakshatra_pada_check CHECK (nakshatra_pada >= 1 AND nakshatra_pada <= 4),
--   CONSTRAINT ganita_positions_sign_id_check CHECK (sign_id >= 1 AND sign_id <= 12)
-- );
-- COMMIT;
-- =============================================================================
