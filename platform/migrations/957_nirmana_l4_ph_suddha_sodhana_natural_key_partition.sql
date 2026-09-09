-- 957_nirmana_l4_ph_suddha_sodhana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 956 (ph_suddha_sodhana output_digest_spec) -- see
-- that migration's header for the full verified account.
-- phala_suddha_sodhana has exactly ONE writer (ph_suddha_sodhana.py;
-- confirmed via grep -- the only other .py hit is ph_phaladesa.py, which
-- only reads it via a LEFT JOIN; test files under tests/ are not
-- writers). Declared per the DEP-ASSERT precedent (880/908/909/910/927/
-- 930/939-940/941-942/943-944/946-947/948-949/950-951/952-953/954-955):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_suddha_sodhana (chart_id, anchor_id) -- sole writer; (chart_id, anchor_id) is the table''s own UNIQUE constraint (phala_suddha_sodhana_anchor_key), and anchor_id FKs to phala_anchors(anchor_id) ON DELETE CASCADE, this asset''s own L4 sibling table -- one row per anchor per chart, never a random per-row uuid -- writer does an unconditional DELETE FROM phala_suddha_sodhana WHERE chart_id = %s immediately before the INSERT loop (delete-then-insert-per-chart, CLAUDE.md SS N.3, with an ON CONFLICT (chart_id, anchor_id) DO UPDATE same-transaction safety net), so (chart_id, anchor_id) is a sufficient live natural key; computed_at (DEFAULT now(), bumped on every ON CONFLICT re-run) excluded from the digest value columns as a wall-clock write-time artifact, and entry_id (surrogate PK, gen_random_uuid() default) excluded as the standard surrogate-PK exclusion'
 WHERE asset_id = 'ph_suddha_sodhana'
   AND natural_key_partition IS NULL;
