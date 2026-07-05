-- Migration 414: chart_dashas — widen the natural-key unique constraint to
-- discriminate KP sub-period rows from classical dasha rows (BA-P3 FIX 2b).
--
-- Root cause (BA Phase-3 Abhinandan re-run, 2026-07-05): the existing unique
-- constraint (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)
-- does NOT include kp_sublevel. compute_kp_subperiods() legitimately emits a
-- KP sub-period row at the SAME level_n + start_iso as the classical
-- Antardasha/Pratyantardasha row it subdivides (a KP sub-period always begins
-- exactly when its parent period begins) — kp_sublevel is the only column
-- that discriminates them. Under the prior executemany()+ON CONFLICT DO
-- UPDATE insert path this collision was silently masked: whichever row
-- (classical or KP) was inserted later in the batch silently overwrote the
-- other's data — real, undetected data corruption. Switching the bulk load
-- to COPY (no ON CONFLICT) surfaced the very first collision as a hard
-- UniqueViolation instead of continuing to mask it.
--
-- Fix: replace the unique constraint with a unique index keyed on
-- COALESCE(kp_sublevel, '') so classical rows (kp_sublevel IS NULL) and KP
-- sub/sub-sub rows are correctly treated as distinct natural keys, while
-- still rejecting genuine duplicates within the same kp_sublevel bucket.
-- (Plain UNIQUE(..., kp_sublevel) would NOT achieve this: SQL NULL is never
-- equal to NULL for uniqueness purposes, so it would silently stop
-- enforcing uniqueness among classical rows entirely.)
--
-- Context-decay-safe: index-only change, no data rewrite, fully idempotent.
--
-- Lock note: this repo's migration runner (platform/scripts/migrate.ts) wraps
-- every migration file in BEGIN/COMMIT, and CREATE INDEX CONCURRENTLY cannot
-- run inside a transaction block — migration 359 hit the same constraint and
-- was deliberately written without CONCURRENTLY for that reason. Following
-- that precedent: this is a plain (non-concurrent) index build, which takes a
-- brief SHARE lock blocking writes to chart_dashas for the build's duration.
-- At current scale (~536K rows total) this is a short, one-time maintenance
-- window; if chart_dashas grows enough that this becomes disruptive, the
-- runner itself would need to support out-of-transaction migrations first.

BEGIN;

ALTER TABLE chart_dashas
  DROP CONSTRAINT IF EXISTS chart_dashas_chart_id_ayanamsha_id_system_id_level_n_start__key;

CREATE UNIQUE INDEX IF NOT EXISTS chart_dashas_natural_key_kp_idx
  ON chart_dashas (
    chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id,
    COALESCE(kp_sublevel, '')
  );

COMMIT;

-- DOWN:
-- CAUTION: only safe to run BEFORE any chart has been rebuilt under this
-- migration — once a chart has classical + KP rows sharing (level_n,
-- start_iso, build_id), re-adding the old plain UNIQUE constraint below will
-- fail with a duplicate-key violation (that collision is exactly what this
-- migration fixes). Do not roll back after a rebuild has run on this schema.
-- BEGIN;
-- DROP INDEX IF EXISTS chart_dashas_natural_key_kp_idx;
-- ALTER TABLE chart_dashas ADD CONSTRAINT chart_dashas_chart_id_ayanamsha_id_system_id_level_n_start__key
--   UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id);
-- COMMIT;
