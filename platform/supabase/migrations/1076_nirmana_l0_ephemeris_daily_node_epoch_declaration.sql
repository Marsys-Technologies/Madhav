-- Migration 1076: ephemeris_daily — declare node frame + epoch on the row.
-- L0 repair item 7 (native-authorized, KALA_DELEGATED_DECISIONS_v1_0.md D-E item 7;
-- Gochara N-4a, GOCHARA_RULING_SHEET_v1_0.md on origin/l3/gochara-elevation:
-- "node_mode and epoch_convention declared on the ephemeris_daily row beside
-- ayanamsha_id by additive migration, no rebuild").
--
-- WHY: ephemeris_daily's Rahu/Ketu rows are computed via swe_id=11 = SE_TRUE_NODE
-- (brahmagyan/l0_ephemeris.py — swisseph's TRUE node, oscillating), while several
-- OTHER declarations across the codebase (bg_ephemeris_engine health probe pre-1075,
-- routers/ephemeris.py, panchang_engine/planets.py) assert or require MEAN_NODE as
-- the Phase 4B house standard. This table stores TRUE under a contract that, until
-- now, asserted mean nowhere explicit on the data itself — and the NOON-UT epoch
-- every row is computed at (swe.julday(..., 12.0)) was likewise undeclared. Per
-- Kimi K3's independent review (KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md §(B)): this
-- table + l0_ephemeris.py's own stale code comments are the ONLY defective sites —
-- routers/ephemeris.py and panchang_engine/planets.py already compute/require
-- MEAN_NODE directly and are unaffected; this migration reconciles the STORE to
-- its own true content, not the reverse.
--
-- ADDITIVE, NO REBUILD: this migration adds two nullable columns and backfills
-- them from the table's own existing, unambiguous content (body name + the fact
-- every row here was always computed at noon UT) — it does NOT recompute, does
-- NOT touch tropical_longitude or any other measured value, and does NOT rebuild
-- the ~825,084-row table.
--
-- Idempotency: ADD COLUMN IF NOT EXISTS + WHERE-guarded UPDATEs — safe to re-run.
-- Transaction ownership belongs to migrate.ts.

BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS node_mode TEXT
    CHECK (node_mode IS NULL OR node_mode IN ('true', 'mean')),
  ADD COLUMN IF NOT EXISTS epoch_convention TEXT;

COMMENT ON COLUMN ephemeris_daily.node_mode IS
  'L0 repair item 7: the lunar-node frame this ROW was computed under. ''true'' '
  'for Rahu/Ketu rows (swe_id=11 = SE_TRUE_NODE, brahmagyan/l0_ephemeris.py — '
  'oscillating, NOT the Phase 4B mean-node house standard other live-serving '
  'paths already use and require). NULL for the other seven bodies, which carry '
  'no node concept. A caller that needs mean-node Rahu/Ketu must NOT read this '
  'table for it — see routers/ephemeris.py''s direct swe.MEAN_NODE call instead.';

COMMENT ON COLUMN ephemeris_daily.epoch_convention IS
  'L0 repair item 7: the time-of-day convention every row in this table is '
  'computed at. ''noon_ut'' for all rows — brahmagyan/l0_ephemeris.py''s '
  '_compute_positions_for_date always calls swe.julday(y, m, d, 12.0). This '
  'table is therefore DAY-GRADE, not instant-grade; a caller needing a specific '
  'birth INSTANT (not noon) must compute live (see ka_graha_sancara.py''s '
  'force_live path) rather than read a day-grade row as if it were instant-exact.';

COMMENT ON TABLE ephemeris_daily IS
  'BRAHMA L0 Brahmagyan: daily tropical planetary positions via pyswisseph. '
  'ayanamsha_id = tropical (subtract ayanamsha at read time for sidereal). '
  'One row per (date, body, ayanamsha_id). node_mode/epoch_convention (migration '
  '1076) declare the lunar-node frame and time-of-day convention on the row '
  'itself — see those columns'' own comments. BRAHMA-BG-0-6.';

-- Backfill existing rows from their own unambiguous content: every row here
-- was always noon-UT; every Rahu/Ketu row was always the TRUE node (swe_id=11).
-- WHERE-guarded so a re-run (or a partial prior run) is a safe no-op.
UPDATE ephemeris_daily
   SET epoch_convention = 'noon_ut'
 WHERE epoch_convention IS NULL;

UPDATE ephemeris_daily
   SET node_mode = 'true'
 WHERE body IN ('Rahu', 'Ketu')
   AND node_mode IS NULL;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT count(*) FROM ephemeris_daily WHERE epoch_convention IS NULL;
--   -- expect: 0
--   SELECT count(*) FROM ephemeris_daily WHERE body IN ('Rahu','Ketu') AND node_mode <> 'true';
--   -- expect: 0
--   SELECT count(*) FROM ephemeris_daily WHERE body NOT IN ('Rahu','Ketu') AND node_mode IS NOT NULL;
--   -- expect: 0 (no node concept for the other seven bodies)
--
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE ephemeris_daily DROP COLUMN IF EXISTS node_mode;
--   ALTER TABLE ephemeris_daily DROP COLUMN IF EXISTS epoch_convention;
--   COMMIT;
-- =============================================================================
