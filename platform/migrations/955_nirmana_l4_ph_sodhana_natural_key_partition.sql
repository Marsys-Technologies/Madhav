-- 955_nirmana_l4_ph_sodhana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 954 (ph_sodhana output_digest_spec) -- see
-- that migration's header for the full verified account.
-- phala_sodhana has exactly ONE writer (ph_sodhana.py; confirmed via grep
-- -- ph_phaladesa.py and ph_suddha_sodhana.py/its engine.py only SELECT
-- from it). Declared per the DEP-ASSERT precedent (880/908/909/910/927/
-- 930/939-940/941-942/943-944/946-947/948-949/950-951/952-953): natural_key_partition
-- being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_sodhana (anchor_id, anomaly_type, detected_field) -- sole writer; (anchor_id, anomaly_type, detected_field) is the table''s own UNIQUE constraint (phala_sodhana_natural_key). chart_id is not part of this unique index but anchor_id is FK''d to phala_anchors(anchor_id), which is itself chart-scoped, so the triple is chart-unambiguous in practice; chart_id is still carried in where_equals and value_columns per this series'' convention. Writer does an unconditional DELETE FROM phala_sodhana WHERE chart_id = %s immediately before the INSERT loop (delete-then-insert-per-chart, CLAUDE.md SS N.3), with a belt-and-suspenders ON CONFLICT DO NOTHING against the natural-key unique index on the INSERT itself; computed_at (DEFAULT now()) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'ph_sodhana'
   AND natural_key_partition IS NULL;
