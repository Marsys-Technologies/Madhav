-- Migration 1227: ephemeris_daily node-series unique index (step 0 of the L0 mean-node series).
-- Created: 2026-10-02. Author: Exec Suvarna (NODE-SERIES lane).
-- Design: 00_ARCHITECTURE/briefs/suvarna/exec/node_series/DESIGN_L0_MEAN_NODE_SERIES_v1_0.md section 2 (SS decisions N-68, N-69;
-- number allocation: plan v1.5.4, 1227 = node-series unique index; 1228 = replacement integrity contract + digest spec;
-- 1250 = drop of the old three-column constraint; 1251 = the older held edges).
--
-- WHAT IT DOES (and nothing else)
-- ===============================
-- Adds ONE index to public.ephemeris_daily:
--   ephemeris_daily_date_body_ayanamsha_node_mode_uq
--     UNIQUE btree (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT
-- node_mode is NULL on the seven non-node bodies (Sun..Saturn) and 'true' on Rahu/Ketu today, so a plain four-column
-- UNIQUE would not dedupe the NULL rows; NULLS NOT DISTINCT (PostgreSQL 15+; live is 15.18) does. The new key is a strict
-- superset of the live key, so no existing row can violate it. NO DATA CHANGE: no row is inserted, updated or deleted,
-- no column is added, the old constraint ephemeris_daily_date_body_ayanamsha_id_key (UNIQUE (date, body, ayanamsha_id))
-- STAYS until migration 1250. Until 1250 a 'mean' row beside a 'true' row for the same (date, body, ayanamsha_id) is still
-- refused by the old key; after 1250 the new index is the only key and admits it (proved in
-- platform/python-sidecar/tests/test_ephemeris_node_index_1227_sql.py on a disposable PostgreSQL).
--
-- ORDERING RULE (read before merging; merge = apply at the next deploy, the migrate job runs this file)
-- ======================================================================================================
-- 1. This migration PRECEDES the series write: it must be applied before the migrations/writers that make a MEAN row
--    possible (1228, the writer change, 1250, the bg_ephemeris rebuild). It may merge any time before step 2 of the
--    rollout (the release) PROVIDED the index already exists (rule 2).
-- 2. THE ROUTINE MIGRATION LOGIN CANNOT CREATE THE INDEX. PROD_DATABASE_URL connects as amjis_app
--    (platform/scripts/validate-migration-database-routes.ts:12); amjis_app OWNS ephemeris_daily (pg_class.relowner,
--    read 2026-10-02) but holds USAGE only on schema public (has_schema_privilege(...,'CREATE') = false, nspowner
--    data_plane_schema_owner), and PostgreSQL requires CREATE on the schema for CREATE INDEX and for ADD CONSTRAINT UNIQUE
--    alike (reproduced on a disposable PostgreSQL 15: "permission denied for schema public" for both forms; the same
--    class as the REPAIR NOTE in migration 1071). So the live index is created by the D6 owner-path executor
--    (00_ARCHITECTURE/briefs/suvarna/exec/node_series/d6_index/, hash-reviewed by SS, run only through run_gated.sh).
--    THIS FILE is the schema-of-record: on production it runs AFTER the D6 step, finds the index, VERIFIES its structure
--    and does no DDL and reads no data; on a database whose role has CREATE on public and that already has the live
--    ephemeris_daily shape (a restored copy, a disposable database) it creates the index itself. If it is applied when the
--    index is absent AND the role has no CREATE on public, it RAISES (fail closed): it never records itself applied
--    without the index existing. Consequence: DO NOT MERGE before the D6 step has run and the verification query below
--    returns the expected row. BLAST RADIUS of an early merge: migrate.ts applies files in numeric order and stops at the
--    first failure, so a failing 1227 fails the deploy's migrate job AND holds back every later pending migration
--    (1230-1238 and the rest) until the D6 step has run.
--    A from-scratch replay is out of scope: no migration adds node_mode/epoch_convention (they exist on the live table only;
--    migration 1076 declares them but the base table comes from the non-numeric ws2_l0_ephemeris.sql, sorted after every
--    numbered file), so such a database fails closed at the column guard below. CI does not replay migrations.
-- 3. The old three-column constraint stays until 1250; no writer may rely on the new key before this file is applied.
--
-- LOCK AND WRITERS
-- ================
-- CREATE UNIQUE INDEX (no CONCURRENTLY: migrate.ts runs this file inside one BEGIN..COMMIT) takes SHARE on the table for
-- the build: reads proceed, writes wait. The only writers of ephemeris_daily are the L0 bg_ephemeris rebuild
-- (pipeline/orchestrator/writers/bg_ephemeris.py, brahmagyan/l0_ephemeris.py _copy_insert) and
-- platform/python-sidecar/scripts/build_ephemeris_1900_2150.py; nothing serves writes. Measured on a disposable PostgreSQL 15
-- with 825,084 rows: about 0.35 s. `SET LOCAL lock_timeout = '5s'` bounds the wait for the lock only (not the build): a
-- running bg_ephemeris rebuild holding row locks makes this fail fast instead of hanging a shared deploy; re-run after the
-- rebuild. Apply only with 0 active bg_ephemeris builds.
--
-- GUARDS (refuse an unexpected live state; the whole file is one DO block, so a refusal rolls everything back; migrate.ts then
-- writes no tracker row)
-- ===========================================================================================================
--   * PostgreSQL >= 15 (NULLS NOT DISTINCT);
--   * public.ephemeris_daily is a plain table with date date, body text, ayanamsha_id text, node_mode text;
--   * (create path only) no node_mode = 'mean' row exists (a mean row before this key means the ordering rule was broken: stop
--     and look) and, if the old three-column key is absent, no duplicate (date, body, ayanamsha_id, node_mode) group exists;
--   * the index name is free, or it is already THIS index (same table, unique, valid, ready, btree, the four columns in
--     order, default operator classes and collations, NULLS NOT DISTINCT, ascending, no predicate, no expressions); any
--     other object by that name refuses;
--   * when the index must be created, the role owns the table and has CREATE on public, else a message names the D6 step.
-- (the verify-only path reads no data: a later mean row or a concurrent write cannot make a legitimate apply fail)
-- Idempotent: a second run finds the verified index and does nothing.
--
-- MANUAL REVERT (only before migration 1250 drops the old key; after it the new index is the ONLY uniqueness guard and must stay):
--   DROP INDEX public.ephemeris_daily_date_body_ayanamsha_node_mode_uq;   -- as the table owner (amjis_app may drop it)
-- A failed apply rolls back by itself (migrate.ts), leaving nothing to revert.
--
-- VERIFIED BY PRODUCTION STRUCTURE (read-only, as suvarna_reader; the file itself re-checks the same facts at its end)
-- ====================================================================================================================
--   SELECT i.indisunique, i.indisvalid, i.indisready, i.indnullsnotdistinct, am.amname,
--          pg_get_indexdef(i.indexrelid)
--     FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid JOIN pg_am am ON am.oid = c.relam
--    WHERE c.relname = 'ephemeris_daily_date_body_ayanamsha_node_mode_uq' AND i.indrelid = 'public.ephemeris_daily'::regclass;
--   -- expect one row: t | t | t | t | btree | CREATE UNIQUE INDEX ... USING btree (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT
--   SELECT conname FROM pg_constraint WHERE conrelid = 'public.ephemeris_daily'::regclass AND contype = 'u';
--   -- expect still: ephemeris_daily_date_body_ayanamsha_id_key (dropped only by 1250)
--   SELECT count(*) FROM public.ephemeris_daily;  -- expect unchanged (825084 on 2026-10-02)
-- Live catalog read 2026-10-02 (suvarna_reader): owner amjis_app; 825,084 rows (91,676 dates x 9 bodies, 1900-01-01..2150-12-31;
-- Rahu/Ketu node_mode 'true', the others NULL, epoch_convention noon_ut, ayanamsha_id tropical); indexes: ephemeris_daily_pkey (id),
-- ephemeris_daily_date_body_ayanamsha_id_key (the old unique constraint), idx_ephemeris_ayanamsha, idx_ephemeris_body,
-- idx_ephemeris_date, idx_ephemeris_date_body; CHECK ephemeris_daily_node_mode_check; heap 272 MB, 494 MB with indexes; no
-- views, foreign keys or triggers depend on the table.
--
-- Trap 103: before treating this as applied, check the _migrations_applied row AND the structure query above; a success deploy
-- run listed for the merge sha may have run a different DEPLOY_SHA.
--
-- No BEGIN/COMMIT here: the migration runner owns the transaction (platform/scripts/migrate.ts: BEGIN; <SQL>;
-- INSERT INTO _migrations_applied; COMMIT).

SET LOCAL lock_timeout = '5s';

DO $mig1227$
DECLARE
  idx_name  constant text := 'ephemeris_daily_date_body_ayanamsha_node_mode_uq';
  old_def   constant text := 'UNIQUE (date, body, ayanamsha_id)';
  tbl       regclass;
  idx       regclass;
  old_key   boolean;
  n bigint;
  ok boolean;
BEGIN
  -- guard: server version
  IF current_setting('server_version_num')::int < 150000 THEN
    RAISE EXCEPTION 'migration 1227 refused: NULLS NOT DISTINCT needs PostgreSQL 15 or later (server_version_num=%)',
      current_setting('server_version_num');
  END IF;

  -- guard: the table and its four key columns
  tbl := to_regclass('public.ephemeris_daily');
  IF tbl IS NULL THEN
    RAISE EXCEPTION 'migration 1227 refused: public.ephemeris_daily does not exist';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE oid = tbl AND relkind = 'r') THEN
    RAISE EXCEPTION 'migration 1227 refused: public.ephemeris_daily is not a plain table';
  END IF;
  SELECT count(*) INTO n
    FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid
   WHERE a.attrelid = tbl AND NOT a.attisdropped AND a.attnum > 0
     AND ((a.attname = 'date' AND t.typname = 'date')
       OR (a.attname IN ('body', 'ayanamsha_id', 'node_mode') AND t.typname = 'text'));
  IF n <> 4 THEN
    RAISE EXCEPTION 'migration 1227 refused: ephemeris_daily lacks date date / body text / ayanamsha_id text / node_mode text (found % of 4)', n;
  END IF;

  SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = tbl AND contype = 'u' AND pg_get_constraintdef(oid) = old_def)
    INTO old_key;

  idx := to_regclass('public.' || idx_name);
  IF idx IS NULL THEN
    -- the index must be created here. Data guards run on this path only.
    SELECT count(*) INTO n FROM public.ephemeris_daily WHERE node_mode = 'mean';
    IF n <> 0 THEN
      RAISE EXCEPTION 'migration 1227 refused: % node_mode=''mean'' rows already exist; the ordering rule (index before the series) was broken', n;
    END IF;
    IF NOT old_key THEN
      -- node-agnostic: count_only_table_level: duplicate-group count over every series row, returns no node value
      SELECT count(*) INTO n FROM (
        SELECT 1 FROM public.ephemeris_daily GROUP BY date, body, ayanamsha_id, node_mode HAVING count(*) > 1 LIMIT 1) d;
      IF n <> 0 THEN
        RAISE EXCEPTION 'migration 1227 refused: duplicate (date, body, ayanamsha_id, node_mode) rows exist and the old three-column key is absent';
      END IF;
    END IF;
    -- needs table ownership and CREATE on schema public
    IF NOT pg_has_role(current_user, (SELECT relowner FROM pg_class WHERE oid = tbl), 'USAGE') THEN
      RAISE EXCEPTION 'migration 1227 refused: % does not own ephemeris_daily; create the index through the D6 owner-path executor first', current_user;
    END IF;
    IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN
      RAISE EXCEPTION 'migration 1227 refused: % has no CREATE on schema public, so CREATE INDEX cannot run here; the index is created by the D6 owner-path executor (00_ARCHITECTURE/briefs/suvarna/exec/node_series/d6_index/) BEFORE this file merges; recording this migration applied without the index would be a silent no-op', current_user;
    END IF;
    EXECUTE format('CREATE UNIQUE INDEX %I ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT', idx_name);
    idx := to_regclass('public.' || idx_name);
  END IF;

  -- verify the structure of the index by that name (freshly created or already present)
  SELECT (c.relkind = 'i' AND i.indrelid = tbl AND i.indisunique AND i.indisvalid AND i.indisready
          AND i.indnullsnotdistinct AND am.amname = 'btree' AND i.indnatts = 4 AND i.indnkeyatts = 4
          AND i.indpred IS NULL AND i.indexprs IS NULL AND i.indoption::text = '0 0 0 0'
          AND NOT EXISTS (SELECT 1 FROM unnest(i.indkey::int2[], i.indclass::oid[], i.indcollation::oid[]) AS k(attnum, opc, coll)
                            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                            LEFT JOIN pg_opclass oc ON oc.oid = k.opc
                           WHERE oc.oid IS NULL OR NOT oc.opcdefault OR oc.opcintype <> a.atttypid OR k.coll <> a.attcollation)
          AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey::int2[]) WITH ORDINALITY k(attnum, ord)
                      JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum ORDER BY k.ord)
              = ARRAY['date', 'body', 'ayanamsha_id', 'node_mode']::text[])
    INTO ok
    FROM pg_class c
    LEFT JOIN pg_index i ON i.indexrelid = c.oid
    LEFT JOIN pg_am am ON am.oid = c.relam
   WHERE c.oid = idx;
  IF ok IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'migration 1227 refused: public.% exists but is not the expected unique btree (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT index', idx_name;
  END IF;
END
$mig1227$;
