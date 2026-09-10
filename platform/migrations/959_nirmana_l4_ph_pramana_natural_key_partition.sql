-- 959_nirmana_l4_ph_pramana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 958 (ph_pramana output_digest_spec) -- see that
-- migration's header for the full verified account. phala_pramana has
-- exactly ONE writer (ph_pramana.py; confirmed via grep -- the only
-- other .py hit is ph_phaladesa.py, which only reads it via a LEFT
-- JOIN). Declared per the DEP-ASSERT precedent (880/908/909/910/927/930/
-- 939-940/941-942/943-944/946-947/948-949/950-951/952-953/954-955/
-- 956-957): natural_key_partition being NULL reads as
-- freshness_state='unknown' (reason 'partition_undeclared') regardless
-- of writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_pramana (chart_id, anchor_id) -- sole writer; derive_pramana_records() produces exactly ONE PramanaRecord per anchor (engine invariant, see its own docstring), so (chart_id, anchor_id) is a sufficient live natural key even though the table''s own broader UNIQUE constraint is (anchor_id, evidence_type, COALESCE(lel_entry_id, -1)) -- phala_pramana_natural_key. anchor_id FKs to phala_anchors(anchor_id) ON DELETE CASCADE, this asset''s own L4 sibling table -- one row per anchor per chart, never a random per-row uuid -- writer does an unconditional DELETE FROM phala_pramana WHERE chart_id = %s immediately before the INSERT loop (delete-then-insert-per-chart, CLAUDE.md SS N.3, with an ON CONFLICT DO NOTHING same-transaction safety net). computed_at (DEFAULT now(), wall-clock write-time artifact) excluded from the digest value columns; pramana_id (surrogate PK, gen_random_uuid() default) excluded as the standard surrogate-PK exclusion. D5 NO-SCORING gate note: this writer never inserts calibration/scoring columns (hard-gated at write time by _d5_gate()); the digest spec captures only structural classification fields, fully compatible with the D5 boundary'
 WHERE asset_id = 'ph_pramana'
   AND natural_key_partition IS NULL;
