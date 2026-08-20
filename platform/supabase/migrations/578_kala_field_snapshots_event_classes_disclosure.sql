-- migration 578: F-78 disclosure — kala_field_snapshots.event_classes is the
-- ATTEMPTED set, not the BUILT set (PARIŚEṢA S3/CL-13, DIAGNOSIS.md F-78).
--
-- Comment-only, additive, non-destructive. Mirrors the existing
-- skipped_classes comment (492_kala_field_core.sql:207-210) so both columns
-- of the same disclosure pair are documented, not just one.
--
-- Rollback (non-destructive):
--   COMMENT ON COLUMN kala_field_snapshots.event_classes IS NULL;

COMMENT ON COLUMN kala_field_snapshots.event_classes IS
  'F-78 disclosure: the ATTEMPTED set, not the built set -- every event class '
  '_discover_event_classes() found a bodha_pratijna row for, regardless of '
  'whether stage 4/5 wrote any kala_field rows for it. A class present here '
  'AND in this row''s skipped_classes was NOT built (see that column''s own '
  'comment). To get the classes actually built for a snapshot, subtract: '
  'services.ka_kshetra.writer.built_event_classes(event_classes, '
  'skipped_classes). Never read this column alone as "classes covered."';
