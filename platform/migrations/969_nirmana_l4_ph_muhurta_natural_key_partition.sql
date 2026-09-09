-- 969_nirmana_l4_ph_muhurta_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 968 (ph_muhurta output_digest_spec) -- see that
-- migration's header for the full verified account, including the
-- brahmagyan/phala/muhurta.py legacy seed-endpoint co-writer
-- investigation (ruled out: live function definition still targets a
-- superseded schema and would error on any invocation). Declared per the
-- DEP-ASSERT precedent (880/908/909/910/927/930/939-940/941-942/943-944/
-- 946-947/948-949/950-951/952-953/954-955/956-957/958-959/960-961/
-- 962-963/964-965): natural_key_partition being NULL reads as
-- freshness_state='unknown' (reason 'partition_undeclared') regardless
-- of writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_muhurta (chart_id, action_class, window_start) -- sole build-time writer (PhMuhurtaWriter); IS the table''s own live UNIQUE index phala_muhurta_natural_key. A legacy HTTP action endpoint (POST /phala/seed_muhurta -> seed_phala_muhurta_native_sample DB function, brahmagyan/phala/muhurta.py PH-4-4) also targets this table but its live function definition still references the superseded action_type/auspiciousness_score/factors columns dropped when this writer''s schema (action_class/composite_quality/etc.) superseded it -- any invocation would error with "column action_type does not exist" and insert zero rows, confirmed via pg_get_functiondef against the running prod DB. Writer does an unconditional DELETE FROM phala_muhurta WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), plus an ON CONFLICT DO NOTHING upsert against the live constraint as a second idempotency layer; muhurta_id (surrogate PK, gen_random_uuid() default) and computed_at (DEFAULT now()) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'ph_muhurta'
   AND natural_key_partition IS NULL;
