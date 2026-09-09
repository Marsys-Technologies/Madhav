-- 981_nirmana_l3_ka_sangam_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Renumbered from 977 to 981 by the CONDUCTOR lane (cycle 436,
-- 2026-09-09) alongside its sibling -- see 980's header for the full
-- cross-lane collision account.
--
-- Sibling migration to 980 (ka_sangam output_digest_spec) -- see that
-- migration's header for the full verified account: sole-writer
-- co-writer investigation (brahmagyan/kala/convergence.py is dead,
-- unimported, unregistered code), the non-determinism screen of
-- services/ka_sangam/engine.py (no SQL of its own, pure ephemeris
-- computation), the signal_id-uniqueness check against
-- bodha_msr_signals's own PK, and the live duplicate-key check (0
-- groups across 20,497 rows). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944/946-947/948-949/
-- 950-951/952-953/954-955/956-957/958-959/960-961/962-963/964-965/
-- 968-969/970-971/972-973/974-975): natural_key_partition being NULL
-- reads as freshness_state='unknown' (reason 'partition_undeclared')
-- regardless of writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'kala_convergence (chart_id, horizon_tier, mode, peak_date, signal_id) -- KaSangamWriter is the confirmed sole live build-time writer (grepped tree-wide for INSERT/DELETE/UPDATE INTO kala_convergence: every other tree-wide reference -- mi_adhilepa, ka_jivana_parva, ka_bhavishya_lekha, ph_pratikara, ka_kala_darshana, ph_muhurta, ph_nimitta, mi_kula, ka_taranga, ka_vighnakara, ka_kalasutra, kala_derivation_completeness_guard.py, dag_edge_guard.py, asset_runner.py, bodha_writers/_idempotency.py -- is read-only; the one other file with a real write, brahmagyan/kala/convergence.py, is a standalone CLI seed script never imported by any reachable entrypoint and never orchestrator-registered). No unique DB constraint exists beyond the surrogate convergence_id bigint-sequence PK; the declared key mirrors the writer''s own _dedup() collision key ((mode, peak_date, signal_id), applied per-tier before every INSERT batch) with chart_id and horizon_tier added for cross-chart/cross-tier scoping. Live-verified 0 duplicate-key groups across all 20,497 live rows (17,957 for chart 1c826d5a + 2,540 for chart cb73cd3d); signal_id is never NULL (0/20,497), consistent with kala_activation_predicates.signal_id (this writer''s own predicate source) also carrying 0 NULLs. Writer does a self-scoped delete-then-insert per substep (CLAUDE.md SS N.3): _substep_near clears only chart+horizon_tier=near rows (plus a one-time full lifetime-tier clear only when there are zero lifetime predicates); each _substep_lifetime clears only chart+signal_id+horizon_tier=lifetime rows for its own predicate; a fingerprint-mismatched or first-time build clears the whole chart via plan_substeps before any substep runs. Surrogate/non-owned columns excluded from the digest value columns: convergence_id (surrogate PK, bigint sequence, not in the writer''s own _insert_windows INSERT column list) and computed_at (present in the INSERT column list but bound to the literal SQL NOW() function, not a parameterized value).'
 WHERE asset_id = 'ka_sangam'
   AND natural_key_partition IS NULL;
