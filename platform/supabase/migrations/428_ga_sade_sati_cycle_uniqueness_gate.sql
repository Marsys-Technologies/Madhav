-- Migration 428: ga_sade_sati cycle uniqueness gate (D-2 / V-13, R6 0d-clips)
-- Created: 2026-07-10
--
-- Context: D-2/V-13 found Sade Sati cycle rows pairwise "duplicated" — e.g.
-- CYCLE_3 and CYCLE_4 for the same (chart_id, ayanamsha_id) both ending at
-- 1998-04-17T07:34:13Z, with different cycle_start values. Root cause (fixed
-- in the same PR, ga_writers/ga_sade_sati_writer.py build_sade_sati_cycles):
-- Saturn's retrograde dance at a sign boundary produced multiple forward
-- "vishakha_entry" candidates that all resolved to the same downstream
-- janma/anumukha/exit chain — each shadow candidate was emitted as its own
-- cycle. The writer fix dedupes by (janma_entry, anumukha_entry, cycle_end),
-- keeping the earliest vishakha_entry.
--
-- This migration adds the DB-level belt-and-suspenders gate: two partial
-- unique indexes on chart_facts, scoped to fact_category='sade_sati_cycle',
-- that make it IMPOSSIBLE for a rebuild to silently re-introduce a duplicate
-- cycle boundary for the same (chart_id, ayanamsha_id) — the INSERT fails
-- loudly instead of serving corrupt data.
--
-- Deviation from the literal task wording "unique on (chart_id, cycle_start)":
-- chart_facts is a per-fact EAV table (chart_id, ayanamsha_id, fact_category,
-- fact_subject, fact_key, fact_value_*), not a cycle-per-row table, and a
-- plain (chart_id, cycle_start) constraint would be WRONG here — multiple
-- ayanamshas legitimately share an identical cycle_start_iso value whenever
-- their computed Moon sign coincides (verified live: CYCLE_1 across
-- krishnamurti/lahiri_chitrapaksha/raman/true_chitra all share
-- cycle_start_iso=1961-02-01T18:29:31+00:00 for chart 482012f1 — correct,
-- not a bug). The natural key that actually distinguishes real cycles is
-- (chart_id, ayanamsha_id, fact_value_text) scoped to the cycle_start_iso /
-- cycle_end_iso fact_key — which is what these indexes enforce. Since the
-- found bug's duplicate signature was on cycle_end_iso (not cycle_start_iso),
-- both boundaries are gated for defense in depth.
--
-- Verified via live read-only queries (chart_id 482012f1 + 1c826d5a) against
-- the pre-fix data: duplicate cycle_end_iso values within one (chart_id,
-- ayanamsha_id) DID exist (the bug); no duplicate cycle_start_iso values were
-- found in either chart's pre-fix data, but the index is added defensively
-- since it is the field the task explicitly named.
--
-- SEQUENCING — DO NOT apply until EVERY chart currently in the DB has been
-- rebuilt with the ga_sade_sati_writer.py dedup fix (same PR). This is a
-- partial UNIQUE INDEX, not a per-chart operation — if apply this migration
-- finds a duplicate value anywhere across ANY chart_id still carrying
-- pre-fix rows, the CREATE UNIQUE INDEX will fail for the whole migration.
-- Before applying: SELECT chart_id, ayanamsha_id, fact_value_text, COUNT(*)
--   FROM chart_facts WHERE fact_category='sade_sati_cycle'
--     AND fact_key IN ('cycle_start_iso','cycle_end_iso')
--   GROUP BY 1,2,3 HAVING COUNT(*) > 1;
-- must return zero rows for every chart in public.charts, not just the two
-- this PR rebuilt.
--
-- Lock note: this repo's migration runner (platform/scripts/migrate.ts) wraps
-- every migration file in BEGIN/COMMIT, and CREATE INDEX CONCURRENTLY cannot
-- run inside a transaction block — migrations 359/414/415 hit the same
-- constraint and were deliberately written without CONCURRENTLY for that
-- reason. Following that precedent: this is a plain (non-concurrent) index
-- build, which takes a brief SHARE lock blocking writes to chart_facts for
-- the build's duration — acceptable at current scale, index-only, no data
-- rewrite, fully idempotent (IF NOT EXISTS).

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS ux_chart_facts_sade_sati_cycle_start_value
  ON chart_facts (chart_id, ayanamsha_id, fact_value_text)
  WHERE fact_category = 'sade_sati_cycle' AND fact_key = 'cycle_start_iso';

CREATE UNIQUE INDEX IF NOT EXISTS ux_chart_facts_sade_sati_cycle_end_value
  ON chart_facts (chart_id, ayanamsha_id, fact_value_text)
  WHERE fact_category = 'sade_sati_cycle' AND fact_key = 'cycle_end_iso';

COMMIT;

-- DOWN:
-- BEGIN;
-- DROP INDEX IF EXISTS ux_chart_facts_sade_sati_cycle_start_value;
-- DROP INDEX IF EXISTS ux_chart_facts_sade_sati_cycle_end_value;
-- COMMIT;
