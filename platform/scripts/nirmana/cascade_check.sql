-- NIRMĀṆA campaign — pre-dispatch CASCADE closure check (charter D-CND-15)
-- Conductor-owned shared campaign tooling (charter C5). Read-only: SELECT only.
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
-- Honest limit: this finds tables reachable by declared FOREIGN KEY with CASCADE. It
-- does NOT find referencing tables that carry NO foreign key -- those ORPHAN rather
-- than cascade, which is the harder failure to detect (they still resolve, so nothing
-- reads false). Cross-check with the second query below, and see #1748.

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
\echo 'Not found by the query above. A stale pointer that still RESOLVES is harder to'
\echo 'detect than an orphan: nothing reads false. Each needs a disposition (#1748).'

SELECT c.table_name, c.column_name, c.data_type
FROM information_schema.columns c
WHERE c.table_schema = 'public'
  AND c.table_name !~ '__ssv_'
  AND c.table_name <> :'table'
  AND c.column_name IN (
    SELECT a.attname FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = :'table'::regclass AND i.indisprimary
  )
  AND NOT EXISTS (
    SELECT 1 FROM pg_constraint k
    WHERE k.contype = 'f' AND k.confrelid = :'table'::regclass
      AND k.conrelid = (quote_ident(c.table_name))::regclass
  )
ORDER BY 1;
