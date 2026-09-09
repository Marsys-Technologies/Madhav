-- 953_nirmana_l5_mi_sambandha_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 952 (mi_sambandha output_digest_spec) -- see
-- that migration's header for the full verified account.
-- mimamsa_manifestation_grammar has exactly ONE writer (mi_sambandha.py;
-- confirmed via grep -- mi_darshana.py only SELECTs from it, the
-- test_mi_sambandha.py hit is a test file, not a writer). Declared per the
-- DEP-ASSERT precedent (880/908/909/910/927/930/939-940/941-942/943-944/
-- 946-947/948-949/950-951): natural_key_partition being NULL reads as
-- freshness_state='unknown' (reason 'partition_undeclared') regardless of
-- writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_manifestation_grammar (chart_id, origin_kind, origin_ref, channel_id) -- sole writer; (chart_id, origin_kind, origin_ref, channel_id) is the table''s own PRIMARY KEY. domain is excluded from the key -- the writer always sets origin_ref equal to domain (both the empirical and prior-seed row-construction loops build the same key tuple), so domain is a value column redundant with origin_ref, not an independent key component. None of the three key columns beyond chart_id is a random uuid4 -- origin_kind is a fixed literal ("prediction_set") and origin_ref/channel_id are deterministic domain/channel names -- writer does an unconditional DELETE FROM mimamsa_manifestation_grammar WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), so the PK is a sufficient live natural key; updated_at (DEFAULT now()) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'mi_sambandha'
   AND natural_key_partition IS NULL;
