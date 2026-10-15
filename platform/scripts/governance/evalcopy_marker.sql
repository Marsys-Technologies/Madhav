-- evalcopy_marker.sql: the one-row MARKER that proves a database is an EVALUATION COPY (SS N-327).
--
-- RUN ONLY ON THE EVALUATION COPY (the restore-drill instance), as its admin, RIGHT AFTER a restore, by the wrapper that has first proved its target IS that instance (gcloud on the instance the
-- proxy points at; never by the database identity, which a physical restore shares with production). NEVER on production: production must never receive the evalcopy schema.
--
--   psql -X -v ON_ERROR_STOP=1 -v backup_id=1791559465537 -v backup_time=2026-10-09T15:24:00Z \
--        -v instance=amjis-ri02-validation-c720f1832 -v source_instance=amjis-postgres -f evalcopy_marker.sql
--
-- The census (asset_census.read_eval_copy_marker) reads evalcopy.marker with the read-only role and requires exactly this row to EQUAL the SUVARNA_EVAL_COPY declaration; the table accepts only
-- well-formed values (the same patterns the census validates) and only one row. Idempotent: it replaces an earlier marker of an earlier restore.
\set ON_ERROR_STOP on
BEGIN;
DROP SCHEMA IF EXISTS evalcopy CASCADE;
CREATE SCHEMA evalcopy;
CREATE TABLE evalcopy.marker (
  only_row        boolean     PRIMARY KEY DEFAULT true CHECK (only_row),
  backup_id       text        NOT NULL CHECK (backup_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$'),
  backup_time     text        NOT NULL CHECK (backup_time ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$'),
  instance        text        NOT NULL CHECK (instance ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$'),
  source_instance text        NOT NULL CHECK (source_instance ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$' AND source_instance <> instance),
  restored_at     timestamptz NOT NULL DEFAULT now()
);
INSERT INTO evalcopy.marker (backup_id, backup_time, instance, source_instance)
VALUES (:'backup_id', :'backup_time', :'instance', :'source_instance');
GRANT USAGE ON SCHEMA evalcopy TO suvarna_reader;
GRANT SELECT ON evalcopy.marker TO suvarna_reader;
COMMIT;
