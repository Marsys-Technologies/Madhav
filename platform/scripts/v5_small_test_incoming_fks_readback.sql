-- v5_small_test_incoming_fks_readback.sql  (READ ONLY)
-- Lists every incoming foreign key of the two parent tables the v5 small-test scripts delete from: build_runs and
-- kala_gochara_publication. This is the scripts' own discovery query (v5_small_test_shared.INCOMING_FK_SQL), with the parent filled in.
-- Run it as the steward before the dry run; any key whose child_cols or parent_cols has more than one column, or whose parent_cols is
-- not exactly {id} (build_runs) / {manifest_id} (kala_gochara_publication), makes the scripts REFUSE by name.

-- incoming keys of build_runs
SELECT c.conname, c.conrelid::regclass::text AS tbl, c.confdeltype AS action, ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum ORDER BY k.ord) AS child_cols, ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.attnum ORDER BY k.ord) AS parent_cols
FROM pg_constraint c WHERE c.contype = 'f' AND c.confrelid = 'public.build_runs'::regclass
ORDER BY c.conname;

-- incoming keys of kala_gochara_publication
SELECT c.conname, c.conrelid::regclass::text AS tbl, c.confdeltype AS action, ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum ORDER BY k.ord) AS child_cols, ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.attnum ORDER BY k.ord) AS parent_cols
FROM pg_constraint c WHERE c.contype = 'f' AND c.confrelid = 'public.kala_gochara_publication'::regclass
ORDER BY c.conname;
