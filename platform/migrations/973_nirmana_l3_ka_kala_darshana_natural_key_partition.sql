-- 973_nirmana_l3_ka_kala_darshana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 972 (ka_kala_darshana output_digest_spec) -- see
-- that migration's header for the full verified account, including the
-- sole-writer co-writer investigation and the service-handler
-- dispositions for ka_dasha_kala/ka_tulana/ka_muhurta_seva screened the
-- same cycle. Declared per the DEP-ASSERT precedent (880/908/909/910/
-- 927/930/939-940/941-942/943-944/946-947/948-949/950-951/952-953/
-- 954-955/956-957/958-959/960-961/962-963/964-965/968-969/970-971):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'kala_darshana (chart_id, convergence_id) -- KaKalaDarshanaWriter is the confirmed sole build-time writer (grepped kala_darshana tree-wide: ka_bhavishya_lekha.py and ka_jivana_parva.py both read-only via SELECT/JOIN, services/ka_tulana explicitly documents read-only, kala_derivation_completeness_guard.py is config/prose only). The natural key mirrors the table''s own live UNIQUE constraint reachable via convergence_id (idx_kala_darshana_convergence, UNIQUE on convergence_id WHERE convergence_id IS NOT NULL -- globally unique since convergence_id FKs to kala_convergence.convergence_id and this writer always sets it from that upstream SELECT), declared here chart-scoped-first as (chart_id, convergence_id) for consistency with every other spec in this campaign. Writer does an unconditional DELETE FROM kala_darshana WHERE chart_id = %s immediately before the INSERT batch (delete-then-insert-per-chart, CLAUDE.md SS N.3). Surrogate/non-owned columns excluded from the digest value columns: id (surrogate PK, bigint sequence, not in the writer''s own INSERT column list) and computed_at (DEFAULT now(), also not in the writer''s own INSERT column list)'
 WHERE asset_id = 'ka_kala_darshana'
   AND natural_key_partition IS NULL;
