-- 971_nirmana_l4_ph_rectification_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 970 (ph_rectification output_digest_spec) -- see
-- that migration's header for the full verified account, including the
-- two-table sole-ownership finding and the brahmagyan/phala/
-- rectification.py legacy dead-function co-writer investigation.
-- Declared per the DEP-ASSERT precedent (880/908/909/910/927/930/
-- 939-940/941-942/943-944/946-947/948-949/950-951/952-953/954-955/
-- 956-957/958-959/960-961/962-963/964-965/968-969): natural_key_partition
-- being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success.

UPDATE asset_registry
   SET natural_key_partition = 'phala_rectification (chart_id, offset_minutes, ayanamsha_id) + phala_rectification_best (chart_id) -- PhRectificationWriter is the confirmed sole build-time writer of BOTH tables in full (not a subset case). Both natural keys ARE the tables'' own live UNIQUE constraints (phala_rectification_chart_offset_ayan; phala_rectification_best_chart_id_key). A legacy dead function, brahmagyan/phala/rectification.py::seed_phala_rectification(), also targets phala_rectification but has zero call sites anywhere in the tree and its INSERT/ON CONFLICT clause reference columns (candidate_time, alignment_score, rectification_confidence, source_citation, computed_at) that do not exist on the live schema -- confirmed dead, not a live co-writer risk. Writer does an unconditional DELETE FROM phala_rectification_best WHERE chart_id = %s then DELETE FROM phala_rectification WHERE chart_id = %s (children first) immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3). Surrogate/non-owned columns excluded from the digest value columns: both tables'' id (surrogate PK, gen_random_uuid()) and scored_at (DEFAULT now()); phala_rectification_best.best_candidate_id (FK to the other table''s fresh-per-rebuild surrogate PK, non-deterministic across rebuilds, redundant with offset_minutes/candidate_birth_utc already included); phala_rectification_best.native_adopted/adopted_at (never set by this writer''s own INSERT column list -- mutated only by a post-build human review action per the D43 stage_for_review gate, reset to DEFAULT on every rebuild, not writer-owned content)'
 WHERE asset_id = 'ph_rectification'
   AND natural_key_partition IS NULL;
