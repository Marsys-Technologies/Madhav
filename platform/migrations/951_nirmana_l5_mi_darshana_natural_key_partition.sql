-- 951_nirmana_l5_mi_darshana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 950 (mi_darshana output_digest_spec) -- see
-- that migration's header for the full verified account.
-- mimamsa_insight_units has exactly ONE writer (mi_darshana.py; confirmed
-- via grep -- the only other .py hits are test files under tests/, no
-- INSERT/UPDATE). Declared per the DEP-ASSERT precedent (880/908/909/
-- 910/927/930/939-940/941-942/943-944/946-947/948-949):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_insight_units (chart_id, insight_id) -- sole writer; (chart_id, insight_id) is the table''s own PRIMARY KEY, and insight_id is deterministically constructed per insight_type from stable upstream identifiers (stratum_key / discovery_id / conclusion_id / event_class_id / channel_id+domain), never a bare uuid4 -- writer does an unconditional DELETE FROM mimamsa_insight_units WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), so (chart_id, insight_id) is a sufficient live natural key; updated_at (DEFAULT now()) and last_calibrated_at (a second wall-clock write-time stamp on 2 of 5 insight_type branches) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'mi_darshana'
   AND natural_key_partition IS NULL;
