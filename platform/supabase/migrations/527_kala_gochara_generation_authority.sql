-- Migration 527: kala_gochara_windows.generation + kala_gochara_authority — ADJUDICATION-6 schema
-- =============================================================================
-- ṢAḌ-DARŚANA lane w2g-generation-schema. Ratified by
-- SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md ADJUDICATION-6 (N4 — cutover posture),
-- which PR #1006's V5 bind-time validation (w2g-validations lane) found missing:
-- `kala_gochara_windows` had NO per-row generation discriminator, and `source`
-- (single-valued 'live' on all 16,692 rows) could not be repurposed without
-- mutating v1 rows -- forbidden by the untouchable-data rail (brief §7).
--
-- ADJUDICATION-6's binding posture: GOCHARA-2.0 writes generation-stamped rows
-- BESIDE v1, never over it; v1 rows are neither updated nor deleted, in this
-- migration or ever; a per-chart `authoritative_generation` pointer decides which
-- generation is served; revert is flipping that ONE pointer -- no data motion, no
-- rebuild, no deploy.
--
-- THIS MIGRATION IS ADDITIVE ONLY AND TOUCHES ZERO EXISTING ROW VALUES:
--   1. `generation` lands via `ADD COLUMN ... DEFAULT 'v1' NOT NULL`. In
--      PostgreSQL 11+ this is a CATALOG-ONLY change when the default is a
--      constant (not volatile) -- the server records the default in
--      pg_attribute/pg_attrdef and every pre-existing row is deemed to hold that
--      default value for reads; it does NOT rewrite the table's heap or touch a
--      single existing row's on-disk data (see PostgreSQL docs, "ALTER TABLE ...
--      ADD COLUMN": "adding a column with a default ... to a large table used to
--      be a big deal ... it's essentially instantaneous, because it doesn't
--      involve rewriting the table"). Existing 16,692 rows are retro-labeled
--      'v1' by the catalog default, not by an UPDATE statement -- the untouchable
--      rail's concern is row DATA, and no row's data is written by this
--      migration (verified: `platform/python-sidecar/tests/test_migration_527_generation_catalog_only.py`
--      asserts xmin is unchanged for a sample of pre-existing rows across the
--      migration boundary -- xmin only advances on an actual heap rewrite/UPDATE).
--   2. `kala_gochara_authority` is a brand-new, empty table. Seeding nothing is
--      deliberate: an ABSENT row for a chart_id means 'v1' authoritative BY
--      DEFINITION (see the table comment below) -- the reading-path contract
--      this migration establishes, not yet consumed by a writer.
--
-- Idempotent: `ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`,
-- `CREATE INDEX IF NOT EXISTS`. No destructive ops. No FROZEN orchestrator/
-- WriterBase change; no writer added by this migration.
--
-- Migration-number coordination (per prompt instructions, cross-checked live
-- against BOTH migration dirs and every in-flight shad-darshana/* branch,
-- local + origin, at claim time 2026-08-01): highest claimed anywhere was 526
-- (`526_kala_vedha_gochara.sql`, shad-darshana/w3-moorti-vedha, ADJUDICATION-11
-- vedha work) with 524/525 also already claimed (w3-abhijit-parihara,
-- w3-moorti-vedha). This lane claims **527**, the next free integer across
-- both `platform/migrations/` and `platform/supabase/migrations/` and every
-- open lane found at claim time.
-- =============================================================================

BEGIN;

-- ── 1. Generation discriminator on the untouchable table (additive, catalog-only) ──

ALTER TABLE kala_gochara_windows
    ADD COLUMN IF NOT EXISTS generation TEXT NOT NULL DEFAULT 'v1';

COMMENT ON COLUMN kala_gochara_windows.generation IS
    'Migration 527 (ADJUDICATION-6): per-row generation stamp. Landed via '
    'ADD COLUMN ... DEFAULT ''v1'' -- a catalog-only change in PG11+, so every '
    'pre-existing row is retro-labeled ''v1'' WITHOUT a heap rewrite or an UPDATE '
    'touching its data (untouchable-data rail respected). GOCHARA-2.0''s writer '
    'stamps its own rows with its own generation label (e.g. ''2.0'') BESIDE the '
    'v1 rows -- v1 rows are never updated or deleted, in this migration or ever. '
    'No CHECK constraint is applied deliberately: the 2.0 writer lane, not this '
    'schema-only migration, owns the exact generation label it stamps, and a '
    'CHECK here would pre-guess a naming choice that is that lane''s to make.';

-- Composite index: every serving-path read (register_gochara_windows.ts's three
-- tools, reading_checklist.ts's fetchGocharaSweep) filters WHERE chart_id = $1
-- AND generation = <authoritative pointer, resolved per-chart>. chart_id alone is
-- already the leading column on three existing indexes (idx_kala_gochara_windows_
-- chart_event, _chart_window, _chart_adverse_intensity); this adds the
-- (chart_id, generation) pair itself so a resolved-authority read (or, once 2.0
-- rows exist, ANY read that must exclude the other generation) does not have to
-- fall back to a filter scan across a mixed-generation chart's full row set.
CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_chart_generation
    ON kala_gochara_windows (chart_id, generation);

-- ── 2. The one-pointer-flip revert surface (ADJUDICATION-6, brand-new table) ──

CREATE TABLE IF NOT EXISTS kala_gochara_authority (
    chart_id                 UUID PRIMARY KEY,
    authoritative_generation TEXT NOT NULL DEFAULT 'v1',
    flipped_at                TIMESTAMPTZ,
    flipped_by                TEXT,
    evidence_ref              TEXT
);

COMMENT ON TABLE kala_gochara_authority IS
    'Migration 527 (ADJUDICATION-6): the per-chart authority pointer. READING-PATH '
    'CONTRACT: an ABSENT row for a chart_id means ''v1'' is authoritative BY '
    'DEFINITION -- this table is seeded with NOTHING by this migration, on '
    'purpose. A caller resolves authority as '
    '`COALESCE((SELECT authoritative_generation FROM kala_gochara_authority '
    'WHERE chart_id = $1), ''v1'')`, never by requiring a row to exist. Revert '
    'from 2.0 back to v1 (or promotion from v1 to 2.0) is exactly one UPDATE (or '
    'DELETE, to fall back to the absent-row default) of THIS table -- no '
    'kala_gochara_windows row is ever touched by a flip. All four ADJUDICATION-6 '
    'flip conditions (zero unclassified divergences; §3.3 specimen continuity; '
    '§3.4 determinism; §3.5 post-cutover battery) gate a write to this table; '
    'none is time-based (the design §7 "N days" framing was rejected as a '
    'category error for a batch-computed century table).';

COMMENT ON COLUMN kala_gochara_authority.authoritative_generation IS
    'Which kala_gochara_windows.generation value is currently served for this '
    'chart. Default ''v1'' matches the absent-row contract on COMMENT ON TABLE '
    'above -- this column-level default only matters if a row is ever inserted '
    'without an explicit value; the real contract is the absent-row COALESCE.';

COMMENT ON COLUMN kala_gochara_authority.flipped_at IS
    'NULL until the first flip. Timestamp of the most recent authority change.';

COMMENT ON COLUMN kala_gochara_authority.flipped_by IS
    'NULL until the first flip. Free-text identity/session of who/what flipped it '
    '(native decision, conductor session id, etc.) -- an audit breadcrumb, not an '
    'FK.';

COMMENT ON COLUMN kala_gochara_authority.evidence_ref IS
    'NULL until the first flip. Pointer to the evidence record (equivalence '
    'corpus run id, close-report artifact path, ruling id) that satisfied all '
    'four ADJUDICATION-6 flip conditions -- never a bare flip with no citation.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_gochara_authority;
--   DROP INDEX IF EXISTS idx_kala_gochara_windows_chart_generation;
--   ALTER TABLE kala_gochara_windows DROP COLUMN IF EXISTS generation;
--   COMMIT;
-- Safe: kala_gochara_authority is dropped whole (nothing was ever seeded into
-- it by this migration); the generation column's DROP is likewise additive-
-- reversal only -- no v1 row data was ever written by this migration, so there
-- is nothing to un-write.
-- =============================================================================
