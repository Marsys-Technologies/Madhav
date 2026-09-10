-- 679_nirmana_l3_f_parva_1_level_column.sql
--
-- NIRMĀṆA L3 Kāla — W3. Discharges F-PARVA-1 (L3_W1_ANALYSIS_BATCH_E.md, ka_jivana_parva
-- finding 1, MUST): `kala_jivana_parva` mixes MD (mahādaśā), AD (antardaśā), and PD
-- (pratyantardaśā) rows in one flat table with NO level discriminator in the served
-- columns. Measured on the native chart: `parva_index=8` (a mahādaśā, Saturn 1991-2010)
-- sits between `parva_index=7` and `parva_index=9` (both antardaśās, same planet,
-- overlapping year ranges) — a consumer rendering the life arc has no way to tell which
-- row is which level without string-parsing `source_citation`
-- (`ka_jivana_parva:v2.0:MD=Saturn` vs `...:MD=Saturn:AD=Mercury` vs `...:PD=Mercury`).
-- The only UNIQUE key today is `(chart_id, parva_index)` — a loop counter, not a natural
-- key. Doctrine: §N.7 item 2 (a serving surface must be able to pin the row it means) +
-- §N.6 item 1 (never present differently-graded rows as one undifferentiated list).
--
-- This migration:
--   1. Adds `parva_level SMALLINT` (1=MD, 2=AD, 3=PD).
--   2. Backfills every EXISTING row deterministically from its own `source_citation` —
--      the exact string-parsing rule the finding itself names as the only way to recover
--      the level today, done once here so no row is left NULL pending the next rebuild:
--        `:PD=` present -> 3 ; else `:AD=` present -> 2 ; else -> 1 (MD, the fallback,
--      since every row's citation begins with `:MD=`).
--   3. Sets the column NOT NULL and adds a CHECK (parva_level IN (1,2,3)), matching this
--      table's own existing `_check` constraint-naming convention
--      (`kala_jivana_parva_parva_quality_check`, `..._dominant_signal_class_check`).
--   4. ADDS (does not replace) a real natural key — additive alongside the existing
--      `(chart_id, parva_index)` unique index, which stays in place unchanged (harmless,
--      just not semantically meaningful; removing it is out of this migration's scope).
--
-- ── THE KEY IS NOT WHAT THE FINDING FIRST PROPOSED — CORRECTED AGAINST LIVE DATA ──────
-- The finding's own proposed key, `(chart_id, parva_level, dasha_planet, start_year)`,
-- was DRY-RUN TESTED against real production data before this migration was finalized and
-- FAILED with a genuine UniqueViolation: chart 482012f1's AD level carries TWO rows with
-- (parva_level=2, dasha_planet='Sun', start_year=2054) — `MD=Venus:AD=Sun` (the LAST,
-- one-year AD of the outgoing Venus mahādaśā) and `MD=Sun:AD=Sun` (the FIRST AD of the
-- incoming Sun mahādaśā, which — a real Vimshottari rule — is always the same lord as the
-- MD itself). Two structurally different antardaśās can share a (lord, start_year) at an
-- MD boundary; year-granularity cannot tell them apart.
-- `(chart_id, source_citation)` was tried next and ALSO failed live: `chart_dashas` for
-- this chart genuinely carries a SECOND partial Vimshottari cycle (Moon MD recurs at
-- 2060-08-18, 120 years after its first occurrence at 1950-01-01 — verified directly
-- against `chart_dashas`), so the SAME (MD lord, AD lord) pair, hence the SAME
-- `source_citation` string, legitimately recurs once per ~120-year cycle. This is honest
-- long-horizon dasha data, not an accretion bug — `ka_jivana_parva`'s own `md_end_actual`
-- fallback of `date(2100, 1, 1)` already anticipates a multi-decade forward horizon.
-- `(chart_id, source_citation, start_year)` — combining the full MD/AD/PD lord-chain
-- string (disambiguates siblings within one cycle) WITH the calendar year (disambiguates
-- the same lord-chain's next cycle) — was verified live to have ZERO duplicate groups
-- across all three canonical charts' full row sets. This is the key this migration
-- installs. `parva_level` is not itself a key column (the level is already fully implied
-- by which `MD=`/`AD=`/`PD=` markers `source_citation` contains) — it exists as a served,
-- directly-queryable/indexable discriminator column, which is the actual F-PARVA-1 defect
-- (no column says the level; a reader had to parse a string to find out).
--
-- The writer (pipeline/orchestrator/writers/ka_jivana_parva.py) is updated in the SAME PR
-- to populate `parva_level` on every future INSERT — this migration's backfill covers only
-- rows that already exist as of this migration running; the writer's own delete-then-insert
-- idempotency (§N.3) means every chart is fully re-covered on its next ordinary rebuild
-- regardless.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE kala_jivana_parva ADD COLUMN IF NOT EXISTS parva_level SMALLINT;

UPDATE kala_jivana_parva
SET parva_level = CASE
  WHEN source_citation LIKE '%:PD=%' THEN 3
  WHEN source_citation LIKE '%:AD=%' THEN 2
  ELSE 1
END
WHERE parva_level IS NULL;

ALTER TABLE kala_jivana_parva ALTER COLUMN parva_level SET NOT NULL;

ALTER TABLE kala_jivana_parva
  DROP CONSTRAINT IF EXISTS kala_jivana_parva_parva_level_check;
ALTER TABLE kala_jivana_parva
  ADD CONSTRAINT kala_jivana_parva_parva_level_check CHECK (parva_level IN (1, 2, 3));

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_jivana_parva_natural_key
  ON kala_jivana_parva (chart_id, source_citation, start_year);
