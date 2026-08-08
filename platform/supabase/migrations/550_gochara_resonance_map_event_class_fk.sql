-- Migration 550: gochara_resonance_map.event_class -> brahma_event_ontology FK
-- Created: 2026-08-08
-- ADHIṢṬHĀNA campaign, Lane A4 (Event-class contract)
--
-- gochara_resonance_map.event_class (migration 459, platform/migrations/) has carried only a
-- source-level SQL comment since its creation claiming it is "one of brahma_event_ontology's 27
-- event_class_id values" (never an enforced DB-level `COMMENT ON COLUMN`, and no FOREIGN KEY or
-- CHECK constraint enforced it either). Bad data could enter the column silently.
-- brahma_event_ontology (migration 388, extended by 456) is a real,
-- populated reference table (27 rows, event_class_id TEXT PRIMARY KEY) already the enforced
-- validation source for TS writers (see platform/src/lib/mcp/lel_event_writer.ts, which queries
-- it live). A proper FK is the right fit here — the reference table already exists with a
-- primary key on exactly the column we need to point at, so FK is preferred over a CHECK-list
-- (which would duplicate brahma_event_ontology's id set as a second, drift-prone copy).
--
-- SAFETY (CLAUDE.md §N.4 "Surgical migrations, verified"): live violation check run BEFORE
-- authoring this migration (2026-08-08, read-only query against gochara_resonance_map +
-- brahma_event_ontology):
--   gochara_resonance_map total rows: 370
--   brahma_event_ontology total rows: 27
--   distinct event_class values in gochara_resonance_map: career_advancement, chronic_onset,
--     illness_acute, major_gain, marriage, surgery (all 6 present in brahma_event_ontology)
--   rows whose event_class would violate the FK: 0
--   rows with event_class IS NULL: 0
-- Zero violations found, so this migration adds the FK constraint directly (validated
-- immediately, not NOT VALID) — the table is small (370 rows) and clean. Idempotent: guarded by
-- an existence check on pg_constraint so re-running this file is a safe no-op.
--
-- ROLLBACK:
--   ALTER TABLE gochara_resonance_map DROP CONSTRAINT IF EXISTS gochara_resonance_map_event_class_fkey;

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'gochara_resonance_map_event_class_fkey'
  ) THEN
    ALTER TABLE gochara_resonance_map
      ADD CONSTRAINT gochara_resonance_map_event_class_fkey
      FOREIGN KEY (event_class) REFERENCES brahma_event_ontology(event_class_id);
  END IF;
END $$;

COMMENT ON COLUMN gochara_resonance_map.event_class IS
  'FOREIGN KEY to brahma_event_ontology(event_class_id) (migration 550) — one of the 27 '
  'ratified event classes (see EVENT_CLASSES in platform/src/lib/event_classes.ts, the TS '
  'mirror of l0_ghatana.EVENT_CLASSES). Previously documented only in a comment with no '
  'enforcing constraint; migration 550 closes that gap.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE gochara_resonance_map DROP CONSTRAINT IF EXISTS gochara_resonance_map_event_class_fkey;
--   -- Pre-550 state had no DB-level column comment at all (only the source-level comment in
--   -- platform/migrations/459_gochara_resonance_map.sql's CREATE TABLE) — restore that true state:
--   COMMENT ON COLUMN gochara_resonance_map.event_class IS NULL;
--   COMMIT;
-- =============================================================================
