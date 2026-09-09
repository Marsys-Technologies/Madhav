-- 963_nirmana_l4_ph_pratikara_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 962 (ph_pratikara output_digest_spec) -- see that
-- migration's header for the full verified account. phala_mitigation has
-- exactly ONE build-time writer (ph_pratikara.py; confirmed via grep --
-- ph_phaladesa.py only SELECTs from it read-only; the legacy
-- brahmagyan/phala/mitigation.py::seed_mitigation call site in
-- pipeline/brahma_pipeline.py is dead code -- both structurally unreachable
-- via its own broken globals() guard and unimported by any live entrypoint,
-- per migration 962's header). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944/946-947/948-949/
-- 950-951/952-953/954-955/956-957/958-959/960-961): natural_key_partition
-- being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_mitigation (chart_id, obstruction_id, intensity_tier) -- sole writer; mirrors the table''s own live UNIQUE constraint phala_mitigation_natural_key, which is (chart_id, COALESCE(obstruction_id, -1), intensity_tier). The COALESCE guards a hypothetical NULL obstruction_id, but obstruction_id is 0/536 NULL for the canonical chart (writer always sets it from kala_obstruction.id) and the plain-column triple is already collision-free across the whole live table, so the plain columns are a sufficient live natural key without the COALESCE wrapper (output_digest_spec key_columns rejects any row with a NULL key column outright). Writer does an unconditional DELETE FROM phala_mitigation WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), and each INSERT also carries ON CONFLICT DO NOTHING against the live constraint; mitigation_id (surrogate PK, gen_random_uuid() default) and computed_at (DEFAULT now()) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'ph_pratikara'
   AND natural_key_partition IS NULL;
