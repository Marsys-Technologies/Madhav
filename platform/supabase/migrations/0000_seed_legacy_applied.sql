-- 0000_seed_legacy_applied.sql
-- Seeds _migrations_applied for files that were applied to the production database
-- before migrate.ts tracking was in place. migrate.ts checks filename presence only;
-- sha256 here is the actual file hash for audit trail completeness.
--
-- 0001_brahma_baseline.sql: squash of migrations 057-157, applied 2026-06-05 via psql.
-- All tables it creates use IF NOT EXISTS; the file also contains pg_dump meta-commands
-- (\restrict, \unrestrict, CREATE SCHEMA without IF NOT EXISTS) that are not valid SQL
-- when executed through pg library — it must remain permanently skipped.

INSERT INTO _migrations_applied (filename, sha256)
VALUES (
  '0001_brahma_baseline.sql',
  'ec6f564cb7cc43d493edf46124ca2c8d6506b6a2291ed1e013d43c9f7b38adef'
)
ON CONFLICT (filename) DO NOTHING;
