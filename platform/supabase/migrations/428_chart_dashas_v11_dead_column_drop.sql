-- Migration 428: chart_dashas — drop dead enrichment columns (register V-11)
-- Created: 2026-07-10
--
-- Root cause (R6 0e-dashameta lane, register row V-11): a 10-row live sample
-- plus a full-table check on both built charts (482012f1, 1c826d5a) showed
-- two of the four "Addition A/J/K" enrichment columns are permanently dead:
--
--   - triggered_yogas_jsonb_atomic       — always '[]'. ga_dashas_writer.py has
--     no yoga-trigger detection logic (which natal yogas activate when their
--     constituent lords rule a dasha) — that capability does not exist
--     anywhere in the GA7 writer and would require a real yoga-activation
--     engine, not a dasha-period computation. Populating it here would be
--     fabricated computation (CLAUDE.md B.10) — the honest fix is to drop the
--     placeholder column rather than ship a permanently-empty JSONB that
--     silently implies "verified: no yogas triggered."
--   - lord_transit_at_period_start_jsonb — always NULL. Requires a transit
--     engine (planet positions AT ARBITRARY FUTURE/PAST DATES, not just at
--     birth) that chart_facts does not provide (chart_facts is natal-only).
--     Same reasoning: out of GA7's scope, drop rather than fabricate.
--
-- lord_natal_shadbala_total (also flagged dead in V-11) is NOT touched here —
-- it is fixed by re-deriving it via chart_facts JOIN in the writer itself
-- (register V-1/G-7/D-1 companion fix), so it stays a real, populated column.
-- sandhi_flag (also flagged in V-11) is NOT a dead column after the sibling
-- writer fix — it is fixed in ga_dashas_writer.py to stop being a tautological
-- constant, not dropped.
--
-- Reverse-citation check (performed before writing this migration): grepped
-- the full platform/ and 00_ARCHITECTURE/ trees for both column names. Zero
-- consumers outside ga_dashas_writer.py itself, its own migration (211), and
-- its unit tests. get_dashas.ts's COMPACT_FIELDS projection (the only live
-- retrieval surface reading chart_dashas) never selects either column by
-- name; its `fields=all` escape hatch does `SELECT *` and tolerates a
-- narrower column set with no code change. Safe to drop.
--
-- Context-decay-safe: idempotent (IF EXISTS), no data-shape impact on any
-- other table, no application code outside ga_writers/ga_dashas_writer.py
-- reads these columns (see ga_dashas_writer.py's _COPY_COLUMNS list, updated
-- in the same commit as this migration to stop referencing them).

BEGIN;

ALTER TABLE chart_dashas DROP COLUMN IF EXISTS triggered_yogas_jsonb_atomic;
ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_transit_at_period_start_jsonb;

COMMIT;

-- DOWN (re-add as dead placeholders — NOT recommended; only for emergency
-- rollback compatibility with an un-migrated ga_dashas_writer.py):
-- BEGIN;
-- ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS triggered_yogas_jsonb_atomic JSONB DEFAULT NULL;
-- ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS lord_transit_at_period_start_jsonb JSONB DEFAULT NULL;
-- COMMIT;
