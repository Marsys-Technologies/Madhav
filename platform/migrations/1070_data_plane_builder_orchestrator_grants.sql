-- 1070_data_plane_builder_orchestrator_grants.sql
--
-- Restore the orchestrator grants `data_plane_builder` needs to complete a build run.
--
-- WHY
-- ---
-- The data-plane ownership cutover (migrations 1035/1036, applied 2026-09-18) created
-- `data_plane_builder` as the dedicated identity for `brahma-build-pipeline-job` and gave it
-- USAGE+SELECT on the new l1/l2 generation SEQUENCES, but never granted it anything on the
-- orchestrator's own metadata tables, which are owned by `amjis_app`. `data_plane_builder`
-- holds ZERO role memberships (verified live 2026-09-20), so it inherits nothing.
--
-- Consequence, observed in production: EVERY build run of EVERY asset, for ANY chart, fails
-- immediately. Cloud Run job execution `brahma-build-pipeline-job-j882q` (2026-09-19T22:50Z,
-- dispatching ga_positions) exited 1 with:
--
--     psycopg.errors.InsufficientPrivilege: permission denied for table asset_registry
--       at pipeline/orchestrator/runner.py:345 _verify_registry_still_matches_manifest
--
-- `_verify_registry_still_matches_manifest` is called unconditionally from `execute_run`
-- (runner.py:1039) before any work begins, so the failure is universal, not asset-specific.
-- The last successful build was 2026-09-12 — before the cutover.
--
-- This also explains the stuck `ga_dashas_replacement_in_progress` guard on the canonical
-- chart: a replacement was begun, the run could not complete, and no subsequent run can
-- clear it while this gap exists.
--
-- SCOPE — least privilege, derived from actual reads/writes, not assumption
-- ------------------------------------------------------------------------
-- Verb map taken from the orchestrator source at this commit:
--   asset_registry             SELECT  + UPDATE of exactly 3 service-probe columns
--                              (asset_runner.py:649, :689 — service_health/last_invoked_at/
--                              last_selftest_at). NOT full UPDATE; NOT DELETE.
--   asset_provenance_receipts  SELECT, INSERT, UPDATE (provenance.py:255 INSERT, :363 UPDATE)
--   asset_freshness            SELECT   (asset_runner.py, provenance.py — read only)
--   charts                     SELECT   (birth_params.py and callers — read only)
--   asset_output_digest_specs  SELECT   (output_digest.py — read only)
--
-- Deliberately NOT granted:
--   * DELETE on any table here.
--   * Full-table UPDATE on asset_registry — the three probe columns are the only ones the
--     orchestrator writes, and asset_registry is otherwise configuration that a builder must
--     not be able to mutate (a builder able to rewrite depends_on/target_table could defeat
--     `_verify_registry_still_matches_manifest`, the very guard this unblocks).
--   * Anything for mimamsa_*/phala_* (0/37 and 0/20 accessible) or the remaining
--     chart_* tables. Those are real, separate gaps in other layers' territory; they are
--     recorded for their owners rather than silently widened here. This migration restores
--     exactly the orchestrator core plus what L1 W1 (ga_positions -> chart_facts,
--     ga_dashas -> chart_dashas) needs; both of those data tables are ALREADY writable.
--   * No sequence grants — neither table here has a serial/identity column (verified live).
--
-- AUTHORITY / SAFETY
-- ------------------
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021). `amjis_app` owns all five tables
-- and is the role the routine migration runner authenticates as (both verified live), so no
-- one-shot owner bootstrap is required — this is an ordinary routine migration.
-- Idempotent: GRANT is naturally idempotent and this migration is re-runnable. It adds
-- privileges only; it revokes nothing and alters no ownership, no RLS and no table shape.

BEGIN;

-- Registry: read the frozen manifest contract; update only the service-probe columns.
GRANT SELECT ON TABLE public.asset_registry TO data_plane_builder;
GRANT UPDATE (service_health, last_invoked_at, last_selftest_at)
  ON TABLE public.asset_registry TO data_plane_builder;

-- Provenance receipts: the builder writes and amends its own receipts.
GRANT SELECT, INSERT, UPDATE ON TABLE public.asset_provenance_receipts TO data_plane_builder;

-- Read-only inputs.
GRANT SELECT ON TABLE public.asset_freshness            TO data_plane_builder;
GRANT SELECT ON TABLE public.charts                     TO data_plane_builder;
GRANT SELECT ON TABLE public.asset_output_digest_specs  TO data_plane_builder;

-- Fail closed if any grant did not take effect, so a silent no-op cannot pass as applied
-- (CLAUDE.md §N.8 Earned-Signal Principle: this check can genuinely read false).
DO $$
DECLARE
  missing text := '';
BEGIN
  IF NOT has_table_privilege('data_plane_builder','public.asset_registry','SELECT')
    THEN missing := missing || ' asset_registry.SELECT'; END IF;
  IF NOT has_column_privilege('data_plane_builder','public.asset_registry','service_health','UPDATE')
    THEN missing := missing || ' asset_registry.service_health.UPDATE'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.asset_provenance_receipts','INSERT')
    THEN missing := missing || ' asset_provenance_receipts.INSERT'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.asset_freshness','SELECT')
    THEN missing := missing || ' asset_freshness.SELECT'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.charts','SELECT')
    THEN missing := missing || ' charts.SELECT'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.asset_output_digest_specs','SELECT')
    THEN missing := missing || ' asset_output_digest_specs.SELECT'; END IF;

  IF missing <> '' THEN
    RAISE EXCEPTION 'migration 1070 did not take effect; still missing:%', missing;
  END IF;
END $$;

COMMIT;
