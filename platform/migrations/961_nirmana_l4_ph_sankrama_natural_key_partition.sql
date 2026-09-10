-- 961_nirmana_l4_ph_sankrama_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 960 (ph_sankrama output_digest_spec) -- see
-- that migration's header for the full verified account. phala_sankrama
-- has exactly ONE writer (ph_sankrama.py; confirmed via grep --
-- ph_phaladesa.py only SELECTs from it via a read-only LEFT JOIN).
-- Declared per the DEP-ASSERT precedent (880/908/909/910/927/930/
-- 939-940/941-942/943-944/946-947/948-949/950-951/952-953/954-955/
-- 956-957): natural_key_partition being NULL reads as
-- freshness_state='unknown' (reason 'partition_undeclared') regardless of
-- writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id, target_domain, relationship_type) -- sole writer; this IS the table''s own live UNIQUE constraint phala_sankrama_natural_key (migration 367 added cdlm_cell_id to the original index specifically so that two distinct CDLM cells linking the same anchor to the same target domain via distinct bridge paths do not collapse to one row). None of the five key columns is a random uuid4 -- chart_id/source_anchor_id/cdlm_cell_id are foreign references (chart, phala_anchors, bodha_cdlm_cells; cdlm_cell_id carried via the derivation ledger, no cross-layer FK by design) and target_domain/relationship_type are deterministic classification strings from the DB-free derive_spillover() engine. Writer does an unconditional DELETE FROM phala_sankrama WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3), and the INSERT itself carries ON CONFLICT ON CONSTRAINT phala_sankrama_natural_key DO NOTHING, so the live unique constraint is a sufficient natural key; sankrama_id (surrogate PK, gen_random_uuid() default) and computed_at (DEFAULT now()) excluded from the digest value columns as non-deterministic across rebuilds'
 WHERE asset_id = 'ph_sankrama'
   AND natural_key_partition IS NULL;
