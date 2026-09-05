-- NIRMĀṆA campaign — pre-dispatch CASCADE closure check (charter D-CND-15)
-- Conductor-owned shared campaign tooling (charter C5). Read-only against every real
-- campaign table -- the no-FK scan below uses a session-local TEMP TABLE (DROPPED ON
-- COMMIT) as scratch space for a server-side loop; that writes nothing durable.
--
--   psql "$DATABASE_URL" -v table=bodha_msr_signals -f platform/scripts/nirmana/cascade_check.sql
--
-- RUN THIS BEFORE EVERY `rebuild_only` DISPATCH, for every table your writer deletes from.
--
-- Why it exists
-- -------------
-- The campaign's DAG models ANCESTORS, and the E-gate gates on ancestors. `ON DELETE
-- CASCADE` makes DESCENDANTS a destruction surface, and nothing in the E-gate, the
-- run-slot protocol, or a writer's own idempotency helper models that direction.
--
-- This is not hypothetical. A `bo_laksana` MSR rebuild -- ordinary, planned,
-- `rebuild_only` work -- cascade-deletes 864,733 rows across 12 tables in THREE
-- layers, including `phala_anchors`, the table a separate campaign-wide hold exists
-- to protect (issues #1770, #1732). It was found because one session declined to
-- accept a favourable conclusion about its own table, not because anything detected
-- it. This query is the detector that should have existed.
--
-- A §N.3 per-chart delete-then-insert is only "in-layer" IF THE FKs SAY SO. Here they
-- said the opposite of the code comment above them (D-CND-16: query the catalogue; a
-- comment asserting a schema property is not evidence of that property).
--
-- Reading the output
-- ------------------
--   depth       how many CASCADE hops from your table
--   layer       inferred from the table-name prefix
--   live_rows   rows that a delete of your table's matching parents could remove
--   verdict     IN-LAYER (your own data, you are replacing it deliberately)
--               CROSS-LAYER *** HOLD *** (another layer's data -- STOP, file an
--                                         adjudication issue, take a snapshot first)
--
-- ANY row marked CROSS-LAYER means: do not dispatch. Take a verified snapshot, file
-- an adjudication issue naming the owning layers, and get an ordering ruling. The
-- owning layer must confirm its data is regenerable BEFORE the snapshot is spent.
--
-- Honest limit: this first query finds tables reachable by declared FOREIGN KEY with
-- CASCADE. It does NOT find referencing tables that carry NO foreign key -- those
-- ORPHAN rather than cascade, which is the harder failure to detect (they still
-- resolve, so nothing reads false; see #1748) -- or tables reachable by ON DELETE SET
-- NULL, a MUTATION surface rather than a destruction one. The second query below
-- covers no-FK orphans; the third covers SET NULL. See #1748 and D-CND-18.
--
-- D-CND-18 (2026-09-05, #1805): the second query below used to match candidate
-- referrers by NAME EQUALITY to the parent's PK column, and excluded a whole TABLE
-- (not just the matching column) the instant it had any FK to the parent. Both
-- under-reported: this campaign's common naming is `top_anchor_id`/`source_pramana_id`,
-- not the parent's own column name, and a table can carry one FK column and one
-- genuinely-orphan column at the same time. Fixed to a type-and-shape candidate scan
-- (any uuid/text/varchar column, per-COLUMN FK exclusion) plus a LIVE sampled
-- resolution check -- type/name matching alone is not sufficient in either direction:
-- `phala_muhurta.fructification_anchor` is a text column that looks like a candidate
-- and holds the literal label 'tara+candra-bala', not an id, so a candidate is only
-- reported once a live sample of its values actually resolves into the parent's PK.

\if :{?table} \else \echo 'ERROR: pass -v table=<your table>' \quit \endif

\echo ''
\echo '════ CASCADE closure — rows a delete from this table would DESTROY ════'

WITH RECURSIVE fk AS (
  SELECT confrelid::regclass::text AS parent, conrelid::regclass::text AS child
  FROM pg_constraint
  WHERE contype = 'f' AND confdeltype = 'c'
    AND conrelid::regclass::text !~ '__ssv_'
), chain AS (
  SELECT child, 1 AS depth, ARRAY[:'table', child] AS path
  FROM fk WHERE parent = :'table'
  UNION ALL
  SELECT f.child, c.depth + 1, c.path || f.child
  FROM chain c JOIN fk f ON f.parent = c.child
  WHERE c.depth < 8 AND NOT f.child = ANY(c.path)
), dedup AS (
  SELECT DISTINCT ON (child) child, depth, path FROM chain ORDER BY child, depth
), classified AS (
  SELECT d.child, d.depth, array_to_string(d.path, ' -> ') AS cascade_path,
    CASE
      WHEN d.child LIKE 'bg\_%'     OR d.child LIKE 'brahma\_%'  THEN 'L0'
      WHEN d.child LIKE 'ga\_%'     OR d.child LIKE 'chart\_%'   THEN 'L1'
      WHEN d.child LIKE 'bodha\_%'                               THEN 'L2'
      WHEN d.child LIKE 'kala\_%'                                THEN 'L3'
      WHEN d.child LIKE 'phala\_%'                               THEN 'L4'
      WHEN d.child LIKE 'mimamsa\_%' OR d.child LIKE 'lel\_%'    THEN 'L5'
      ELSE '(unknown)'
    END AS layer,
    CASE
      WHEN :'table' LIKE 'bg\_%'     OR :'table' LIKE 'brahma\_%'  THEN 'L0'
      WHEN :'table' LIKE 'ga\_%'     OR :'table' LIKE 'chart\_%'   THEN 'L1'
      WHEN :'table' LIKE 'bodha\_%'                                THEN 'L2'
      WHEN :'table' LIKE 'kala\_%'                                 THEN 'L3'
      WHEN :'table' LIKE 'phala\_%'                                THEN 'L4'
      WHEN :'table' LIKE 'mimamsa\_%' OR :'table' LIKE 'lel\_%'    THEN 'L5'
      ELSE '(unknown)'
    END AS own_layer
  FROM dedup d
)
SELECT depth, child AS cascade_deletes_from, layer,
  (xpath('/row/c/text()',
    query_to_xml(format('SELECT count(*) AS c FROM %I', child), false, true, '')))[1]::text::bigint AS live_rows,
  CASE WHEN layer = own_layer AND layer <> '(unknown)'
       THEN 'IN-LAYER'
       ELSE 'CROSS-LAYER *** HOLD ***' END AS verdict,
  cascade_path
FROM classified
ORDER BY (layer = own_layer), depth, live_rows DESC;

\echo ''
\echo '════ Referencing tables with NO foreign key — these ORPHAN, they do not cascade ════'
\echo 'Type-and-shape candidate scan + LIVE resolution check (D-CND-18, #1805). A column'
\echo 'is reported here only if it (a) is an id-shaped type (uuid/text/varchar -- this'
\echo 'campaign stores the same logical id as either uuid or text depending on the'
\echo 'table, so matching the parent PK''s exact type would itself under-report), (b)'
\echo 'carries no FK on THAT column to this table (per-column exclusion, not per-table),'
\echo 'and (c) a live sample of its non-null values actually resolves (cast to text) into'
\echo 'this table''s PK. Reported row counts are exact full counts of resolving rows, not'
\echo 'scaled from the sample -- ONLY the accept/reject decision is probabilistic (sampled'
\echo 'up to 500 values per candidate, so a same-shaped column on a very large table'
\echo 'cannot resolve-check its full contents at prohibitive cost). A rejected candidate'
\echo 'is not reported and is not re-verified beyond the sample: this finds a real orphan'
\echo 'surface with high confidence, it does not prove the absence of one on a column'
\echo 'whose non-null values happen to fall entirely outside the sampled 500.'
\echo ''
\echo 'Implementation note: the schema-wide candidate scan is ~2,500+ id-shaped columns'
\echo '(this campaign has many tables). Probing each from the psql client as a separate'
\echo 'round trip was measured over 120s and abandoned -- this runs the whole scan as one'
\echo 'server-side PL/pgSQL loop instead (a session-local TEMP TABLE holds results, DROPPED'
\echo 'ON COMMIT), which is still read-only against every real campaign table -- it writes'
\echo 'nothing but its own throwaway scratch space. The final SELECT is a plain read.'
\echo ''
\echo 'Known-truth regression case (D-CND-18, live-verified 2026-09-05): against'
\echo 'phala_anchors this must return exactly 2 rows -- mimamsa_predictions.source_pramana_id'
\echo '(195 rows, crosses into L5) and phala_phaladesa.top_anchor_id (13 rows). If either is'
\echo 'missing or a count differs, this query has regressed. Do NOT "simplify" the'
\echo 'resolution check back to a name-or-type-only heuristic:'
\echo 'phala_muhurta.fructification_anchor is the same shape as an anchor id and holds the'
\echo 'literal label ''tara+candra-bala'', not ids -- a name/type-only match reports it as a'
\echo 'false positive; only the live resolution check tells the two apart.'

-- psql variable interpolation (`:'table'`) does not reach inside a dollar-quoted DO
-- body reliably across psql versions, and PL/pgSQL's own `:=` assignment syntax makes
-- relying on it there doubly fragile. Pass the target table in through a TEMP TABLE
-- instead of interpolating it into the block.
--
-- Deliberately NOT `ON COMMIT DROP`: under psql's default autocommit, each top-level
-- statement is its own transaction, so a table created `ON COMMIT DROP` is dropped
-- the instant its own CREATE statement's transaction commits -- before the very next
-- statement in this same file can see it (verified live: reproduces a bare "relation
-- ... does not exist" on the following DELETE, every time). `IF NOT EXISTS` + the
-- `DELETE FROM` immediately below it are what keep this idempotent/safe to re-run in
-- one session instead; the table lives for the rest of the session and is cleaned up
-- automatically when the connection closes, same as any other TEMP TABLE.
CREATE TEMP TABLE IF NOT EXISTS _cascade_check_target (t text);
DELETE FROM _cascade_check_target;
INSERT INTO _cascade_check_target VALUES (:'table');

DO $cascade_check_orphan_scan$
DECLARE
  target_table text;
  pk_col       text;
  cand         RECORD;
  n_sample     bigint;
  n_resolved   bigint;
  n_full       bigint;
BEGIN
  SELECT t INTO target_table FROM _cascade_check_target LIMIT 1;

  -- Same reason as _cascade_check_target above: this DO block is itself one
  -- statement/transaction, so ON COMMIT DROP here would drop this table before
  -- the plain SELECT right after the block could read it.
  CREATE TEMP TABLE IF NOT EXISTS _cascade_check_orphans (
    table_name text, column_name text, resolving_rows bigint, sample_note text
  );
  DELETE FROM _cascade_check_orphans;

  EXECUTE format(
    'SELECT a.attname FROM pg_index i
       JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
      WHERE i.indrelid = %L::regclass AND i.indisprimary LIMIT 1', target_table)
    INTO pk_col;

  FOR cand IN
    EXECUTE format(
      'SELECT c.table_name, c.column_name
         FROM information_schema.columns c
        WHERE c.table_schema = %L
          AND c.table_name !~ %L
          AND c.table_name <> %L
          AND c.data_type IN (%L, %L, %L)
          AND NOT EXISTS (
            SELECT 1 FROM pg_constraint k
            JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = ANY(k.conkey)
            WHERE k.contype = %L AND k.confrelid = %L::regclass
              AND k.conrelid = c.table_name::regclass
              AND a.attname = c.column_name
          )',
      'public', '__ssv_', target_table, 'uuid', 'text', 'character varying', 'f', target_table)
  LOOP
    EXECUTE format(
      'SELECT count(*), count(*) FILTER (WHERE v::text IN (SELECT %I::text FROM %I))
         FROM (SELECT %I AS v FROM %I WHERE %I IS NOT NULL LIMIT 500) s',
      pk_col, target_table, cand.column_name, cand.table_name, cand.column_name)
      INTO n_sample, n_resolved;

    CONTINUE WHEN n_sample = 0 OR n_resolved::numeric / n_sample < 0.95;

    EXECUTE format(
      'SELECT count(*) FROM %I WHERE %I::text IN (SELECT %I::text FROM %I)',
      cand.table_name, cand.column_name, pk_col, target_table)
      INTO n_full;

    INSERT INTO _cascade_check_orphans
      VALUES (cand.table_name, cand.column_name, n_full,
              format('%s/%s sampled values resolve', n_resolved, n_sample));
  END LOOP;
END;
$cascade_check_orphan_scan$;

SELECT table_name, column_name, resolving_rows, sample_note
FROM _cascade_check_orphans
ORDER BY 1, 2;

\echo ''
\echo '════ Referencing tables with ON DELETE SET NULL — a MUTATION surface, not destruction ════'
\echo 'Third bug found verifying #1805 (D-CND-18): the CASCADE query above filters'
\echo 'confdeltype=''c'' and cannot see ON DELETE SET NULL children. SET NULL does not'
\echo 'destroy rows -- they survive, so C13''s destroys_rows test stays false and WP-6'
\echo 'does not stop a dispatch -- but the FK column is silently nulled, and with it the'
\echo 'record of what those rows were derived from. A stale CASCADE-orphaned pointer at'
\echo 'least still says "derived from a replaced generation"; a SET-NULLed one says'
\echo 'nothing at all. Treat a non-zero count here as a real provenance cost, reported'
\echo 'separately from CASCADE destruction because conflating the two would misreport in'
\echo 'the other direction (§N.8).'

SELECT k.conrelid::regclass::text AS table_name, a.attname AS column_name,
  (xpath('/row/n/text()', query_to_xml(format(
     'SELECT count(*) AS n FROM %I WHERE %I IS NOT NULL',
     k.conrelid::regclass::text, a.attname), false, true, '')))[1]::text::bigint AS rows_will_be_nulled
FROM pg_constraint k
JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = ANY(k.conkey)
WHERE k.contype = 'f' AND k.confdeltype = 'n'
  AND k.confrelid = :'table'::regclass
  AND k.conrelid::regclass::text !~ '__ssv_'
ORDER BY 1, 2;
