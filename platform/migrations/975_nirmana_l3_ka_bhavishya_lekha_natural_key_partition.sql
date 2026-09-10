-- 975_nirmana_l3_ka_bhavishya_lekha_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 974 (ka_bhavishya_lekha output_digest_spec) -- see
-- that migration's header for the full verified account, including the
-- sole-writer co-writer investigation, the bo_karanajala re-screen
-- (deferred), the ka_graha_sancara service-handler disposition, and the
-- ka_avadhi/ka_kalasutra/ka_taranga rule-outs screened the same cycle.
-- Declared per the DEP-ASSERT precedent (880/908/909/910/927/930/
-- 939-940/941-942/943-944/946-947/948-949/950-951/952-953/954-955/
-- 956-957/958-959/960-961/962-963/964-965/968-969/970-971/972-973):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'kala_bhavishya (chart_id, projection_rank) -- KaBhavishyaLekhaWriter is the confirmed sole build-time writer (grepped kala_bhavishya tree-wide: ph_nimitta.py + services/ph_nimitta/engine.py both read-only via SELECT, inheriting a projection into the UNRELATED phala_anchors table via D37; kala_derivation_completeness_guard.py is config/prose only). No unique DB constraint exists beyond the surrogate id PK; projection_rank is assigned via enumerate(darshana_rows, start=1) over the writer''s own total-order query (ORDER BY effective_score DESC NULLS LAST, peak_date, convergence_id -- convergence_id is kala_convergence''s own unique PK, so this cannot itself tie), making it unique per chart by construction within one build''s INSERT batch. Writer preserves outcome_recorded/outcome_notes (the one genuinely non-regenerable pair of columns -- an observation of the world, not a derivation) across a rebuild via a dict keyed on (signal_id, peak_date), and raises RuntimeError rather than silently dropping an unreattachable outcome. Writer does an unconditional DELETE FROM kala_bhavishya WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3). Surrogate/non-owned columns excluded from the digest value columns: id (surrogate PK, bigint sequence, not in the writer''s own INSERT column list) and computed_at (DEFAULT now(), also not in the writer''s own INSERT column list). The writer''s date.today() read bounds the rolling 5-year eligibility WHERE-clause window (an intentional day-to-day drift in which projections qualify, not a defect) but is never embedded into any persisted column''s value, so it does not affect same-build determinism.'
 WHERE asset_id = 'ka_bhavishya_lekha'
   AND natural_key_partition IS NULL;
