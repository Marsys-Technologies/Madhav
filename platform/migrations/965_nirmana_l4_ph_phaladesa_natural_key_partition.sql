-- 965_nirmana_l4_ph_phaladesa_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 964 (ph_phaladesa output_digest_spec) -- see that
-- migration's header for the full verified account. phala_phaladesa has
-- exactly ONE build-time writer (ph_phaladesa.py; the writer's own
-- docstring and test_ph_wave7.py::test_writer_only_writes_phala_phaladesa
-- both assert sole ownership; grep across all .py files found no other
-- writer of the table). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944/946-947/948-949/
-- 950-951/952-953/954-955/956-957/958-959/960-961/962-963): natural_key_
-- partition being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_phaladesa (chart_id, domain) -- sole writer; IS the table''s own live UNIQUE index phala_phaladesa_natural_key. domain is CHECK-constrained to the 13-member canonical domain vocabulary (migration 386). Writer does an unconditional DELETE FROM phala_phaladesa WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), plus an ON CONFLICT (chart_id, domain) DO UPDATE upsert as a second idempotency layer; phaladesa_id (surrogate PK, gen_random_uuid() default), computed_at (DEFAULT now()), and narration_jsonb (embeds date.today() at row-build time -- non-deterministic across rebuilds on different calendar days, same exclusion class as a timestamp column even though its own type is jsonb) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'ph_phaladesa'
   AND natural_key_partition IS NULL;
