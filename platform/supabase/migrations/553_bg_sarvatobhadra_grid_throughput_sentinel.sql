-- Migration 553: bg_sarvatobhadra_grid asset_throughput sentinel row
-- =============================================================================
-- SAMPŪRTI G4a — L0b lane · sampurti/l0b-grid · 2026-08-10
--
-- ROOT CAUSE (R16 — every status claim cites the exact query):
--
-- bg_sarvatobhadra_grid was registered in migration 529 (applied 2026-08-02,
-- _migrations_applied id=389) with has_writer=false and target_floor=0.
-- The table exists with 0 rows — as designed per ADJUDICATION-11 Part 2
-- (migration 529 comment: "DELIBERATELY EMPTY").
--
-- The global_runner (pipeline/orchestrator/global_runner.py _run_asset_writer())
-- returns "deferred" (line 158) for any asset with no registered writer and
-- NEVER calls _upsert_asset_throughput_global() in that code path:
--
--   writer_cls = get_writer(asset_id)   -- returns None for has_writer=false
--   if writer_cls is None:
--       logger.info("[global_build] DEFERRED: ...")
--       return "deferred"               -- exits WITHOUT touching asset_throughput
--
-- Consequence (verified by exact query):
--   SELECT state FROM asset_throughput
--   WHERE asset_id = 'bg_sarvatobhadra_grid' AND chart_id IS NULL;
--   → 0 rows
--
-- bg_sarvatobhadra_grid has NO asset_throughput row, making it invisible to the
-- cockpit/stats route even though its designed state (0 rows, deliberately empty)
-- is correct by ADJUDICATION-11 intent.
--
-- ── WHY CONTENT ROWS ARE NOT ADDED ──────────────────────────────────────────
-- B.1/B.10 compliance: The SBC (Sarvatobhadra Chakra) grid geometry genuinely
-- varies by Jyotish tradition. Corpus search produced 8 sarvatobhadra hits, all
-- noise except one passing [MEDIUM] mention that cites the technique exists but
-- not its geometry. Neither Jyotish Sara Sangraha nor Narada Samhita is held
-- in the repo's classical_texts. Selecting ONE grid as "the" classical grid
-- is an interpretive, school-selecting act — seating it as an L0 base fact is
-- exactly the B.1 structural_prior-masquerading-as-fact violation the
-- DATA-HONESTY RAIL exists to prevent. Content rows require:
--   (a) native approval of which school_tag's grid to use; and
--   (b) source-verification: grid cells read from a held classical text via the
--       SELECT-from-classical_text_chunks discipline (per migration 528's own
--       precondition).
-- Neither condition is met. This migration ONLY repairs monitoring visibility.
--
-- ── ACTIVATION PATH (zero code change required — per migration 529) ──────────
-- A future native-approved, source-verified school's grid activates the
-- ka_vedha_gochara DB-sourced-grid-first path automatically when rows land
-- under a school_tag. No writer code change is needed.
--
-- ── PRECEDENT ────────────────────────────────────────────────────────────────
-- bg_panchanga (has_writer=false, scope='global'):
--   state='lit', rows_written=0, last_built_at=2026-06-18
--   (set by the orchestrator's global_runner after a build run; the panchanga
--   engine is a service asset whose "0 rows" is also correct by design).
-- This migration applies the same monitoring-sentinel pattern for
-- bg_sarvatobhadra_grid: state='lit', rows_written=0 = "monitored,
-- intentionally empty" — not a build failure.
--
-- ── IDEMPOTENCY ────────────────────────────────────────────────────────────────
-- ON CONFLICT ... DO UPDATE mirrors the _upsert_asset_throughput_global()
-- function signature. Safe to re-run.
-- =============================================================================

BEGIN;

-- ── Preflight guard: asset_registry row must exist (migration 529 must be applied)
DO $$
DECLARE _cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO _cnt
    FROM asset_registry
    WHERE asset_id = 'bg_sarvatobhadra_grid'
      AND has_writer = false
      AND target_floor = 0
      AND scope = 'global';
    IF _cnt = 0 THEN
        RAISE EXCEPTION
            'Migration 553 preflight failed: bg_sarvatobhadra_grid not found in '
            'asset_registry with has_writer=false, target_floor=0, scope=''global''. '
            'Apply migration 529 first.';
    END IF;
END $$;

-- ── Preflight guard: content table must exist and have 0 rows (B.10 safety net)
DO $$
DECLARE _cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO _cnt FROM bg_sarvatobhadra_grid;
    IF _cnt != 0 THEN
        RAISE EXCEPTION
            'Migration 553 preflight failed: bg_sarvatobhadra_grid has % rows '
            '(expected 0 — deliberately empty per ADJUDICATION-11). '
            'Content rows must not be present at this migration point; '
            'their addition requires native approval + source verification (B.1/B.10).',
            _cnt;
    END IF;
END $$;

-- ── Sentinel asset_throughput row (global; chart_id IS NULL) ─────────────────
-- state='lit': signals "monitoring-visible, intentionally empty"
-- rows_written=0: correct — this asset is deliberately empty by design
-- Matches the partial-index unique constraint:
--   UNIQUE (asset_id) WHERE chart_id IS NULL   [asset_throughput_global_idx]
INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, last_built_at)
VALUES ('bg_sarvatobhadra_grid', NULL, 'lit', 0, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET
    state         = 'lit',
    rows_written  = 0,
    last_built_at = NOW(),
    last_error    = NULL;

-- ── Post-condition verification ───────────────────────────────────────────────
DO $$
DECLARE _state TEXT; _rows INTEGER;
BEGIN
    SELECT state, rows_written
    INTO _state, _rows
    FROM asset_throughput
    WHERE asset_id = 'bg_sarvatobhadra_grid'
      AND chart_id IS NULL;

    IF _state IS NULL THEN
        RAISE EXCEPTION
            'Migration 553 post-condition failed: no asset_throughput row found '
            'for bg_sarvatobhadra_grid after INSERT. This should not happen.';
    END IF;

    IF _state != 'lit' THEN
        RAISE EXCEPTION
            'Migration 553 post-condition failed: asset_throughput.state=% '
            '(expected ''lit'') for bg_sarvatobhadra_grid.', _state;
    END IF;

    IF _rows != 0 THEN
        RAISE EXCEPTION
            'Migration 553 post-condition failed: asset_throughput.rows_written=% '
            '(expected 0) for bg_sarvatobhadra_grid.', _rows;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_throughput
--     WHERE asset_id = 'bg_sarvatobhadra_grid' AND chart_id IS NULL;
--   COMMIT;
-- =============================================================================
